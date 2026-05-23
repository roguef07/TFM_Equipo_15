# Proyecto Final – Cloud Computing y Big Data
## TFM Equipo 15 – Máster en Big Data and Business Intelligence
### Arquitectura Cloud aplicada al TFM del grupo: Forecasting Retail

---

> **Repositorio de Código:**  
> https://github.com/roguef07/TFM_Equipo_15 (rama: `Asignatura-Cloud`)

---

## FASE 1: Diseño de Arquitectura Cloud (Teórico)

---

### 1. Diagrama de Arquitectura

El siguiente diagrama refleja el ciclo de vida completo del dato, desde la ingesta
de fuentes OLTP hasta el consumo final por la herramienta de Business Intelligence.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FUENTES DE DATOS (OLTP)                              │
│                                                                             │
│   ┌──────────────┐       ┌──────────────┐       ┌──────────────────────┐   │
│   │  Kaggle API  │       │  Sistemas POS│       │  Logs de e-commerce  │   │
│   │  (CSV ventas)│       │  (BD retail) │       │  (clickstream)       │   │
│   └──────┬───────┘       └──────┬───────┘       └──────────┬───────────┘   │
└──────────┼────────────────────┼──────────────────────────┼───────────────-─┘
           │                    │                           │
           ▼                    ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CAPA DE INGESTA (AWS / LocalStack)                      │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │              Amazon S3  –  Data Lake  (Capa RAW)                  │     │
│   │            s3://data-lake-crudo/raw/customer_shopping.csv         │     │
│   └───────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   CAPA DE PROCESAMIENTO (AWS EMR / PySpark)                 │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  PySpark – Limpieza, normalización, agregación por fecha/categoría│     │
│   │  Salida: s3://data-lake-crudo/gold/customer_sales_parquet/        │     │
│   │  Formato: Apache Parquet (columnar, comprimido)                   │     │
│   └───────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              CAPA SERVING – DATA WAREHOUSE (Amazon RDS / PostgreSQL)        │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  Tabla: customer_sales_gold                                        │     │
│   │  Vistas Data Mart: dm_ventas_por_categoria_mes                     │     │
│   │                    dm_ranking_shopping_mall                        │     │
│   │                    dm_evolucion_diaria                             │     │
│   │                    dm_dashboard_bi                                 │     │
│   └───────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CAPA DE CONSUMO (Power BI / Tableau)                   │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  Dashboard de ventas por categoría, centro comercial y tendencias  │     │
│   │  Modelos de forecasting retail                                     │     │
│   └───────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **Nota:** Para la versión local (MVP Cloud-in-Local), AWS S3 es sustituido por
> **LocalStack**, AWS EMR por **PySpark local**, y Amazon RDS por
> **PostgreSQL en Docker**. El código es idéntico, solo cambia el endpoint.

---

### 2. Justificación Tecnológica

#### 2.1 Elección del proveedor Cloud: Amazon Web Services (AWS)

Se elige **AWS** por los siguientes motivos:

- **Madurez del ecosistema**: AWS es el proveedor con mayor cuota de mercado y el
  más amplio catálogo de servicios gestionados para Big Data.
- **Compatibilidad con LocalStack**: LocalStack emula de forma nativa los servicios
  AWS (S3, Lambda, RDS), lo que permite un desarrollo local sin coste y una
  migración a producción mínima.
- **Integración nativa con PySpark**: Amazon EMR (Elastic MapReduce) está
  optimizado para ejecutar cargas Spark con configuración mínima.

#### 2.2 Justificación de cada servicio

| Servicio AWS | Equivalente Local (MVP) | Justificación |
|---|---|---|
| **Amazon S3** | LocalStack S3 | Almacenamiento de objetos escalable, bajo coste, soporte nativo de Parquet. Actúa como Data Lake separando capa RAW y Gold. |
| **Amazon EMR + PySpark** | PySpark local (Docker) | Procesamiento distribuido sin gestión de infraestructura. Permite escalar el clúster según demanda sin aprovisionar servidores. |
| **Amazon RDS (PostgreSQL)** | PostgreSQL 16 (Docker) | DBaaS gestionado: copias de seguridad automáticas, escalado vertical, alta disponibilidad. Evita la gestión manual de IaaS (EC2 + PostgreSQL). |
| **AWS Glue / boto3** | boto3 | Orquestación de la ingesta; en producción se usaría AWS Glue para Crawlers y catálogo de datos. |
| **Power BI** | Power BI Desktop | Herramienta de BI ampliamente adoptada en entornos empresariales con conector nativo a PostgreSQL. |

#### 2.3 Separación OLTP vs OLAP

La arquitectura diferencia explícitamente dos mundos:

