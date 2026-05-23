import os

import boto3
import pandas as pd
from sqlalchemy import create_engine


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BUCKET_NAME = "data-lake-crudo"
S3_GOLD_KEY = "gold/customer_sales_parquet/customer_sales_gold.parquet"

PARQUET_DIR = os.path.join(BASE_DIR, "data", "gold", "customer_sales_parquet")
PARQUET_FILE = os.path.join(PARQUET_DIR, "customer_sales_gold.parquet")

POSTGRES_USER = os.environ.get("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "admin123")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "retail_dw")

TABLE_NAME = "customer_sales_gold"


def create_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localhost:5500"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        region_name="us-east-1",
    )


def download_gold_from_s3(s3_client):
    os.makedirs(PARQUET_DIR, exist_ok=True)

    print("Descargando Parquet Gold desde LocalStack S3...")

    try:
        s3_client.download_file(BUCKET_NAME, S3_GOLD_KEY, PARQUET_FILE)
    except Exception as e:
        raise RuntimeError(
            f"Fallo al descargar el Parquet Gold desde S3. "
            f"¿Está LocalStack activo y se ejecutó 02_spark_transform.py? "
            f"Error original: {e}"
        )

    print(f"Parquet descargado en: {PARQUET_FILE}")


def create_connection():
    connection_string = (
        f"postgresql+psycopg2://"
        f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    return create_engine(connection_string)


def read_gold_parquet():
    print("Leyendo archivo Parquet Gold...")
    df = pd.read_parquet(PARQUET_FILE)
    print(f"Total registros cargados: {len(df)}")
    return df


def load_to_postgres(df, engine):
    print("Cargando datos a PostgreSQL...")

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False,
    )

    print(f"Tabla '{TABLE_NAME}' cargada correctamente.")


def main():
    print("\n--- INICIO CARGA DATA WAREHOUSE ---\n")

    s3_client = create_s3_client()
    download_gold_from_s3(s3_client)

    df_gold = read_gold_parquet()

    engine = create_connection()
    load_to_postgres(df_gold, engine)
    engine.dispose()

    print("\nProceso ETL completado correctamente.")
    print("Datos disponibles en PostgreSQL.")

    print("\nConexión Power BI:")
    print(f"Servidor: {POSTGRES_HOST}")
    print(f"Puerto: {POSTGRES_PORT}")
    print(f"Base de datos: {POSTGRES_DB}")
    print(f"Usuario: {POSTGRES_USER}")


if __name__ == "__main__":
    main()
