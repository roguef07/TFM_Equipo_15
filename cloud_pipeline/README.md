# Cloud Pipeline – Customer Shopping Data

Arquitectura Cloud-Native para Forecasting Retail

## Descripción del Proyecto

Este proyecto corresponde al desarrollo del MVP técnico de la asignatura de Cloud Computing y Big Data, utilizando como base el Trabajo Fin de Máster (TFM) del equipo.

El objetivo es construir un pipeline de datos tipo Cloud-Native reproducible localmente mediante Docker, aplicando conceptos de:

- Data Lakehouse
- Arquitectura OLTP vs OLAP
- Procesamiento distribuido
- Contenedorización
- Business Intelligence

El proyecto utiliza el dataset **Customer Shopping Dataset** obtenido mediante la API de Kaggle.

---

# Arquitectura General del Pipeline

Kaggle API  
↓  
LocalStack (S3 – Capa Raw)  
↓  
PySpark (Transformación y limpieza)  
↓  
Parquet (Capa Gold)  
↓  
PostgreSQL (Data Warehouse)  
↓  
SQL Data Mart  
↓  
Power BI

---

# Tecnologías Utilizadas

| Tecnología | Propósito |
|---|---|
| Docker | Contenedorización |
| Docker Compose | Orquestación local |
| LocalStack | Simulación de AWS S3 |
| PySpark | Procesamiento distribuido |
| PostgreSQL | Data Warehouse |
| SQLAlchemy | Conexión Python ↔ PostgreSQL |
| Kaggle API | Descarga automática del dataset |
| Power BI | Visualización y dashboards |
| Kubernetes / Minikube | Bonus opcional |

---

# Estructura del Proyecto

```text
cloud_pipeline/
│
├── data/
│
├── docs/
│
├── kubernetes/
│
├── powerbi/
│
├── screenshots/
│
├── scripts/
│   ├── 00_download_kaggle.py
│   ├── 01_upload_s3.py
│   ├── 02_spark_transform.py
│   └── 03_load_postgres.py
│
├── sql/
│   └── datamart.sql
│
├── docker-compose.yml
├── requirements.txt
└── README.md
