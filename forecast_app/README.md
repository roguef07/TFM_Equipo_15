# Sistema de Pronóstico de Ventas Semanales

Aplicación Streamlit para el pronóstico de ventas semanales por categoría de producto. Soporta tres modelos de predicción: **SARIMA**, **Regresión Lineal** y **XGBoost**.

---

## Requisitos e instalación

**Python 3.9 o superior requerido.**

```bash
pip install -r requirements.txt
```

### Dependencias principales

| Paquete | Uso |
|---------|-----|
| `streamlit` | Interfaz de usuario web |
| `pandas` | Manipulación de datos |
| `numpy` | Cálculo numérico |
| `scikit-learn` | Pipelines ML (Regresión Lineal) |
| `xgboost` | Modelo de gradient boosting |
| `statsmodels` | Modelo SARIMA |
| `matplotlib` | Visualizaciones |

---

## Cómo ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en el navegador en `http://localhost:8501`.

---

## Formato del archivo CSV de entrada

El CSV debe contener al menos cuatro columnas (los nombres se seleccionan en la interfaz):

| Tipo de columna | Ejemplo de nombre | Descripción |
|-----------------|-------------------|-------------|
| Fecha | `fecha`, `date` | Fecha de la transacción |
| Categoría | `categoria`, `product_type` | Etiqueta de categoría del producto |
| Cantidad | `cantidad`, `units_sold` | Unidades vendidas |
| Precio | `precio`, `unit_price` | Precio unitario |

La columna de ventas (`ventas = cantidad × precio`) se calcula automáticamente.

---

## Flujo de trabajo de la aplicación

1. **Carga del CSV** — Sube tu archivo de datos históricos.
2. **Selección de columnas** — Mapea las cuatro columnas requeridas mediante los selectores.
3. **Procesar datos** — La aplicación limpia, valida y agrega los datos a frecuencia semanal por categoría. Las semanas sin datos se rellenan con cero.
4. **EDA** — Explora los datos con cuatro vistas analíticas:
   - Estadísticas descriptivas globales y por categoría
   - Tendencia global de ventas semanales
   - Ventas superpuestas por categoría
   - Estacionalidad: ventas promedio por semana del año
5. **Configuración del modelo** — Selecciona el modelo y el horizonte de pronóstico (1–52 semanas).
6. **Entrenar y pronosticar** — Se entrena un modelo independiente por categoría. Se muestran métricas de evaluación y los pronósticos futuros con visualización.

---

## Estructura del proyecto

| Archivo | Responsabilidad |
|---------|----------------|
| `app.py` | UI Streamlit, gestión de estado, sección EDA, flujo de entrenamiento |
| `preprocessing.py` | Limpieza de datos, conversión de tipos, agregación semanal, relleno de semanas faltantes |
| `features.py` | Construcción de features de lag (lag-1, lag-4) y calendáricas (semana del año, mes) |
| `models.py` | Búsqueda exhaustiva de hiperparámetros SARIMA por AIC |
| `pipelines.py` | Pipelines scikit-learn para Regresión Lineal y XGBoost |
| `forecast.py` | Pronóstico iterativo hacia el futuro para modelos SARIMA y ML |
| `evaluation.py` | Cálculo de métricas MAE, RMSE y MAPE |
| `requirements.txt` | Dependencias del entorno |

---

## Descripción de los modelos

### SARIMA (Seasonal AutoRegressive Integrated Moving Average)

Modelo estadístico de series temporales que captura tendencia, estacionalidad y autocorrelación. La selección de hiperparámetros se realiza mediante búsqueda exhaustiva sobre p, d, q ∈ {0, 1} y P, D, Q ∈ {0, 1} con período estacional = 52 semanas. El modelo con menor AIC es seleccionado automáticamente.

**Recomendación:** Requiere al menos 2 años de historia semanal por categoría para resultados fiables.

### Regresión Lineal

Pipeline de scikit-learn con escalado estándar (`StandardScaler`) seguido de `LinearRegression`. Usa como features: lag-1, lag-4, semana del año y mes. Es el modelo más interpretable y rápido.

### XGBoost

Gradient boosting sobre árboles de decisión mediante `XGBRegressor` (100 estimadores, profundidad máxima 5, tasa de aprendizaje 0.1). No requiere escalado. Generalmente captura mejor las no linealidades y estacionalidades complejas.

---

## Métricas de evaluación

| Métrica | Descripción |
|---------|-------------|
| **MAE** | Error Absoluto Medio — promedio de errores absolutos en las mismas unidades que las ventas |
| **RMSE** | Raíz del Error Cuadrático Medio — penaliza más los errores grandes |
| **MAPE (%)** | Error Porcentual Absoluto Medio — error relativo, útil para comparar entre categorías con distinta escala |

---

## Limitaciones conocidas

- La búsqueda SARIMA es exhaustiva sobre un espacio pequeño (64 combinaciones). Para series largas, considerar `pmdarima.auto_arima` como alternativa más eficiente.
- Los features de lag requieren un mínimo de 4 semanas de historia por categoría; categorías con menos datos son omitidas con un aviso.
- El pronóstico iterativo de los modelos ML acumula error en horizontes largos (>12 semanas).
