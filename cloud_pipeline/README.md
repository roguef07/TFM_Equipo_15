# Cloud Pipeline – Customer Shopping Data  
## Arquitectura Cloud-Native 
---

# Descripción del Proyecto

Este proyecto corresponde al desarrollo del MVP técnico de la asignatura de **Fundamentos de Cloud Computing**, utilizando como base el Trabajo Fin de Máster (TFM) del equipo.

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
| psycopg2 | Conexión Python y PostgreSQL |
| Kaggle API | Descarga automática del dataset |
| Power BI | Visualización y dashboards (Opcional)|
| Apache Airflow | Orquestación del pipeline |

---

# Estructura del Proyecto

```text
cloud_pipeline/
│
├── dags/
│   └── pipeline_dag.py              <- DAG de Airflow
│
├── data/                            <- Generado en runtime (no en repo)
│
├── scripts/
│   ├── 00_download_kaggle.py
│   ├── 01_upload_s3.py
│   ├── 02_spark_transform.py
│   ├── 03_load_postgres.py
│   └── 04_create_datamart.py
│
├── sql/
│   └── datamart.sql
│
├── docker-compose.yml
├── docker-compose.airflow.yml       <- Entorno Airflow
├── Dockerfile.airflow               <- Imagen Airflow + Java
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

# Requisitos del Sistema

Para poder ejecutar correctamente el proyecto es necesario instalar las siguientes herramientas:

| # | Requisito | Versión mínima | Descarga | Comprobación |
|---|---|---|---|---|
| 1 | **Git** | 2.x | https://git-scm.com/downloads | `git --version` |
| 2 | **Docker Desktop** | 4.x | https://www.docker.com/products/docker-desktop | `docker --version` |
| 3 | **Python** | 3.9+ | https://www.python.org/downloads/ | `python --version` |
| 4 | **Java JDK** | 17 (LTS) | https://adoptium.net/ | `java -version` |


## Configurar Java en Windows (obligatorio para PySpark)

PySpark requiere Java y la variable de entorno `JAVA_HOME` apuntando al JDK.

**1. Instalar Java 17 desde Adoptium:**
https://adoptium.net/ → descargar el instalador `.msi` de Temurin 17 (LTS)

**2. Configurar `JAVA_HOME`** (si el instalador no lo hace automáticamente):

```text
Panel de control → Sistema → Configuración avanzada del sistema
→ Variables de entorno → Nueva (variables del sistema)

Nombre: JAVA_HOME
Valor:  C:\Program Files\Eclipse Adoptium\jdk-17.x.x.x-hotspot
```

**3. Añadir Java al PATH:**
```text
Variables de entorno → Path → Editar → Nuevo
%JAVA_HOME%\bin
```

**4. Verificar:**
```bash
java -version
# Debe mostrar: openjdk version "17.x.x"
echo %JAVA_HOME%
# Debe mostrar la ruta del JDK
```

---

# Preparación del Entorno

## 1. Clonar el repositorio

```bash
git clone https://github.com/roguef07/TFM_Equipo_15.git
cd TFM_Equipo_15/cloud_pipeline
```

## 2. Entrar a la rama cloud

```bash
git checkout Asignatura-Cloud
```

## 3. Crear y activar entorno virtual Python

Se recomienda usar un entorno virtual para aislar las dependencias del proyecto:

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

## 4. Instalar dependencias Python

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

## Configurar Kaggle

| SO | Ruta |
|---|---|
| Windows | `C:\Users\TU_USUARIO\.kaggle\kaggle.json` |
| Linux/Mac | `~/.kaggle/kaggle.json` |

> Este archivo no debe subirse a GitHub.

---

# Levantar el Entorno Docker

```bash
docker compose up -d
```

## Servicios levantados

| Servicio | Puerto | Descripción |
|---|---|---|
| LocalStack | 5500 | Simulación de AWS S3 |
| PostgreSQL | 5432 | Data Warehouse |

Esperar a que los servicios estén saludables:

```bash
docker compose ps
```

---

# Ejecución del Pipeline

## Con Airflow (Opción Recomendada)

Apache Airflow orquesta los 5 scripts automáticamente en orden, con reintentos y monitorización desde una interfaz web.

> **Requisito previo:** el entorno base debe estar levantado primero:
> ```bash
> docker compose up -d
> ```
> Airflow corre dentro de Docker y se comunica con LocalStack y PostgreSQL por red interna (`localstack:4566` y `postgres_dw:5432`). Los puertos del host (5500, 5432) son solo para la ejecución manual desde tu máquina.

### Construir y levantar entorno Airflow

La imagen de Airflow incluye Java (para PySpark) y se construye localmente:

```bash
docker compose -f docker-compose.airflow.yml up -d --build
```

La primera vez puede tardar varios minutos por la descarga e instalación de Java y PySpark.

### Acceder a la UI de Airflow

```
http://localhost:8080
Usuario: admin
Contraseña: admin
```

### Activar el DAG

1. Abrir la UI de Airflow en `http://localhost:8080`
2. Buscar el DAG `customer_shopping_pipeline`
3. Activar el toggle (ON)
4. Hacer clic en "Trigger DAG" para ejecutarlo manualmente

