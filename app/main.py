import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from app.utils.anomaly_detector import detectar_anomalias
from models.explainer import analyze_series, generate_explanation
from models.model_selection import run_all_models
from models.preprocessing import clean_and_aggregate_weekly


# ── Helpers ───────────────────────────────────────────────────────────

def render_eda(df: pd.DataFrame, cat_col: str) -> None:
    st.subheader("Análisis Exploratorio de Datos (EDA)")

    with st.expander("Ver análisis completo", expanded=True):
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

        st.markdown("#### Tendencia global de ventas semanales")
        total_weekly = df.groupby("week")["ventas"].sum().reset_index()
        fig1, ax1 = plt.subplots(figsize=(12, 3))
        ax1.plot(total_weekly["week"], total_weekly["ventas"], linewidth=1.5, color="#1e40af")
        ax1.set_xlabel("Semana")
        ax1.set_ylabel("Ventas totales")
        ax1.set_title("Ventas totales por semana")
        fig1.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

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

        st.markdown("#### Estacionalidad: ventas promedio por semana del año")
        df_woy = df.copy()
        df_woy["weekofyear"] = df_woy["week"].dt.isocalendar().week.astype(int)
        seasonality = df_woy.groupby("weekofyear")["ventas"].mean().reset_index()
        fig3, ax3 = plt.subplots(figsize=(12, 3))
        ax3.bar(seasonality["weekofyear"], seasonality["ventas"], color="#1e40af", alpha=0.75)
        ax3.set_xlabel("Semana del año")
        ax3.set_ylabel("Ventas promedio")
        ax3.set_title("Estacionalidad semanal")
        fig3.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)


def _render_resultado(res: dict, df: pd.DataFrame, cat_col: str) -> None:
    if res["error"] is not None:
        st.error(f"Error al procesar esta categoría: {res['error']}")
        return

    cat           = res["cat"]
    best_model    = res["best_model"]
    all_metrics   = res["all_metrics"]
    forecast_df   = res["forecast_df"]
    cat_avg_price = res["cat_avg_price"]
    explanation   = res["explanation"]
    anomalias     = res["anomalias"]

    # ── Métricas clave ────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Modelo ganador", best_model)
    c2.metric("RMSE", f"{all_metrics[best_model]['rmse']:.1f} u")
    c3.metric("MAE",  f"{all_metrics[best_model]['mae']:.1f} u")
    c4.metric("MAPE", f"{all_metrics[best_model]['mape']:.1f}%")

    # ── Explicación del modelo ────────────────────────────────────────
    with st.expander(f"Ver análisis del modelo — {best_model}", expanded=False):
        st.markdown(explanation)

    # ── Gráfico ───────────────────────────────────────────────────────
    hist = df[df[cat_col] == cat]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 3))

    ax1.plot(hist["week"], hist["quantity"],
             label="Histórico", linewidth=1.5, color="#1e40af")
    ax1.plot(forecast_df["week"], forecast_df["forecast_units"],
             linestyle="--", linewidth=1.8, color="#dc2626",
             label=f"Pronóstico · {best_model}")
    ax1.set_title("Unidades vendidas", fontsize=10)
    ax1.set_xlabel("Semana")
    ax1.set_ylabel("Unidades")
    ax1.legend(fontsize=8)

    ax2.plot(hist["week"], hist["ventas"],
             label="Histórico", linewidth=1.5, color="#1e40af")
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
    plt.close(fig)

    # ── Anomalías ─────────────────────────────────────────────────────
    if anomalias:
        st.markdown("#### Anomalías detectadas en datos históricos")
        for a in anomalias:
            with st.container(border=True):
                st.markdown(
                    f"**{a['fecha']}** — variación: `{a['variacion_pct']:+.1f}%`"
                    f" ({a['desviacion_std']:.1f}σ)"
                )
                st.caption(a["explicacion"])


# ── Configuración de página ───────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Pronóstico de Ventas",
)