| Aspecto | OLTP (origen) | OLAP (destino) |
|---|---|---|
| **Propósito** | Registro transaccional en tiempo real | Análisis histórico y agregaciones |
| **Modelo de datos** | Normalizado (3NF), muchas tablas pequeñas | Desnormalizado (estrella/copo de nieve) |
| **Consultas** | Escrituras frecuentes, lecturas puntuales | Lecturas masivas sobre grandes volúmenes |
| **Tecnología en este proyecto** | Kaggle CSV / sistemas POS externos | PostgreSQL Data Warehouse + Data Mart |
| **Formato de almacenamiento** | CSV crudo (Capa RAW en S3) | Parquet columnar (Capa Gold en S3) |

Esta separación es fundamental porque:

1. **Rendimiento**: Las consultas analíticas sobre millones de filas no penalizan
   las transacciones operacionales del negocio.
2. **Integridad**: Los sistemas OLTP no se ven afectados por transformaciones o
   cargas masivas del pipeline ETL.
3. **Escalabilidad independiente**: Se puede escalar el Data Warehouse (RDS) sin
   tocar los sistemas de origen.

#### 2.4 DBaaS vs IaaS – Por qué elegir servicios gestionados

Se opta por **DBaaS (Amazon RDS)** frente a una base de datos instalada en una
instancia EC2 (IaaS) por las siguientes razones:

| Criterio | IaaS (EC2 + PostgreSQL manual) | DBaaS (Amazon RDS) |
|---|---|---|
| **Gestión de SO** | Responsabilidad del equipo | AWS lo gestiona |
| **Parches de seguridad** | Manuales | Automáticos |
| **Backups** | Configuración manual | Automatizados y gestionados |
| **Alta disponibilidad** | Requiere configuración adicional | Multi-AZ con 1 clic |
| **Coste operativo** | Alto (tiempo de ingeniería) | Incluido en el servicio |
| **Escalabilidad** | Requiere migración manual | Vertical con downtime mínimo |

> En el MVP local se usa PostgreSQL en Docker para mantener el mismo motor de base
> de datos y facilitar la migración a RDS en producción sin cambios de código.

#### 2.5 Uso de Apache Parquet como formato columnar

El pipeline almacena la capa Gold en **formato Parquet** en lugar de CSV por:

- **Compresión**: Parquet reduce el almacenamiento entre un 70-85% respecto a CSV
  equivalente.
- **Rendimiento de lectura**: Las consultas analíticas solo leen las columnas
  necesarias (proyección de columnas), reduciendo el I/O drásticamente.
- **Tipos de datos nativos**: Preserva tipos (date, double, int) sin necesidad de
  conversión al cargar en PostgreSQL.
- **Compatibilidad**: Compatible con S3, Spark, Athena, Redshift Spectrum y
  herramientas de BI directamente.

---

### 3. Estimación de Costes (High-Level)

#### 3.1 Supuestos del escenario

- Dataset: ~100.000 filas CSV, ~10 MB de datos crudos, ~2 MB en Parquet
- Frecuencia de actualización: diaria (1 ejecución/día)
- Región AWS: eu-west-1 (Irlanda)
- Usuarios concurrentes Power BI: 5

#### 3.2 Desglose de costes mensuales estimados (AWS)

| Servicio | Configuración | Coste estimado/mes |
|---|---|---|
| **Amazon S3** | 1 GB almacenamiento + 30 peticiones/día | ~$0.02 |
| **Amazon EMR (Spark)** | 1 instancia m5.xlarge × 15 min/día | ~$2.50 |
| **Amazon RDS (PostgreSQL)** | db.t3.micro, 20 GB SSD, Single-AZ | ~$15.00 |
| **AWS Glue / boto3 (ingesta)** | 1 DPU × 15 min/día | ~$1.50 |
| **Transferencia de datos** | Salida a Power BI (~100 MB/mes) | ~$0.01 |
| **Total estimado** | | **~$19 / mes** |

> Para un dataset de mayor volumen (escala TFM completa con millones de registros),
> el coste podría crecer en el componente EMR y RDS (instancias más grandes).

#### 3.3 Principales generadores de coste

1. **Amazon RDS**: Es el servicio de mayor coste continuo porque la instancia de
   base de datos corre 24/7, incluso fuera del horario de ejecución del pipeline.
2. **Amazon EMR**: Aunque se lanza solo durante la ejecución, las instancias EC2
   subyacentes tienen un coste por hora. Para datasets pequeños como el del MVP,
   es el componente más caro por ejecución.

#### 3.4 Estrategias arquitectónicas para minimizar costes

