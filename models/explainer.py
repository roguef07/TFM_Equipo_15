"""
Análisis de características de la serie temporal y generación de explicaciones
sobre la selección del mejor modelo.
"""
import numpy as np
import pandas as pd

# Fortalezas y debilidades genéricas de cada modelo
_MODEL_SW = {
    "SARIMA": {
        "strengths": [
            "Modela explícitamente tendencia, estacionalidad y autocorrelación mediante parámetros interpretables",
            "Selección automática de hiperparámetros por criterio AIC",
            "Produce intervalos de confianza estadísticamente fundamentados",
        ],
        "weaknesses": [
            "Requiere series largas (mínimo 50 semanas recomendado) para estimar los parámetros con fiabilidad",
            "Asume relaciones lineales en la dinámica de la serie",
            "Tiempo de entrenamiento elevado en la búsqueda exhaustiva de hiperparámetros",
        ],
    },
    "Regresión Lineal": {
        "strengths": [
            "Alta interpretabilidad: los coeficientes son directamente legibles",
            "Generaliza bien en series con tendencia lineal estable y baja volatilidad",
            "Robusto ante sobreajuste en datasets pequeños por su baja complejidad",
        ],
        "weaknesses": [
            "No captura relaciones no lineales entre las variables de entrada",
            "La estacionalidad solo se modela mediante features manuales de lag y calendario",
            "Sensible a outliers extremos que distorsionan los coeficientes",
        ],
    },
    "XGBoost": {
        "strengths": [
            "Captura automáticamente relaciones no lineales y patrones complejos",
            "Robusto ante outliers y semanas con ventas cero gracias a la estructura de árboles",
            "Excelente rendimiento en series con alta variabilidad o comportamiento irregular",
        ],
        "weaknesses": [
            "Menor interpretabilidad (modelo de caja negra respecto a SARIMA y regresión)",
            "Riesgo de sobreajuste en series muy cortas (menos de 30 semanas)",
            "No extrapola valores más allá del rango observado en entrenamiento",
        ],
    },
}


# ── Análisis de la serie ──────────────────────────────────────────────

def analyze_series(series: pd.Series) -> dict:
    """
    Calcula características estadísticas clave de la serie temporal.

    Returns
    -------
    dict con claves:
        series_length        int   — número de semanas
        trend_strength       float — cambio total relativo (pendiente normalizada)
        volatility           float — coeficiente de variación (std / media)
        seasonality_strength float — autocorrelación máxima en lags estacionales
        zero_ratio           float — proporción de semanas con ventas = 0
        mean                 float — media de ventas
        std                  float — desviación típica
    """
    arr = np.asarray(series, dtype=float)
    n = len(arr)
    mean_val = float(np.mean(arr)) if n > 0 else 0.0
    std_val = float(np.std(arr)) if n > 0 else 0.0

    # Tendencia: pendiente lineal normalizada por la media
    if n >= 4 and mean_val != 0:
        x = np.arange(n, dtype=float)
        slope, _ = np.polyfit(x, arr, 1)
        trend_strength = float(abs(slope * n / mean_val))
    else:
        trend_strength = 0.0

    # Volatilidad: coeficiente de variación
    volatility = float(std_val / mean_val) if mean_val > 0 else 0.0

    # Estacionalidad: autocorrelación máxima en lags representativos
    def _autocorr(a: np.ndarray, lag: int) -> float:
        if len(a) <= lag:
            return 0.0
        mu = np.mean(a)
        num = np.sum((a[: len(a) - lag] - mu) * (a[lag:] - mu))
        denom = np.sum((a - mu) ** 2)
        return float(num / denom) if denom > 0 else 0.0

    candidate_lags = [lv for lv in [4, 13, 26, 52] if n > lv + 1]
    seasonality_strength = (
        max(abs(_autocorr(arr, lv)) for lv in candidate_lags)
        if candidate_lags
        else 0.0
    )

    zero_ratio = float(np.mean(arr == 0))

    return {
        "series_length": n,
        "trend_strength": round(trend_strength, 3),
        "volatility": round(volatility, 3),
        "seasonality_strength": round(seasonality_strength, 3),
        "zero_ratio": round(zero_ratio, 3),
        "mean": round(mean_val, 2),
        "std": round(std_val, 2),
    }


# ── Etiquetas descriptivas ────────────────────────────────────────────