# ── Header profesional ────────────────────────────────────────────────
st.markdown(
    """
    <div style='padding:1.2rem 0 1rem;border-bottom:3px solid #1e40af;margin-bottom:1.5rem;'>
      <h1 style='margin:0;color:#1e293b;font-size:2rem;'>Sistema de Pronóstico de Ventas</h1>
      <p style='margin:.4rem 0 0;color:#64748b;font-size:1rem;'>
        Selección automática de modelos &nbsp;·&nbsp; Detección de anomalías
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────
ejecutar = False

with st.sidebar:
    st.markdown("## Configuración")

    # ── 1. Datos ──────────────────────────────────────────────────────
    st.markdown("### 1. Datos")
    file = st.file_uploader("Cargar archivo CSV", type=["csv"])

    if file:
        try:
            df_raw = pd.read_csv(file)
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            st.stop()

        cols = df_raw.columns.tolist()
        st.selectbox("Columna de fecha",     cols, key="date_col")
        st.selectbox("Columna de categoría", cols, key="cat_col")
        st.selectbox("Columna de cantidad",  cols, key="qty_col")
        st.selectbox("Columna de precio",    cols, key="price_col")

        if st.button("Procesar datos", use_container_width=True):
            try:
                with st.spinner("Procesando..."):
                    df_clean = clean_and_aggregate_weekly(
                        df_raw,
                        st.session_state["date_col"],
                        st.session_state["cat_col"],
                        st.session_state["qty_col"],
                        st.session_state["price_col"],
                    )
                st.session_state["data"] = df_clean
                cat_col_key   = st.session_state["cat_col"]
                price_col_key = st.session_state["price_col"]
                st.session_state["avg_price"] = (
                    df_raw.groupby(cat_col_key)[price_col_key].mean().to_dict()
                )
                st.success(
                    f"{len(df_clean):,} filas · "
                    f"{df_clean[cat_col_key].nunique()} categorías"
                )
            except ValueError as ve:
                st.error(f"Error en el preprocesamiento: {ve}")
            except Exception as e:
                st.error(f"Error inesperado: {e}")

    # ── 2. Análisis ───────────────────────────────────────────────────
    if "data" in st.session_state:
        _df_sb  = st.session_state["data"]
        _cat_sb = st.session_state.get("cat_col")

        st.markdown("---")
        st.markdown("### 2. Análisis")

        horizon = st.number_input(
            "Horizonte (semanas)",
            min_value=1, max_value=52, value=12,
        )
        include_sarima = st.checkbox(
            "Incluir SARIMA",
            value=True,
            help=(
                "SARIMA evalúa hasta 64 combinaciones de hiperparámetros por categoría. "
                "Desactívalo si el dataset tiene muchas categorías y necesitas resultados rápidos."
            ),
        )
        categorias_disponibles = sorted(_df_sb[_cat_sb].unique().tolist())
        categorias_seleccionadas = st.multiselect(
            "Categorías a analizar",
            options=categorias_disponibles,
            default=categorias_disponibles,
        )
        ejecutar = st.button("Ejecutar análisis", use_container_width=True, type="primary")

    # ── Contáctanos ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Conoce más sobre el proyecto en:")
    st.markdown(
        '<a href="https://github.com/roguef07/TFM_Equipo_15/tree/main" '
        'target="_blank" style="color:#1e40af;font-weight:500;">'
        "Ver Repositorio en GitHub</a>",
        unsafe_allow_html=True,
    )


# ── Cuerpo principal ──────────────────────────────────────────────────
if "data" not in st.session_state:
    st.info("Carga un archivo CSV en el panel lateral para comenzar.")
    st.stop()

df      = st.session_state["data"]
cat_col = st.session_state.get("cat_col")

if cat_col is None:
    st.warning("Por favor, selecciona las columnas antes de continuar.")
    st.stop()

# Vista previa compacta
with st.expander("Vista previa de los datos procesados", expanded=False):
    st.dataframe(df.head(20), use_container_width=True)

# ── Ejecución del análisis ────────────────────────────────────────────
if ejecutar:
    if not categorias_seleccionadas:
        st.warning("Selecciona al menos una categoría.")
        st.stop()

    avg_price  = st.session_state.get("avg_price", {})
    resultados: list[dict] = []
    n = len(categorias_seleccionadas)

    with st.status("Analizando categorías...", expanded=True) as status_widget:
        for i, cat in enumerate(categorias_seleccionadas):
            st.write(f"Procesando **{cat}**... ({i + 1}/{n})")
            try:
                temp  = df[df[cat_col] == cat].copy().sort_values("week")
                chars = analyze_series(temp["quantity"])
                result = run_all_models(temp, cat_col, horizon, include_sarima=include_sarima)

                best_model  = result["best_model_name"]
                all_metrics = result["metrics"]
                forecast_df = result["best_forecast"].copy()
                forecast_df["category"] = cat

                cat_avg_price = avg_price.get(cat, 1.0)
                forecast_df["forecast_revenue"] = (
                    forecast_df["forecast"] * cat_avg_price
                ).round(2)
                forecast_df = forecast_df.rename(columns={"forecast": "forecast_units"})

                explanation = generate_explanation(cat, best_model, all_metrics, chars)
                anomalias   = detectar_anomalias(temp, cat)

                resultados.append({
                    "cat":           cat,
                    "temp":          temp,
                    "best_model":    best_model,
                    "all_metrics":   all_metrics,
                    "forecast_df":   forecast_df,
                    "cat_avg_price": cat_avg_price,
                    "explanation":   explanation,
                    "anomalias":     anomalias,
                    "summary_row": {
                        "Categoría":           cat,
                        "Modelo seleccionado": best_model,
                        "MAE (unidades)":      round(all_metrics[best_model]["mae"], 2),
                        "RMSE (unidades)":     round(all_metrics[best_model]["rmse"], 2),
                        "MAPE (%)":            round(all_metrics[best_model]["mape"], 2),
                        "Precio promedio":     round(cat_avg_price, 2),
                    },
                    "error": None,
                })
            except ValueError as ve:
                resultados.append({"cat": cat, "error": str(ve)})
                st.warning(f"'{cat}' omitida: {ve}")
            except Exception as e:
                resultados.append({"cat": cat, "error": str(e)})
                st.warning(f"Error en '{cat}': {e}")

        n_ok = sum(1 for r in resultados if r.get("error") is None)
        status_widget.update(
            label=f"Análisis completado — {n_ok}/{n} categorías procesadas",
            state="complete",
            expanded=False,
        )

    exitosos = [r for r in resultados if r.get("error") is None]
    if not exitosos:
        st.error(
            "No se pudo entrenar ningún modelo. "
            "Revisa que los datos tengan suficiente historia por categoría."
        )
        st.stop()

    # ── Resultados en tabs ────────────────────────────────────────────
    tab_labels = ["Análisis exploratorio"] + [r["cat"] for r in resultados]
    tabs = st.tabs(tab_labels)
    with tabs[0]:
        render_eda(df, cat_col)
    for tab, res in zip(tabs[1:], resultados):
        with tab:
            _render_resultado(res, df, cat_col)

    # ── Resumen global ────────────────────────────────────────────────
    summary_rows  = [r["summary_row"] for r in exitosos]
    forecasts_all = [r["forecast_df"] for r in exitosos]

    st.markdown("---")
    st.subheader("Resumen de selección de modelos")
    st.info(
        "Las métricas MAE y RMSE están en **unidades** (el target de los modelos). "
        "El revenue estimado = unidades pronosticadas × precio promedio histórico por categoría."
    )
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    if forecasts_all:
        st.subheader("Pronóstico combinado (todos los modelos ganadores)")
        st.dataframe(
            pd.concat(forecasts_all, ignore_index=True),
            use_container_width=True,
        )

