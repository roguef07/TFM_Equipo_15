import pandas as pd

def clean_and_aggregate_weekly(df, date_col, cat_col, qty_col, price_col):

    df = df.copy()

    # =========================
    # 1. Conversión de tipos
    # =========================
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    df[qty_col] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)

    df[price_col] = (
        pd.to_numeric(df[price_col], errors='coerce')
        .ffill()
        .bfill()
    )

    # =========================
    # 2. Limpieza de datos críticos
    # =========================
    # eliminar fechas inválidas (NaT rompe series temporales)
    df = df.dropna(subset=[date_col])

    # evitar negativos
    df[price_col] = df[price_col].clip(lower=0)
    df[qty_col] = df[qty_col].clip(lower=0)

    # =========================
    # 3. Feature engineering base
    # =========================
    df["ventas"] = df[qty_col] * df[price_col]

    # FIX IMPORTANTE: evitar apply (causa errores con NaT/Period)
    df["week"] = df[date_col].dt.to_period("W").dt.start_time

    # =========================
    # 4. Agregación semanal
    # =========================
    df_grouped = df.groupby(["week", cat_col], as_index=False).agg({
        qty_col: "sum",
        "ventas": "sum",
    }).rename(columns={qty_col: "quantity"})

    # =========================
    # 5. Completar semanas faltantes por categoría
    # =========================
    all_categories = df_grouped[cat_col].unique()
    full_data = []

    for cat in all_categories:

        temp = df_grouped[df_grouped[cat_col] == cat].copy()

        # si por alguna razón no hay datos, saltar
        if temp.empty:
            continue

        idx = pd.date_range(
            start=temp["week"].min(),
            end=temp["week"].max(),
            freq="W-MON"
        )

        temp = temp.set_index("week").reindex(idx).fillna(0)

        temp[cat_col] = cat
        temp = temp.rename_axis("week").reset_index()

        full_data.append(temp)

    if not full_data:
        raise ValueError(
            "clean_and_aggregate_weekly: no se encontraron datos válidos por categoría tras la limpieza. "
            "Verifica que las columnas seleccionadas contengan fechas, cantidades y precios válidos."
        )

    return pd.concat(full_data, ignore_index=True)