def _vol_label(v: float) -> str:
    if v > 0.6:
        return "🔴 Alta"
    if v > 0.3:
        return "🟡 Moderada"
    return "🟢 Baja"


def _sea_label(s: float) -> str:
    if s > 0.4:
        return "🔴 Fuerte"
    if s > 0.2:
        return "🟡 Moderada"
    return "🟢 Débil"


def _trend_label(t: float) -> str:
    if t > 0.5:
        return "🔴 Pronunciada"
    if t > 0.2:
        return "🟡 Moderada"
    return "🟢 Estable"


# ── Generación de explicación ─────────────────────────────────────────

def generate_explanation(
    category: str,
    best_model: str,
    all_metrics: dict,
    characteristics: dict,
) -> str:
    """
    Genera en español una explicación estructurada de la selección del modelo.

    Parameters
    ----------
    category        : nombre de la categoría
    best_model      : nombre del modelo ganador
    all_metrics     : {model_name: {mae, rmse, mape}}
    characteristics : salida de analyze_series()

    Returns
    -------
    str  Markdown listo para renderizar con st.markdown()
    """
    ts = characteristics["trend_strength"]
    vol = characteristics["volatility"]
    sea = characteristics["seasonality_strength"]
    n = characteristics["series_length"]
    zr = characteristics["zero_ratio"]

    lines: list[str] = []

    # ── 1. Comparativa de rendimiento ─────────────────────────────────
    lines += [
        "#### 📊 Comparativa de rendimiento en el conjunto de test",
        "",
        "| Modelo | MAE | RMSE | MAPE (%) | |",
        "|--------|----:|-----:|---------:|---|",
    ]
    for model in ["SARIMA", "Regresión Lineal", "XGBoost"]:
        if model in all_metrics:
            m = all_metrics[model]
            badge = "✅ **Seleccionado**" if model == best_model else ""
            lines.append(
                f"| {model} | {m['mae']:.2f} | {m['rmse']:.2f} | {m['mape']:.1f} | {badge} |"
            )
        else:
            lines.append(f"| {model} | — | — | — | ⚠️ No disponible |")

    lines += ["", "---", ""]

    # ── 2. Justificación de la selección ─────────────────────────────
    winner_rmse = all_metrics[best_model]["rmse"]
    other_rmses = {m: all_metrics[m]["rmse"] for m in all_metrics if m != best_model}
    improvement_parts = [
        f"{m}: {((v - winner_rmse) / v * 100):.1f}% peor"
        for m, v in sorted(other_rmses.items(), key=lambda x: x[1])
    ]
    improvement_str = " | ".join(improvement_parts) if improvement_parts else ""

    lines += [
        f"#### 🏆 ¿Por qué se seleccionó **{best_model}**?",
        "",
    ]

    if improvement_str:
        lines.append(
            f"**{best_model}** obtuvo el **menor RMSE ({winner_rmse:.2f})** entre todos los modelos "
            f"evaluados ({improvement_str})."
        )
        lines.append("")

    # Razones basadas en las características de la serie
    reasons: list[str] = []

    if best_model == "SARIMA":
        if sea > 0.3:
            reasons.append(
                f"la serie presenta una **estacionalidad significativa** "
                f"(autocorrelación estacional máxima: {sea:.2f}). "
                "SARIMA la modela de forma explícita mediante sus parámetros estacionales (P, D, Q), "
                "mientras que los modelos ML solo la aproximan con features de lag manuales"
            )
        if ts > 0.4:
            reasons.append(
                f"existe una **tendencia pronunciada** (cambio relativo: {ts:.2f}×). "
                "Los parámetros de diferenciación (d, D) de SARIMA la absorben directamente "
                "sin necesidad de ingeniería de features adicional"
            )
        if n >= 60:
            reasons.append(
                f"la serie es **suficientemente larga** ({n} semanas) para estimar "
                "los parámetros del modelo estadístico con solidez"
            )
        if vol < 0.4:
            reasons.append(
                f"la **volatilidad es contenida** (CV = {vol:.2f}), lo que favorece "
                "los modelos paramétricos que asumen cierta regularidad en la señal"
            )
        if not reasons:
            reasons.append(
                "obtuvo el mejor ajuste empírico al conjunto de test, "
                "posiblemente porque la serie tiene una dinámica temporal "
                "que los parámetros AR/MA capturan con precisión"
            )

    elif best_model == "Regresión Lineal":
        if n < 50:
            reasons.append(
                f"la serie es **corta** ({n} semanas). "
                "La baja complejidad del modelo lineal evita el sobreajuste "
                "que pueden exhibir SARIMA y XGBoost con pocos datos"
            )
        if ts > 0.2 and vol < 0.4:
            reasons.append(
                f"la tendencia es **lineal y estable** "
                f"(cambio relativo: {ts:.2f}×, CV = {vol:.2f}), "
                "exactamente el escenario donde la regresión lineal es óptima"
            )
        if sea < 0.2:
            reasons.append(
                f"la **estacionalidad es débil** (autocorrelación: {sea:.2f}), "
                "por lo que los modelos más complejos no aportan ventaja sobre "
                "los features simples de lag y calendario"
            )
        if not reasons:
            reasons.append(
                "demostró el mejor ajuste empírico, probablemente porque la regularidad "
                "de la serie hace que su capacidad de generalización supere "
                "la flexibilidad adicional de los otros modelos"
            )

    elif best_model == "XGBoost":
        if vol > 0.5:
            reasons.append(
                f"la serie presenta **alta volatilidad** (CV = {vol:.2f}). "
                "Los ensambles de árboles de decisión son más robustos ante picos "
                "y caídas abruptas, sin asumir linealidad en la respuesta"
            )
        if zr > 0.1:
            reasons.append(
                f"hay un **{zr * 100:.0f}% de semanas con ventas cero**. "
                "XGBoost gestiona este patrón de forma natural al no asumir continuidad "
                "ni distribución normal en los residuos"
            )
        if sea > 0.2:
            reasons.append(
                f"la **estacionalidad moderada-fuerte** (autocorrelación: {sea:.2f}) "
                "queda recogida implícitamente por los features de lag y calendario "
                "sin necesidad de especificación explícita del período"
            )
        if ts > 0.3 and vol > 0.4:
            reasons.append(
                "la combinación de **tendencia y alta variabilidad** favorece "
                "a los modelos no lineales que pueden adaptar su frontera de decisión "
                "de forma más flexible que los modelos paramétricos"
            )
        if not reasons:
            reasons.append(
                "capturó mejor los **patrones no lineales** de la serie, "
                "obteniendo el menor error de predicción en el conjunto de test"
            )

    if reasons:
        lines.append(
            "Este modelo fue el más adecuado para esta categoría porque "
            + "; además, ".join(reasons) + "."
        )
        lines.append("")

    lines += ["---", ""]

    # ── 3. Características de la serie ───────────────────────────────
    lines += [
        "#### 📈 Características de la serie detectadas automáticamente",
        "",
        "| Característica | Valor | Interpretación |",
        "|----------------|------:|----------------|",
        f"| Longitud | {n} semanas | {'✅ Suficiente para todos los modelos' if n >= 50 else '⚠️ Serie corta — favorece modelos simples'} |",
        f"| Volatilidad (CV) | {vol:.2f} | {_vol_label(vol)} |",
        f"| Estacionalidad (autocorr.) | {sea:.2f} | {_sea_label(sea)} |",
        f"| Tendencia (normalizada) | {ts:.2f}× | {_trend_label(ts)} |",
        f"| Semanas con ventas = 0 | {zr * 100:.1f}% | {'⚠️ Frecuente — puede afectar a modelos lineales' if zr > 0.15 else 'ℹ️ Ocasional o inexistente'} |",
        "",
        "---",
        "",
    ]

    # ── 4. Fortalezas y debilidades de cada modelo ────────────────────
    lines += [
        "#### ⚖️ Fortalezas y debilidades de cada modelo para esta categoría",
        "",
    ]

    for model in ["SARIMA", "Regresión Lineal", "XGBoost"]:
        sw = _MODEL_SW[model]
        is_best = "✅ " if model == best_model else ""
        available = model in all_metrics

        if available:
            rmse_val = all_metrics[model]["rmse"]
            lines.append(f"**{is_best}{model}** — RMSE en test: {rmse_val:.2f}")
        else:
            lines.append(f"**{model}** — ⚠️ No disponible (serie insuficiente)")

        lines.append("")
        lines.append("*Fortalezas:*")
        for s in sw["strengths"]:
            lines.append(f"- {s}")
        lines.append("")
        lines.append("*Debilidades:*")
        for w in sw["weaknesses"]:
            lines.append(f"- {w}")
        lines.append("")

    return "\n".join(lines)
