import datetime


def generar_informe(resultados_informe: list[dict]) -> str:
    """Llama a Ollama y devuelve el texto del informe ejecutivo."""
    lineas = []
    for r in resultados_informe:
        if r.get("error"):
            lineas.append(f"- {r['cat']}: no se pudo analizar ({r['error']})")
            continue
        n_anomalias = len(r.get("anomalias", []))
        anomalias_txt = f"{n_anomalias} anomalía(s) detectada(s)" if n_anomalias else "sin anomalías destacables"
        lineas.append(
            f"- {r['cat']}: mejor modelo = {r['best_model']}, "
            f"MAPE = {r['mape']:.1f}%, MAE = {r['mae']:.1f} unidades, {anomalias_txt}"
        )

    resumen_datos = "\n".join(lineas)
    prompt = (
        "Eres un consultor de datos para una empresa retail. Aquí están los resultados "
        f"del análisis de forecasting de ventas por categoría:\n{resumen_datos}\n\n"
        "Redacta un informe ejecutivo con esta estructura:\n"
        "1. Resumen general (2-3 frases sobre el estado global de las ventas)\n"
        "2. Resultados por categoría (para cada una: mejor modelo, fiabilidad y si hay anomalías destacables)\n"
        "3. Recomendaciones (2-3 acciones concretas basadas en los datos)\n\n"
        "Máximo 400 palabras. Sin jerga técnica. Escrito para dirección, no para un equipo técnico."
    )

    try:
        import ollama
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
        )
        # ollama>=0.2 returns a ChatResponse object; <0.2 returns a dict
        try:
            return response.message.content.strip()
        except AttributeError:
            return response["message"]["content"].strip()
    except Exception as e:
        return (
            f"Ollama no está disponible ({type(e).__name__}). "
            "Asegúrate de que el servidor está corriendo "
            "(`ollama serve`) y de que el modelo está descargado (`ollama pull llama3.2`)."
        )


def construir_html(texto_informe: str, resultados_informe: list[dict]) -> str:
    """Construye un HTML autocontenido con el texto ejecutivo y los gráficos embebidos."""
    fecha = datetime.date.today().strftime("%d/%m/%Y")

    categorias_html = []
    for r in resultados_informe:
        if r.get("error"):
            categorias_html.append(
                f"<section><h2>{r['cat']}</h2>"
                f"<p class='error'>No se pudo analizar: {r['error']}</p></section>"
            )
            continue

        # Gráfico embebido
        fig_tag = ""
        if r.get("fig_base64"):
            fig_tag = (
                f'<img src="data:image/png;base64,{r["fig_base64"]}" '
                f'style="max-width:100%;margin:12px 0;">'
            )

        # Métricas
        metricas = (
            f"<table><tr><th>Mejor modelo</th><th>MAPE (%)</th><th>MAE (unidades)</th></tr>"
            f"<tr><td>{r['best_model']}</td><td>{r['mape']:.1f}</td><td>{r['mae']:.1f}</td></tr></table>"
        )

        # Anomalías
        anomalias_items = ""
        for a in r.get("anomalias", []):
            signo = "+" if a["variacion_pct"] > 0 else ""
            anomalias_items += f"<li>{a['fecha']}: {signo}{a['variacion_pct']:.1f}%</li>"
        anomalias_html = (
            f"<p><strong>Anomalías detectadas:</strong></p><ul>{anomalias_items}</ul>"
            if anomalias_items else "<p>Sin anomalías destacables.</p>"
        )

        categorias_html.append(
            f"<section><h2>{r['cat']}</h2>{fig_tag}{metricas}{anomalias_html}</section>"
        )

    cuerpo_categorias = "\n".join(categorias_html)
    texto_escapado = texto_informe.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Informe ejecutivo de ventas</title>
<style>
  body {{ font-family: sans-serif; max-width: 960px; margin: 40px auto; color: #1a1a1a; }}
  h1 {{ color: #2563eb; }}
  h2 {{ color: #374151; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; margin-top: 32px; }}
  table {{ border-collapse: collapse; margin: 8px 0; }}
  th, td {{ border: 1px solid #d1d5db; padding: 6px 14px; text-align: left; }}
  th {{ background: #f3f4f6; }}
  pre {{ white-space: pre-wrap; background: #f9fafb; padding: 16px; border-radius: 6px; }}
  .error {{ color: #dc2626; }}
  section {{ margin-bottom: 40px; }}
</style>
</head>
<body>
<h1>Informe ejecutivo de ventas</h1>
<p><strong>Fecha:</strong> {fecha}</p>
<h2>Resumen ejecutivo</h2>
<pre>{texto_escapado}</pre>
<h2>Detalle por categoría</h2>
{cuerpo_categorias}
</body>
</html>"""
