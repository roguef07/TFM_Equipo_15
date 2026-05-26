import logging

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import io
from matplotlib.backends.backend_pdf import PdfPages

from explainer import analyze_series, generate_explanation
from model_selection import run_all_models
from preprocessing import clean_and_aggregate_weekly

logging.basicConfig(level=logging.INFO)


# ── Helpers ──────────────────────────────────────────────────────────

def render_eda(df: pd.DataFrame, cat_col: str) -> None:
    """Renderiza el análisis exploratorio de datos completo."""
    st.subheader("Análisis Exploratorio de Datos (EDA)")

    with st.expander("Ver análisis completo", expanded=False):

        # 1. Estadísticas descriptivas
        st.markdown("#### Estadísticas descriptivas")
        col_a, col_b = st.columns(2)

        with col_a:
            st.write("**Ventas totales semanales (todas las categorías)**")
            total_weekly = df.groupby("week")["ventas"].sum().reset_index()
            st.dataframe(
                total_weekly["ventas"].describe().to_frame().T.round(2),
                use_container_width=True,
            )

        with col_b:
            st.write("**Resumen por categoría**")
            by_cat = (
                df.groupby(cat_col)["ventas"]
                .agg(["sum", "mean", "std", "min", "max"])
                .round(2)
            )
            st.dataframe(by_cat, use_container_width=True)

        # 2. Tendencia global de ventas
        st.markdown("#### Tendencia global de ventas semanales")
        total_weekly = df.groupby("week")["ventas"].sum().reset_index()
        fig1, ax1 = plt.subplots(figsize=(12, 3))
        ax1.plot(total_weekly["week"], total_weekly["ventas"], linewidth=1.5, color="#2563eb")
        ax1.set_xlabel("Semana")
        ax1.set_ylabel("Ventas totales")
        ax1.set_title("Ventas totales por semana")
        fig1.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

        # 3. Ventas por categoría
        st.markdown("#### Ventas semanales por categoría")
        fig2, ax2 = plt.subplots(figsize=(12, 4))
        for cat in df[cat_col].unique():
            temp = df[df[cat_col] == cat]
            ax2.plot(temp["week"], temp["ventas"], label=str(cat), linewidth=1)
        ax2.set_xlabel("Semana")
        ax2.set_ylabel("Ventas")
        ax2.set_title("Ventas por categoría")
        ax2.legend(fontsize=7, ncol=4)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

        # 4. Estacionalidad semanal
        st.markdown("#### Estacionalidad: ventas promedio por semana del año")
        df_woy = df.copy()
        df_woy["weekofyear"] = df_woy["week"].dt.isocalendar().week.astype(int)
        seasonality = df_woy.groupby("weekofyear")["ventas"].mean().reset_index()
        fig3, ax3 = plt.subplots(figsize=(12, 3))
        ax3.bar(seasonality["weekofyear"], seasonality["ventas"], color="#2563eb", alpha=0.75)
        ax3.set_xlabel("Semana del año")
        ax3.set_ylabel("Ventas promedio")
        ax3.set_title("Estacionalidad semanal")
        fig3.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)


# ── Configuración de página ───────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Pronóstico de Ventas")
st.title("Sistema de Pronóstico de Ventas")
st.markdown(
    "Aplicación para generar pronósticos semanales de ventas por categoría de producto. "
    "Carga un CSV para comenzar."
)


# ── Carga de archivo y selección de columnas ─────────────────────────
file = st.file_uploader("Cargar archivo CSV", type=["csv"])

if file:
    try:
        df_raw = pd.read_csv(file)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    st.subheader("Vista previa")
    st.dataframe(df_raw.head(), use_container_width=True)

    st.markdown(
    "Seleccione las columnas correspondientes para cada variable."
    " El sistema intentará limpiar los datos y convertirlos a un formato semanal.")

    cols = df_raw.columns.tolist()
    col1, col2, col3, col4 = st.columns(4)

    # Las claves de session_state se actualizan automáticamente con los widgets
    col1.selectbox("Columna de fecha", cols, key="date_col")
    col2.selectbox("Columna de categoría", cols, key="cat_col")
    col3.selectbox("Columna de cantidad", cols, key="qty_col")
    col4.selectbox("Columna de precio", cols, key="price_col")

    if st.button("Procesar datos"):
        try:
            with st.spinner("Limpiando y agregando datos por semana..."):
                df_clean = clean_and_aggregate_weekly(
                    df_raw,
                    st.session_state["date_col"],
                    st.session_state["cat_col"],
                    st.session_state["qty_col"],
                    st.session_state["price_col"],
                )
            st.session_state["data"] = df_clean

            # Precio promedio por categoría (para convertir unidades → revenue)
            cat_col_key   = st.session_state["cat_col"]
            price_col_key = st.session_state["price_col"]
            st.session_state["avg_price"] = (
                df_raw.groupby(cat_col_key)[price_col_key]
                .mean()
                .to_dict()
            )

            st.success(
                f"Datos procesados correctamente: {len(df_clean):,} filas, "
                f"{df_clean[cat_col_key].nunique()} categorías."
            )
        except ValueError as ve:
            st.error(f"Error en el preprocesamiento: {ve}")
        except Exception as e:
            st.error(f"Error inesperado durante el procesamiento: {e}")

    if "data" in st.session_state:
        st.subheader("Datos semanales agregados")
        st.dataframe(st.session_state["data"].head(100), use_container_width=True)


