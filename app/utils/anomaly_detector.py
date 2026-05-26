import pandas as pd


def detectar_anomalias(df: pd.DataFrame, categoria: str, modelo_ollama: str = "llama3.2") -> list[dict]:
    """
    Detecta semanas donde quantity se desvía >1.5σ de la media histórica
    y solicita a Ollama una hipótesis en lenguaje natural por cada una.

    Returns list of dicts: {fecha, desviacion_std, variacion_pct, explicacion}
    """
    serie = df["quantity"]
    media = serie.mean()
    std = serie.std()

    if std == 0:
        return []

    mascara = (serie - media).abs() > 1.5 * std
    anomalos = df[mascara].copy()

    if anomalos.empty:
        return []

    anomalos["_desviacion_abs"] = (anomalos["quantity"] - media).abs()
    anomalos = anomalos.nlargest(3, "_desviacion_abs").drop(columns="_desviacion_abs")

    try:
        import ollama
        ollama_disponible = True
    except ImportError:
        ollama_disponible = False

    resultados = []
    for _, fila in anomalos.iterrows():
        fecha = fila["week"].strftime("%Y-%m-%d")
        variacion_pct = (fila["quantity"] - media) / media * 100
        desviacion_std = (fila["quantity"] - media) / std

        if ollama_disponible:
            prompt = (
                f"Eres un analista de ventas retail. En la categoría {categoria}, detectamos "
                f"una anomalía en {fecha}: las ventas variaron un {variacion_pct:.1f}% respecto "
                f"a la media histórica. Dame una hipótesis breve y accionable en 2-3 frases, "
                f"sin jerga técnica."
            )
            try:
                respuesta = ollama.chat(
                    model=modelo_ollama,
                    messages=[{"role": "user", "content": prompt}],
                )
                explicacion = respuesta["message"]["content"].strip()
            except Exception:
                explicacion = (
                    "Ollama no está disponible. Asegúrate de que el servidor está corriendo "
                    "(`ollama serve`) y de que el modelo está descargado (`ollama pull llama3.2`)."
                )
        else:
            explicacion = (
                "Paquete `ollama` no instalado. Ejecuta `pip install ollama` para activar "
                "las explicaciones automáticas."
            )

        resultados.append({
            "fecha": fecha,
            "desviacion_std": round(desviacion_std, 2),
            "variacion_pct": round(variacion_pct, 1),
            "explicacion": explicacion,
        })

    return resultados
