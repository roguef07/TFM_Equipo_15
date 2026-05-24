import io
import os
import shutil

import boto3
import pandas as pd
import psycopg2


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BUCKET_NAME = "data-lake-crudo"
S3_GOLD_PREFIX = "gold/customer_sales_parquet/"

PARQUET_DIR = os.path.join(BASE_DIR, "data", "gold", "customer_sales_parquet")

POSTGRES_USER = os.environ.get("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "admin123")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "retail_dw")

TABLE_NAME = "customer_sales_gold"


def create_s3_client():
    """Crea cliente boto3 apuntando a LocalStack S3."""
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localhost:5500"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        region_name="us-east-1",
    )


def download_gold_from_s3(s3_client):
    """Descarga los Parquet Gold desde LocalStack S3; limpia el directorio local antes."""
    if os.path.exists(PARQUET_DIR):
        shutil.rmtree(PARQUET_DIR)
    os.makedirs(PARQUET_DIR)

    print("Descargando Parquet Gold desde LocalStack S3...")

    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_GOLD_PREFIX)
        objects = [o for o in response.get("Contents", []) if o["Key"].endswith(".parquet")]
        if not objects:
            raise ValueError("No se encontraron archivos Parquet en S3.")
        for obj in objects:
            filename = os.path.basename(obj["Key"])
            s3_client.download_file(BUCKET_NAME, obj["Key"], os.path.join(PARQUET_DIR, filename))
    except Exception as e:
        raise RuntimeError(
            f"Fallo al descargar el Parquet Gold desde S3. "
            f"¿Está LocalStack activo y se ejecutó 02_spark_transform.py? "
            f"Error original: {e}"
        )

    print(f"Parquet descargado en: {PARQUET_DIR}")


def read_gold_parquet():
    print("Leyendo archivo Parquet Gold...")
    df = pd.read_parquet(PARQUET_DIR)
    print(f"Total registros cargados: {len(df)}")
    return df


def load_to_postgres(df):
    """Reemplaza la tabla customer_sales_gold usando psycopg2 COPY para máxima eficiencia."""
    print("Cargando datos a PostgreSQL...")

    _TYPE_MAP = {
        "object": "TEXT",
        "int32": "INTEGER",
        "int64": "BIGINT",
        "float32": "FLOAT",
        "float64": "FLOAT",
        "bool": "BOOLEAN",
        "datetime64[ns]": "DATE",
        "dbdate": "DATE",
    }

    cols_def = []
    for col_name, dtype in df.dtypes.items():
        pg_type = _TYPE_MAP.get(str(dtype), "TEXT")
        cols_def.append(f'"{col_name}" {pg_type}')

    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{TABLE_NAME}" CASCADE')
            cur.execute(f'CREATE TABLE "{TABLE_NAME}" ({", ".join(cols_def)})')

            buf = io.StringIO()
            df.to_csv(buf, index=False, header=False, na_rep="")
            buf.seek(0)
            cur.copy_expert(
                f'COPY "{TABLE_NAME}" FROM STDIN WITH (FORMAT CSV, NULL \'\')',
                buf,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f"Tabla '{TABLE_NAME}' cargada correctamente.")


def recreate_views():
    """Recrea las vistas del datamart desde sql/datamart.sql (idempotente con CREATE OR REPLACE)."""
    sql_file = os.path.join(BASE_DIR, "sql", "datamart.sql")
    with open(sql_file) as f:
        sql = f.read()
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.close()
    print("Vistas del datamart recreadas correctamente.")


def main():
    print("\n--- INICIO CARGA DATA WAREHOUSE ---\n")

    s3_client = create_s3_client()
    download_gold_from_s3(s3_client)

    df_gold = read_gold_parquet()

    load_to_postgres(df_gold)
    recreate_views()

    print("\nProceso ETL completado correctamente.")
    print("Datos disponibles en PostgreSQL.")

    print("\nConexión Power BI:")
    print(f"Servidor: {POSTGRES_HOST}")
    print(f"Puerto: {POSTGRES_PORT}")
    print(f"Base de datos: {POSTGRES_DB}")
    print(f"Usuario: {POSTGRES_USER}")


if __name__ == "__main__":
    main()
