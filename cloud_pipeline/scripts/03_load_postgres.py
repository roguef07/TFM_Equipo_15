import os

import pandas as pd
from sqlalchemy import create_engine


PARQUET_DIR = "data/gold/customer_sales_parquet"

POSTGRES_USER = "admin"
POSTGRES_PASSWORD = "admin123"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "retail_dw"

TABLE_NAME = "fact_sales_gold"


def create_postgres_engine():
    connection_url = (
        f"postgresql+psycopg2://{POSTGRES_USER}:"
        f"{POSTGRES_PASSWORD}@{POSTGRES_HOST}:"
        f"{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    return create_engine(connection_url)


def read_parquet_files():
    if not os.path.exists(PARQUET_DIR):
        raise FileNotFoundError(
            f"No se encontró la carpeta {PARQUET_DIR}. "
            "Ejecuta primero scripts/02_spark_transform.py"
        )

    print("Leyendo archivos Parquet de la capa Gold...")
    df = pd.read_parquet(PARQUET_DIR)

    print(f"Registros leídos: {len(df)}")
    print("Columnas disponibles:")
    print(df.columns.tolist())

    return df


def load_to_postgres(df, engine):
    print(f"Cargando datos en PostgreSQL, tabla: {TABLE_NAME}")

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False,
    )

    print("Carga finalizada correctamente en PostgreSQL.")


def main():
    engine = create_postgres_engine()
    df = read_parquet_files()
    load_to_postgres(df, engine)


if __name__ == "__main__":
    main()
