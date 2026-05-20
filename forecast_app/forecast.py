import numpy as np
import pandas as pd


def forecast_sarima(model, steps: int) -> np.ndarray:
    """Devuelve las predicciones futuras como array numpy de longitud `steps`."""
    return np.asarray(model.forecast(steps=steps))


def forecast_ml(
    model,
    last_data: pd.DataFrame,
    horizon: int,
    cat_col: str,
    target_col: str = "quantity",
) -> pd.DataFrame:
    """
    Genera predicciones iterativas hacia el futuro con modelos ML.

    En cada paso actualiza todos los features que dependen del histórico:
    lags (lag_1, lag_2, lag_4), medias móviles (ma_4, ma_13),
    índice de tendencia (time_index), features de calendario y dummies de mes.

    Returns
    -------
    pd.DataFrame con columnas ['week', 'forecast']
    """
    df = last_data.copy()
    forecasts = []

    for _ in range(horizon):
        row = df.iloc[-1:].copy()
        idx = row.index[0]
        next_week = df["week"].iloc[-1] + pd.Timedelta(weeks=1)
        ts = pd.Timestamp(next_week)
        n = len(df)

        # ── Fecha ─────────────────────────────────────────────────────
        row.loc[idx, "week"] = next_week

        # ── Calendario ────────────────────────────────────────────────
        row.loc[idx, "weekofyear"] = ts.isocalendar()[1]
        row.loc[idx, "month"]      = ts.month
        if "quarter" in df.columns:
            row.loc[idx, "quarter"] = ts.quarter
        if "year" in df.columns:
            row.loc[idx, "year"] = ts.year

        # ── Dummies de mes ────────────────────────────────────────────
        for m in range(2, 13):
            col = f"m_{m}"
            if col in df.columns:
                row.loc[idx, col] = int(ts.month == m)

        # ── Índice de tendencia ───────────────────────────────────────
        if "time_index" in df.columns:
            row.loc[idx, "time_index"] = df["time_index"].iloc[-1] + 1

        # ── Lags ──────────────────────────────────────────────────────
        row.loc[idx, "lag_1"] = df[target_col].iloc[-1]
        if "lag_2" in df.columns:
            row.loc[idx, "lag_2"] = df[target_col].iloc[-2] if n >= 2 else df[target_col].iloc[-1]
        row.loc[idx, "lag_4"] = df[target_col].iloc[-4] if n >= 4 else df[target_col].iloc[-1]

        # ── Medias móviles ────────────────────────────────────────────
        if "ma_4" in df.columns:
            row.loc[idx, "ma_4"]  = df[target_col].iloc[-4:].mean()
        if "ma_13" in df.columns:
            row.loc[idx, "ma_13"] = df[target_col].iloc[-13:].mean()

        # ── Predicción ────────────────────────────────────────────────
        drop_cols = [c for c in [target_col, "ventas", cat_col, "week"] if c in row.columns]
        X = row.drop(columns=drop_cols)
        pred = float(model.predict(X)[0])

        row.loc[idx, target_col] = pred
        df = pd.concat([df, row], ignore_index=True)
        forecasts.append({"week": next_week, "forecast": pred})

    return pd.DataFrame(forecasts)
