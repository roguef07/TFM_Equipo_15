import streamlit as st
from db import init_db
from ingesta import ingest_csv
from modelos import register_model
from ejecuciones import create_execution
from pronosticos import run_arima
import pandas as pd

st.set_page_config(page_title="Forecasting App", layout="wide")

st.title("Forecasting App (TFM - MVP)")
st.caption("Aplicación de forecasting con ARIMA sobre datos cargados por CSV")

# Inicializar base de datos
init_db()

# -------------------------
# Upload CSV
# -------------------------
st.header("Carga de datos")

uploaded = st.file_uploader("Sube un CSV", type=["csv"])

if uploaded:
    with st.spinner("⏳ Procesando CSV e ingiriendo datos..."):
        id_dataset = ingest_csv(uploaded, uploaded.name)

    st.success(f"Dataset guardado con ID: {id_dataset}")

    st.divider()

    # -------------------------
    # Configuración del modelo
    # -------------------------
    st.header("Configuración del modelo ARIMA")

    col1, col2, col3 = st.columns(3)

    with col1:
        freq = st.selectbox("Frecuencia temporal", ["D", "W", "M"], index=1)

    with col2:
        horizon = st.number_input("Horizonte de predicción", min_value=1, value=12)

    with col3:
        categoria = st.text_input("Categoría (opcional)", value="", help="Dejar vacío para todas las categorías")

    st.subheader("Parámetros ARIMA")

    col4, col5, col6 = st.columns(3)
    with col4:
        p = st.number_input("p (AR)", min_value=0, value=1)
    with col5:
        d = st.number_input("d (I)", min_value=0, value=1)
    with col6:
        q = st.number_input("q (MA)", min_value=0, value=1)

    if st.button("Ejecutar Forecast"):
        with st.spinner("📈 Entrenando modelo y generando pronóstico..."):

            # Registrar modelo
            id_modelo = register_model(
                tipo="ARIMA",
                version="1.0",
                descripcion="Modelo ARIMA univariado por categoría"
            )

            # Configuración
            config = {
                "freq": freq,
                "order": (p, d, q),
                "seasonal_order": (0, 0, 0, 0),
                "horizon": horizon,
                "categoria": categoria.strip() if categoria else None
            }

            # Crear ejecución
            id_ejecucion = create_execution(
                id_dataset=id_dataset,
                id_modelo=id_modelo,
                horizonte=horizon,
                params=config
            )

            # Ejecutar forecast
            forecast_df = run_arima(
                id_dataset=id_dataset,
                id_ejecucion=id_ejecucion,
                config=config
            )

        st.success("Forecast generado y guardado en la base de datos")

        # -------------------------
        # Resultados
        # -------------------------
        st.header("Resultados")

        st.dataframe(forecast_df, use_container_width=True)

        # Visualización simple
        st.subheader("Visualización")

        if not forecast_df.empty:
            for cat, g in forecast_df.groupby("categoria"):
                st.markdown(f"**Categoría: {cat}**")
                chart_df = g[["fecha_pronosticada", "valor_pronosticado"]].copy()
                chart_df["fecha_pronosticada"] = pd.to_datetime(chart_df["fecha_pronosticada"])
                chart_df = chart_df.set_index("fecha_pronosticada")
                st.line_chart(chart_df)