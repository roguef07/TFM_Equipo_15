"""
Selección automática del mejor modelo por categoría.

Entrena SARIMA, Regresión Lineal y XGBoost sobre la misma serie y
selecciona el modelo con menor RMSE en el conjunto de test (último 30%).

Target: 'quantity' (unidades semanales vendidas).
Los resultados en revenue se obtienen multiplicando por el precio promedio en app.py.
"""
import logging

import numpy as np
import pandas as pd

from evaluation import evaluate
from features import create_features
from forecast import forecast_ml, forecast_sarima
from models import sarima_auto_tune
from pipelines import create_lr_pipeline, create_xgb_pipeline

logger = logging.getLogger(__name__)

MODEL_NAMES = ["SARIMA", "Regresión Lineal", "XGBoost"]

TRAIN_RATIO = 0.70
MIN_NONZERO_WEEKS = 52


def run_all_models(
    temp: pd.DataFrame,
    cat_col: str,
    horizon: int,
    include_sarima: bool = True,
) -> dict:
    """
    Entrena los modelos disponibles para una categoría y devuelve el mejor.

    Parameters
    ----------
    temp : pd.DataFrame
        Serie de UNA categoría con columnas ['week', cat_col, 'quantity', 'ventas'].
    cat_col : str
        Nombre de la columna de categoría.
    horizon : int
        Semanas a pronosticar hacia el futuro.
    include_sarima : bool
        Si False, omite SARIMA.

    Returns
    -------
    dict con claves:
        metrics         (dict)          {model_name: {mae, rmse, mape}}
        best_model_name (str)           modelo ganador
        best_forecast   (pd.DataFrame)  columnas ['week', 'forecast']
                                        donde 'forecast' está en unidades (quantity)
    """
    # ── Validación de la serie ────────────────────────────────────────
    nonzero_weeks = int((temp["quantity"] > 0).sum())
    if nonzero_weeks < MIN_NONZERO_WEEKS:
        raise ValueError(
            f"Solo {nonzero_weeks} semanas con ventas > 0 "
            f"(mínimo requerido: {MIN_NONZERO_WEEKS}). "
            "Serie insuficiente para modelar con fiabilidad."
        )

    split = int(len(temp) * TRAIN_RATIO)
    train_raw = temp.iloc[:split]
    test_raw  = temp.iloc[split:]

    if train_raw["quantity"].var() == 0:
        raise ValueError(
            "La varianza en el conjunto de entrenamiento es cero. "
            "Serie constante — no es posible entrenar ningún modelo."
        )

    metrics:   dict[str, dict]        = {}
    forecasts: dict[str, pd.DataFrame] = {}

    # ── SARIMA ────────────────────────────────────────────────────────
    if include_sarima:
        try:
            model_sarima = sarima_auto_tune(train_raw["quantity"])
            if model_sarima is not None and len(test_raw) > 0:
                preds = np.asarray(model_sarima.forecast(steps=len(test_raw)))
                mae, rmse, mape = evaluate(test_raw["quantity"], preds)
                metrics["SARIMA"] = {"mae": mae, "rmse": rmse, "mape": mape}

                future_vals = forecast_sarima(model_sarima, horizon)
                future_idx  = pd.date_range(
                    start=temp["week"].max() + pd.Timedelta(weeks=1),
                    periods=horizon,
                    freq="W-MON",
                )
                forecasts["SARIMA"] = pd.DataFrame(
                    {"week": future_idx, "forecast": future_vals}
                )
        except Exception as e:
            logger.warning("SARIMA no disponible para esta categoría: %s", e)

    # ── Modelos ML (Regresión Lineal y XGBoost) ───────────────────────
    try:
        temp_feat = create_features(temp, "quantity", cat_col)
        split_f   = int(len(temp_feat) * TRAIN_RATIO)
        train_f   = temp_feat.iloc[:split_f]
        test_f    = temp_feat.iloc[split_f:]

        drop_cols = [c for c in ["quantity", "ventas", cat_col, "week"] if c in train_f.columns]
        X_train = train_f.drop(columns=drop_cols)
        y_train = train_f["quantity"]
        X_test  = test_f.drop(columns=drop_cols)
        y_test  = test_f["quantity"]

        for name, pipeline in [
            ("Regresión Lineal", create_lr_pipeline()),
            ("XGBoost", create_xgb_pipeline()),
        ]:
            try:
                pipeline.fit(X_train, y_train)
                preds = pipeline.predict(X_test)
                mae, rmse, mape = evaluate(y_test, preds)
                metrics[name]   = {"mae": mae, "rmse": rmse, "mape": mape}
                future_df = forecast_ml(
                    pipeline, temp_feat, horizon, cat_col, target_col="quantity"
                )
                forecasts[name] = future_df
            except Exception as e:
                logger.warning("%s no disponible: %s", name, e)

    except ValueError as ve:
        logger.warning("Feature engineering no disponible (serie corta): %s", ve)
    except Exception as e:
        logger.warning("Error en modelos ML: %s", e)

    if not metrics:
        raise ValueError(
            "Ningún modelo pudo entrenarse. "
            "La serie puede ser demasiado corta o completamente constante."
        )

    best_model_name = min(metrics, key=lambda m: metrics[m]["rmse"])

    return {
        "metrics":          metrics,
        "best_model_name":  best_model_name,
        "best_forecast":    forecasts[best_model_name].copy(),
    }
