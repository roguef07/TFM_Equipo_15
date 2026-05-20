import numpy as np
import pandas as pd


def create_features(df: pd.DataFrame, target_col: str, cat_col: str) -> pd.DataFrame:
    """
    Construye features para modelos ML a partir de una serie semanal de una sola categoría.

    Features generadas
    ------------------
    Lags            : lag_1, lag_2, lag_4
    Medias móviles  : ma_4, ma_13  (calculadas sobre shift(1) para evitar leakage)
    Tendencia       : time_index   (posición ordinal en la serie)
    Calendario      : weekofyear, month, quarter, year
    Dummies de mes  : m_2 … m_12  (m_1 es la categoría de referencia)
    """
    df = df.copy().sort_values("week").reset_index(drop=True)

    # ── Lags ─────────────────────────────────────────────────────────
    df["lag_1"] = df.groupby(cat_col)[target_col].shift(1)
    df["lag_2"] = df.groupby(cat_col)[target_col].shift(2)
    df["lag_4"] = df.groupby(cat_col)[target_col].shift(4)

    # ── Medias móviles sobre shift(1) — sin leakage ───────────────────
    df["ma_4"] = df.groupby(cat_col)[target_col].transform(
        lambda s: s.shift(1).rolling(4).mean()
    )
    df["ma_13"] = df.groupby(cat_col)[target_col].transform(
        lambda s: s.shift(1).rolling(13).mean()
    )

    # ── Tendencia lineal ──────────────────────────────────────────────
    df["time_index"] = np.arange(len(df))

    # ── Calendario ───────────────────────────────────────────────────
    df["weekofyear"] = df["week"].dt.isocalendar().week.astype(int)
    df["month"]      = df["week"].dt.month
    df["quarter"]    = df["week"].dt.quarter
    df["year"]       = df["week"].dt.year

    # ── Dummies estacionales por mes (m_1 = referencia, se omite) ────
    for m in range(2, 13):
        df[f"m_{m}"] = (df["week"].dt.month == m).astype(int)

    result = df.dropna()
    if result.empty:
        raise ValueError(
            f"create_features: el DataFrame resultante está vacío para target='{target_col}'. "
            "La serie es demasiado corta — se necesitan al menos 14 filas por categoría "
            "(la media móvil ma_13 requiere 13 semanas de historia previas)."
        )
    return result
