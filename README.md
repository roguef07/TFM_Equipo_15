# Sistema de apoyo a la toma de decisiones empresariales mediante modelos de pronóstico automatizado de ventas
## Equipo 15 - Master en Big Data & Business Intelligence

- Francisco Javier Robles Guevara 
- Marina Palhares Telles Claro 
- Stephany Maria Solano Salas
- Tessa Veronica Yañez Alonso

## Sobre este repositorio:
Este repositorio contiene el MVP (Producto Mínimo Viable) del Trabajo de Fin de Máster (TFM), cuyo objetivo es construir una aplicación local para la predicción de demanda/ventas mediante modelos de forecasting, integrando:

- Ingesta de datos
- Persistencia en base de datos
- Pipeline de modelado
- Generación de predicciones
- Visualización interactiva

La aplicación está desarrollada en Python, utiliza Streamlit como interfaz y SQLite como sistema gestor de base de datos.

## Estructura del repositorio
En este repositorio se encontrará el código desarrollado relacionado con nuestro proyecto
- En la carpeta ([scraping](https://github.com/roguef07/TFM_Equipo_15/tree/main/scraping)) se encuentra todo lo relacionado al proceso de conectar con el API de Kaggle para obtener información relevante a analizar para generar el modelo predictivo de nuestro proyecto.
- En la carpeta ([forecast_app](https://github.com/roguef07/TFM_Equipo_15/tree/main/forecast_app)) se encuentra los modulos que pertenecen a nuestro MVP.
- En la carpet ([doc/diagramas](https://github.com/roguef07/TFM_Equipo_15/tree/main/doc/diagramas)) se puede encontrar el diagramado respectivo al modelo de datos, tanto como sus editables como la imagen del modelo.

## Requisitos previos

Antes de ejecutar la aplicación, es necesario contar con:

* Python **3.10 o superior**
* pip
* Entorno virtual (recomendado)

---

## Instalación

### Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd <nombre-del-repo>
```

---

### Crear entorno virtual (opcional pero recomendado)

```bash
python -m venv venv
```

Activar el entorno:

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

---

### Instalar dependencias

```bash
pip install -r forecast_app/requirements.txt
```

---

## Configurar Ollama (necesario para anomalías e informe ejecutivo)

La app utiliza Ollama como LLM local para generar explicaciones de anomalías e informes ejecutivos. No requiere API key ni conexión a internet.

**RAM recomendada:** mínimo 8 GB (para `llama3.2`), recomendado 16 GB.

1. Descarga e instala Ollama desde [ollama.com/download](https://ollama.com/download)
2. Descarga el modelo (solo la primera vez, ~2 GB):
   ```bash
   ollama pull llama3.2
   ```
3. Arranca el servidor y déjalo corriendo en una terminal aparte:
   ```bash
   ollama serve
   ```

Si Ollama no está corriendo, la app sigue funcionando con normalidad: los modelos de forecasting y los gráficos se calculan y muestran igualmente. Solo las explicaciones de anomalías y el informe ejecutivo mostrarán un aviso en su lugar.

---

## Ejecución de la aplicación

Una vez instaladas las dependencias, ejecutar:

```bash
streamlit run app/main.py
```

Esto abrirá automáticamente la aplicación en el navegador web.

---

## Uso del dataset de ejemplo

En el repositorio se incluye un archivo:

```
forecast_app/ventas_dummy.csv
```

Este archivo puede usarse directamente desde la interfaz de Streamlit como **dataset de prueba**, permitiendo:

* Probar la ingesta de datos
* Ver la persistencia en SQLite
* Ejecutar el pipeline de predicción
* Visualizar resultados

No es necesario cargar datos externos para la evaluación del proyecto.

---

## Flujo de funcionamiento

1. El usuario interactúa con la interfaz Streamlit
2. Se cargan los datos (CSV)
3. Los datos son procesados por el módulo de ingesta
4. Se almacenan en SQLite
5. Se ejecuta el modelo predictivo
6. Las predicciones se persisten en la base de datos
7. Los resultados se visualizan en la aplicación

---

## Modelo de datos

El modelo de datos funcional del sistma es el siguiente, donde se tiene la interacción entre los distintos datasets, los modelos de predicción y la obtenciión de los resultados:
![Modelo de datos (primera versión)](doc/diagramas/Modelo_sistema.jpg)

---


## Archivos no incluidos en el repositorio

Los datasets y el entorno virtual no están en el repo por su tamaño. Aquí cómo recuperarlos:

### Datos (dataset Olist de Kaggle)

Los CSVs originales se descargan con el script incluido. Necesitas una cuenta de Kaggle y tu API key configurada (`~/.kaggle/kaggle.json`):

```bash
cd scrapping
pip install -r requirements.txt
python Download_dataset.py
```

Los archivos se guardan en `scrapping/data/`. El notebook `EDA.ipynb` y el script `app.py` de esa carpeta también generan la tabla analítica `tabla_analitica_olist.csv` que usa la app principal.

### Entorno virtual

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r forecast_app/requirements.txt
```

---

## Módulos de `forecast_app`

| Archivo | Función |
|---------|---------|
| `app.py` | Orquestador Streamlit: carga de datos, EDA, selección de modelos, renderizado y sección de informe |
| `preprocessing.py` | Limpia el CSV y agrega a nivel semanal por categoría |
| `model_selection.py` | Entrena SARIMA, Regresión Lineal y XGBoost; elige el mejor por RMSE |
| `models.py` | Búsqueda de hiperparámetros SARIMA por AIC |
| `pipelines.py` | Pipelines sklearn para Regresión Lineal y XGBoost |
| `features.py` | Ingeniería de características (lags, medias móviles, variables de calendario) |
| `forecast.py` | Genera predicciones futuras con el modelo ganador |
| `evaluation.py` | Calcula MAE, RMSE y MAPE |
| `explainer.py` | Analiza la serie y genera la explicación de selección de modelo |
| `anomaly_detector.py` | Detecta semanas atípicas (>1.5σ) y genera hipótesis vía Ollama |
| `report_generator.py` | Genera el texto ejecutivo vía Ollama y construye el HTML autocontenido para descarga |

---

> [!NOTE]
> Work in progress.