| Estrategia | Ahorro estimado | Descripción |
|---|---|---|
| **Formato Parquet** | 70-85% en almacenamiento S3 y I/O | Reduce el tamaño de los datos y el tiempo de procesamiento de Spark. |
| **EMR on-demand vs reservado** | Hasta 40% con instancias reservadas | Para pipelines con ejecución fija diaria, contratar instancias reservadas de 1 año reduce el coste de EMR significativamente. |
| **RDS en modo Serverless v2 (Aurora)** | Variable (paga por uso) | Para cargas analíticas con picos predecibles, Aurora Serverless v2 escala a 0 ACUs fuera del horario laboral, eliminando el coste base nocturno. |
| **Particionamiento de datos en S3** | 30-60% en consultas Athena | Particionando la capa Gold por año/mes/día, Athena y Spark solo escanean las particiones necesarias. |
| **Lifecycle policies en S3** | 20-40% en almacenamiento a largo plazo | Mover datos RAW a S3 Glacier después de 30 días reduce el coste de almacenamiento en un 80%. |
| **Apagado automático de RDS fuera de horario** | 50-60% en desarrollo | Usar AWS Instance Scheduler para apagar la instancia RDS por las noches y fines de semana en entornos no productivos. |

---

## FASE 2: Prototipo Funcional MVP (Cloud-in-Local)

### Resumen del Pipeline implementado

| Etapa | Script | Herramienta | Resultado |
|---|---|---|---|
| 1. Descarga dataset | `00_download_kaggle.py` | Kaggle API | CSV en `data/` |
| 2. Capa RAW (Ingesta) | `01_upload_s3.py` | boto3 + LocalStack | CSV en `s3://data-lake-crudo/raw/` |
| 3. Capa Gold (Transformación) | `02_spark_transform.py` | PySpark + boto3 | Parquet en `s3://data-lake-crudo/gold/` |
| 4. Data Warehouse | `03_load_postgres.py` | SQLAlchemy + PostgreSQL | Tabla `customer_sales_gold` en `retail_dw` |
| 5. Data Mart | `sql/datamart.sql` | SQL (PostgreSQL) | 4 vistas analíticas listas para BI |

### Transformaciones PySpark aplicadas (Capa Gold)

- Eliminación de duplicados (`dropDuplicates`)
- Tratamiento de nulos en columnas críticas (`dropna`)
- Normalización de tipos: fechas (`make_date`), numéricos (`cast`)
- Limpieza de texto: eliminación de espacios (`trim`)
- Filtrado de registros inválidos (precios negativos, edades fuera de rango)
- Agregación por `invoice_date`, `category`, `shopping_mall`:
  - `ventas_totales`, `unidades_vendidas`, `cantidad_transacciones`, `ticket_promedio`

### Vistas Data Mart creadas (`sql/datamart.sql`)

| Vista | Propósito |
|---|---|
| `dm_ventas_por_categoria_mes` | Ventas mensuales por categoría de producto |
| `dm_ranking_shopping_mall` | Ranking de centros comerciales por ventas |
| `dm_evolucion_diaria` | Serie temporal de ventas diarias (para forecasting) |
| `dm_dashboard_bi` | Vista general lista para conectar a Power BI |

### Instrucciones de ejecución (reproducibilidad)

```bash
# 1. Clonar repositorio y cambiar a rama
git clone https://github.com/roguef07/TFM_Equipo_15.git
cd TFM_Equipo_15/cloud_pipeline
git checkout Asignatura-Cloud

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Levantar entorno Docker
docker compose up -d

# 4. Ejecutar pipeline (en orden)
python scripts/00_download_kaggle.py
python scripts/01_upload_s3.py
python scripts/02_spark_transform.py
python scripts/03_load_postgres.py

# 5. Crear Data Mart en PostgreSQL
# Conectar a: localhost:5432 / retail_dw / admin / admin123
# Ejecutar: sql/datamart.sql
```

### Conexión Power BI

| Parámetro | Valor |
|---|---|
| Servidor | localhost |
| Puerto | 5432 |
| Base de datos | retail_dw |
| Usuario | admin |
| Contraseña | admin123 |

---

## Conclusiones

Este proyecto demuestra la viabilidad de una arquitectura **Data Lakehouse Cloud-Native**
aplicada al caso de uso de forecasting retail del TFM del equipo. La estrategia
**Cloud-in-Local** permite:

1. **Desarrollar sin coste cloud** durante la fase de prototipado, usando herramientas
   equivalentes (LocalStack, Docker, PySpark local).
2. **Migrar a producción con cambios mínimos**: solo requiere cambiar el endpoint de
   S3 (LocalStack → AWS S3) y la cadena de conexión de PostgreSQL (Docker → RDS).
3. **Aplicar buenas prácticas desde el inicio**: formato Parquet, separación RAW/Gold,
   Data Mart para BI, y entorno completamente reproducible con Docker.

La arquitectura AWS propuesta permite escalar el pipeline desde los ~100.000 registros
del MVP hasta millones de transacciones reales manteniendo el mismo código,
con un coste estimado de ~$19/mes para el volumen actual.
