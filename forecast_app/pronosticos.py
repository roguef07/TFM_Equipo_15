import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from db import get_connection


def load_series(id_dataset):
    """
    Carga la serie temporal agregada por fecha y categoría
    """
    conn = get_connection()
    query = """
        SELECT 
            fecha_venta,
            categoria,
            SUM(unidades_vendidas) AS total
        FROM ventas
        WHERE id_dataset = ?
        GROUP BY fecha_venta, categoria
        ORDER BY fecha_venta
    """
    df = pd.read_sql(query, conn, params=(id_dataset,))
    conn.close()
    return df


def arima_model(
    df,
    freq="W",          # semanal
    order=(1, 1, 1),    # ARIMA simple
    seasonal_order=(0, 0, 0, 0),  # sin estacionalidad (rápido)
    horizon=12
):
    """
    Entrena ARIMA por categoría y genera forecast multi-serie
    """
    results = []

    for categoria, group in df.groupby("categoria"):
        serie = group.copy()

        serie["fecha_venta"] = pd.to_datetime(serie["fecha_venta"])
        serie = serie.sort_values("fecha_venta")
        serie = serie.set_index("fecha_venta")
        serie = serie.asfreq(freq)

        # rellenar huecos
        serie["total"] = serie["total"].interpolate()

        model = SARIMAX(
            serie["total"],
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )

        fitted_model = model.fit(disp=False)

        forecast = fitted_model.get_forecast(steps=horizon)
        pred = forecast.predicted_mean

        forecast_df = pred.reset_index()
        forecast_df.columns = ["fecha_pronosticada", "valor_pronosticado"]
        forecast_df["step"] = range(1, horizon + 1)
        forecast_df["categoria"] = categoria

        results.append(forecast_df)

    final_forecast = pd.concat(results, ignore_index=True)
    return final_forecast


def save_forecast(id_ejecucion, forecast_df):
    """
    Guarda el forecast en la tabla pronosticos
    """
    conn = get_connection()
    cur = conn.cursor()

    rows = []
    for _, row in forecast_df.iterrows():
        rows.append((
            id_ejecucion,
            str(row["fecha_pronosticada"]),
            str(row["categoria"]),
            float(row["valor_pronosticado"])
        ))

    # batch insert (rápido)
    cur.executemany("""
        INSERT INTO pronosticos(
            id_ejecucion,
            fecha_pronosticada,
            categoria,
            valor_pronosticado
        )
        VALUES (?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def run_arima(id_dataset, id_ejecucion, config):
    """
    Pipeline completo:
    ventas → ARIMA → pronosticos
    """
    df = load_series(id_dataset)

    forecast_df = arima_model(
        df=df,
        freq=config.get("freq", "W"),
        order=config.get("order", (1, 1, 1)),
        seasonal_order=config.get("seasonal_order", (0, 0, 0, 0)),
        horizon=config.get("horizon", 12)
    )

    save_forecast(id_ejecucion, forecast_df)

    return forecast_df