# ── EDA + Selección automática de modelo ─────────────────────────────
if "data" in st.session_state:
    df = st.session_state["data"]
    cat_col = st.session_state.get("cat_col")

    if cat_col is None:
        st.warning("Por favor, carga un archivo CSV y selecciona las columnas primero.")
        st.stop()

    # EDA
    render_eda(df, cat_col)

    # Configuración
    st.subheader("Configuración del pronóstico")
    col_h, col_s = st.columns([2, 3])
    with col_h:
        horizon = st.number_input(
            "Horizonte de pronóstico (semanas)",
            min_value=1,
            max_value=52,
            value=12,
        )
    with col_s:
        include_sarima = st.checkbox(
            "Incluir SARIMA en la comparación",
            value=True,
            help=(
                "SARIMA evalúa hasta 64 combinaciones de hiperparámetros por categoría. "
                "Desactívalo si el dataset tiene muchas categorías y necesitas resultados rápidos."
            ),
        )

    if st.button("🔍 Seleccionar mejor modelo y generar forecast"):
        categories = df[cat_col].unique()
        avg_price  = st.session_state.get("avg_price", {})
        progress_bar = st.progress(0)
        summary_rows: list[dict] = []
        forecasts_all: list[pd.DataFrame] = []

        # colector de figuras para generar PDF más tarde
        pdf_figs: list = []

        for i, cat in enumerate(categories):
            st.markdown(f"---\n### Categoría: **{cat}**")

            try:
                temp = df[df[cat_col] == cat].copy().sort_values("week")
                chars = analyze_series(temp["quantity"])

                with st.spinner(f"Entrenando modelos para '{cat}'..."):
                    result = run_all_models(
                        temp, cat_col, horizon, include_sarima=include_sarima
                    )

                best_model  = result["best_model_name"]
                all_metrics = result["metrics"]
                forecast_df = result["best_forecast"].copy()
                forecast_df["category"] = cat

                # Convertir unidades → revenue estimado con precio promedio
                cat_avg_price = avg_price.get(cat, 1.0)
                forecast_df["forecast_revenue"] = (
                    forecast_df["forecast"] * cat_avg_price
                ).round(2)
                forecast_df = forecast_df.rename(columns={"forecast": "forecast_units"})

                forecasts_all.append(forecast_df)

                summary_rows.append({
                    "Categoría": cat,
                    "Modelo seleccionado": best_model,
                    "MAE (unidades)":  round(all_metrics[best_model]["mae"], 2),
                    "RMSE (unidades)": round(all_metrics[best_model]["rmse"], 2),
                    "MAPE (%)":        round(all_metrics[best_model]["mape"], 2),
                    "Precio promedio": round(cat_avg_price, 2),
                })

                # Explicación detallada
                explanation = generate_explanation(cat, best_model, all_metrics, chars)
                with st.expander(
                    f"Ver análisis completo — modelo seleccionado: **{best_model}**",
                    expanded=True,
                ):
                    st.markdown(explanation)

                # Gráfico: unidades históricas + pronóstico de unidades
                hist = df[df[cat_col] == cat]
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 3))

                # Panel izquierdo: unidades
                ax1.plot(hist["week"], hist["quantity"],
                         label="Histórico", linewidth=1.5, color="#2563eb")
                ax1.plot(forecast_df["week"], forecast_df["forecast_units"],
                         linestyle="--", linewidth=1.8, color="#dc2626",
                         label=f"Pronóstico · {best_model}")
                ax1.set_title("Unidades vendidas", fontsize=10)
                ax1.set_xlabel("Semana")
                ax1.set_ylabel("Unidades")
                ax1.legend(fontsize=8)

                # Panel derecho: revenue estimado
                ax2.plot(hist["week"], hist["ventas"],
                         label="Histórico", linewidth=1.5, color="#2563eb")
                ax2.plot(forecast_df["week"], forecast_df["forecast_revenue"],
                         linestyle="--", linewidth=1.8, color="#dc2626",
                         label=f"Pronóstico · {best_model}")
                ax2.set_title(f"Revenue estimado (× precio prom. {cat_avg_price:.2f})", fontsize=10)
                ax2.set_xlabel("Semana")
                ax2.set_ylabel("Ventas")
                ax2.legend(fontsize=8)

                fig.suptitle(f"Categoría: {cat}  —  Modelo: {best_model}", fontsize=11)
                fig.tight_layout()
                st.pyplot(fig)
                # guardar figura para PDF (no cerrar aún)
                pdf_figs.append(fig)

            except ValueError as ve:
                st.warning(f"Categoría '{cat}' omitida: {ve}")
            except Exception as e:
                st.error(f"Error inesperado en categoría '{cat}': {e}")
            finally:
                progress_bar.progress((i + 1) / len(categories))

        if not summary_rows:
            st.error(
                "No se pudo entrenar ningún modelo. "
                "Revisa que los datos tengan suficiente historia por categoría."
            )
            st.stop()

        # Resumen global
        st.markdown("---")
        st.subheader("📋 Resumen de selección de modelos")
        st.info(
            "Las métricas MAE y RMSE están en **unidades** (el target de los modelos). "
            "El revenue estimado = unidades pronosticadas × precio promedio histórico por categoría."
        )
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

        # Pronóstico combinado
        if forecasts_all:
            st.subheader("📅 Pronóstico combinado (todos los modelos ganadores)")
            st.dataframe(
                pd.concat(forecasts_all, ignore_index=True),
                use_container_width=True,
            )
        # --- Generar PDF con todo lo mostrado ---
        try:
            buffer = io.BytesIO()
            with PdfPages(buffer) as pdf:
                # Portada / resumen textual
                fig_cover = plt.figure(figsize=(8.27, 11.69))  # A4
                fig_cover.clf()
                txt = (
                    "Reporte de pronósticos\n\n"
                    f"Categorías procesadas: {len(summary_rows)}\n"
                    f"Horizonte (semanas): {horizon}\n\n"
                    "Resumen por categoría:\n"
                )
                fig_cover.text(0.02, 0.95, txt, fontsize=12, va="top")
                pdf.savefig(fig_cover)
                plt.close(fig_cover)

                # Tabla resumen
                df_summary = pd.DataFrame(summary_rows)
                if not df_summary.empty:
                    fig_table = plt.figure(figsize=(8.27, 11.69))
                    ax = fig_table.add_subplot(111)
                    ax.axis("off")
                    table = ax.table(
                        cellText=df_summary.values,
                        colLabels=df_summary.columns,
                        loc="center",
                    )
                    table.auto_set_font_size(False)
                    table.set_fontsize(8)
                    table.scale(1, 1.5)
                    pdf.savefig(fig_table)
                    plt.close(fig_table)

                # Tabla pronóstico combinado (primeras filas)
                try:
                    combined_df = pd.concat(forecasts_all, ignore_index=True) if forecasts_all else pd.DataFrame()
                except Exception:
                    combined_df = pd.DataFrame()

                if not combined_df.empty:
                    fig_fore = plt.figure(figsize=(8.27, 11.69))
                    axf = fig_fore.add_subplot(111)
                    axf.axis("off")
                    sample_fore = combined_df.head(80)
                    tablef = axf.table(
                        cellText=sample_fore.values,
                        colLabels=sample_fore.columns,
                        loc="center",
                    )
                    tablef.auto_set_font_size(False)
                    tablef.set_fontsize(7)
                    tablef.scale(1, 1.2)
                    pdf.savefig(fig_fore)
                    plt.close(fig_fore)

                # Añadir todas las figuras de categoría y reporte
                for f in pdf_figs:
                    try:
                        pdf.savefig(f)
                        plt.close(f)
                    except Exception:
                        continue

            buffer.seek(0)
            st.download_button(
                label="📥 Descargar reporte completo (PDF)",
                data=buffer.getvalue(),
                file_name="reporte_pronosticos.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.warning(f"No se pudo generar el PDF: {e}")