El DAG ejecuta en orden: descarga del dataset → subida a S3 → transformación PySpark → carga a PostgreSQL → creación del Datamart.


### Apagar entorno Airflow

```bash
docker compose -f docker-compose.airflow.yml down
```

---

## Ejecución Manual (Alternativa)

Ejecutar los scripts **en orden**:

Nota: Para la ejecución manual es necesario instalar las dependencias del requirements.txt

```bash
pip install -r requirements.txt

```

### Paso 1 – Descargar Dataset desde Kaggle

```bash
python scripts/00_download_kaggle.py
```

**Resultado:** CSV descargado en `data/customer_shopping_data.csv`

---

### Paso 2 – Subida a LocalStack S3 (Capa Raw)

```bash
python scripts/01_upload_s3.py
```

**Resultado:** CSV en `s3://data-lake-crudo/raw/customer_shopping_data.csv`

---

### Paso 3 – Procesamiento PySpark (Capa Gold)

```bash
python scripts/02_spark_transform.py
```

**Transformaciones realizadas:**
- Eliminación de duplicados y nulos
- Normalización de tipos (fechas, numéricos, texto)
- Filtrado de registros inválidos
- Agregación por fecha, categoría y centro comercial

**Resultado:** Parquet en `data/gold/` y en `s3://data-lake-crudo/gold/`

---

### Paso 4 – Ingesta al Data Warehouse PostgreSQL

```bash
python scripts/03_load_postgres.py
```

**Qué hace:**
1. Descarga el Parquet Gold desde `s3://data-lake-crudo/gold/` (LocalStack)
2. Lo carga en PostgreSQL como tabla `customer_sales_gold`

**Resultado:** Tabla `customer_sales_gold` en la base de datos `retail_dw`

---

### Paso 5 – Creación del Data Mart

Para ejecución manual (sin Airflow):

```bash
python scripts/04_create_datamart.py
```

**Alternativa directa vía SQL:**

**Windows (PowerShell):**
```powershell
Get-Content sql\datamart.sql | docker exec -i postgres_dw psql -U admin -d retail_dw
```

**Linux / Mac:**
```bash
docker exec -i postgres_dw psql -U admin -d retail_dw < sql/datamart.sql
```
---

# Conexión con Power BI (Opcional)

| Parámetro | Valor |
|---|---|
| Servidor | localhost |
| Puerto | 5432 |
| Base de datos | retail_dw |
| Usuario | admin |
| Contraseña | admin123 |

Conectar mediante: **Obtener datos → Base de datos PostgreSQL**

---

# Solución de Problemas Frecuentes

| Error | Causa | Solución |
|---|---|---|
| `Java gateway process exited` | Java no instalado o `JAVA_HOME` no configurado | Instalar JDK 17 y configurar `JAVA_HOME` |
| `EndpointConnectionError` al ejecutar `01_upload_s3.py` | LocalStack no está levantado | `docker compose up -d` y esperar a que el healthcheck sea `healthy` |
| `NoSuchKey` al ejecutar `02_spark_transform.py` | No se ejecutó `01_upload_s3.py` antes | Ejecutar los scripts en orden |
| `RuntimeError: Fallo al descargar el Parquet Gold` al ejecutar `03_load_postgres.py` | No se ejecutó `02_spark_transform.py` antes, o LocalStack no está levantado | Ejecutar los scripts en orden; verificar `docker compose up -d` |
| `could not connect to server` al ejecutar `03_load_postgres.py` | PostgreSQL no está levantado | `docker compose up -d` |
| `ModuleNotFoundError` | Dependencias no instaladas o entorno virtual no activado | Activar `.venv` y ejecutar `pip install -r requirements.txt` |

---

# Buenas Prácticas Aplicadas

- Arquitectura reproducible con Docker
- Separación entre capa Raw y Gold
- Formato Parquet columnar para optimización analítica
- Separación conceptual OLTP vs OLAP
- Procesamiento distribuido con PySpark
- Manejo de errores con mensajes descriptivos
- Versionamiento mediante GitHub
- Modularización del pipeline ETL (un script por etapa)
- Orquestación con Airflow

---

# Autores

Proyecto desarrollado como parte de la asignatura de:

**Fundamentos en Cloud Computing**  
TFM Equipo 15 – Máster en Big Data and Business Intelligence
