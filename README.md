# Cloud Pipeline – Customer Shopping Data  
## Arquitectura Cloud-Native para Forecasting Retail

---

# Descripción del Proyecto

Este proyecto corresponde al desarrollo del MVP técnico de la asignatura de **Cloud Computing y Big Data**, utilizando como base el Trabajo Fin de Máster (TFM) del equipo.

El objetivo es construir un pipeline de datos tipo **Cloud-Native** reproducible localmente mediante Docker, aplicando conceptos de:

- Data Lakehouse
- Arquitectura OLTP vs OLAP
- Procesamiento distribuido
- Contenedorización
- Business Intelligence

El proyecto utiliza el dataset **Customer Shopping Dataset** obtenido mediante la API de Kaggle.

---

# Arquitectura General del Pipeline

```text
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
```

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
```

---

# Dataset Utilizado

- **Dataset:** Customer Shopping Dataset  
- **Fuente:**  
  https://www.kaggle.com/datasets/mehmettahiraslan/customer-shopping-dataset

## Variables principales del dataset

- Fecha de compra
- Categoría
- Precio
- Cantidad
- Método de pago
- Género
- Edad
- Centro comercial

---

# Preparación del Entorno

## 1. Clonar el repositorio

```bash
git clone https://github.com/roguef07/TFM_Equipo_15.git
```

## 2. Entrar a la rama cloud

```bash
git checkout Asignatura-Cloud
```

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

# Configuración de Kaggle API

## Crear cuenta en Kaggle

https://www.kaggle.com/

## Descargar credenciales

Ir a:

```text
Profile → Settings → API → Create New Token
```

Se descargará un archivo llamado:

```text
kaggle.json
```

## Configurar Kaggle en Windows

Mover el archivo a:

```text
C:\Users\TU_USUARIO\.kaggle\
```

> *Importante*:  
> Cada integrante debe configurar localmente su archivo `kaggle.json`.  
> Este archivo NO debe subirse a GitHub.

---

# Levantar el Entorno Docker

Ejecutar:

```bash
docker compose up -d
```

## Servicios levantados

- LocalStack
- PostgreSQL
- Spark

---

# Pipeline de Ejecución

---

## Paso 1 – Descargar Dataset desde Kaggle

```bash
python scripts/00_download_kaggle.py
```

### Resultado esperado

- Dataset descargado automáticamente
- CSV almacenado en `data/`

---

## Paso 2 – Subida a LocalStack S3 (Capa Raw)

```bash
python scripts/01_upload_s3.py
```

### Resultado esperado

- Bucket S3 creado
- CSV almacenado en LocalStack

---

## Paso 3 – Procesamiento PySpark (Capa Gold)

```bash
python scripts/02_spark_transform.py
```

### Transformaciones realizadas

- Limpieza básica de datos
- Tratamiento de valores nulos
- Eliminación de duplicados
- Conversión de fechas
- EDA básico del dataset
- Agregación por categoría y fecha

### Resultado esperado

- Datos almacenados en formato Parquet
- Generación de capa Gold analítica

---

## Paso 4 – Ingesta al Data Warehouse PostgreSQL

```bash
python scripts/03_load_postgres.py
```

### Resultado esperado

- Tabla cargada correctamente en PostgreSQL
- Data Warehouse disponible para BI

---

## Paso 5 – Creación del Data Mart

Ejecutar:

```sql
sql/datamart.sql
```

### Resultado esperado

- Vista optimizada para consumo analítico y dashboards

---

# Conexión con Power BI

Conectar Power BI a PostgreSQL utilizando los siguientes parámetros:

| Parámetro | Valor |
|---|---|
| Servidor | localhost |
| Puerto | 5432 |
| Base de datos | retail_dw |
| Usuario | admin |
| Contraseña | admin123 |

---

# Buenas Prácticas Aplicadas

- Arquitectura reproducible con Docker
- Separación entre capa Raw y Gold
- Uso de Parquet para optimización analítica
- Separación conceptual OLTP vs OLAP
- Procesamiento distribuido con Spark
- Versionamiento mediante GitHub
- Modularización del pipeline ETL

---

# Posibles Mejoras Futuras

- Automatización con Apache Airflow
- Orquestación con Kubernetes
- Dashboards en tiempo real
- Integración con servicios cloud reales (AWS/GCP)
- Implementación de CI/CD
- Monitoreo del pipeline

---

# Autores

Proyecto desarrollado como parte de la asignatura de:

**Cloud Computing y Big Data**  
TFM Equipo 15 – Máster en Analítica de Datos
