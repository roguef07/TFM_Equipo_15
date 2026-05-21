import os

import pandas as pd
from sqlalchemy import create_engine


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PARQUET_DIR = os.path.join(
    BASE_DIR,
    "data",
    "gold",
    "customer_sales_parquet"
)

PARQUET_FILE = os.path.join(
    PARQUET_DIR,
    "customer_sales_gold.parquet"
)

POSTGRES_USER = "admin"
POSTGRES_PASSWORD = "admin123"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "retail_dw"

TABLE_NAME = "customer_sales_gold"


def create_connection():
    connection_string = (
        f"postgresql+psycopg2://"
        f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    engine = create_engine(connection_string)

    return engine


def read_gold_parquet():
    if not os.path.exists(PARQUET_FILE):
        raise FileNotFoundError(
            f"No se encontró el archivo:\n{PARQUET_FILE}\n"
            "Ejecuta primero scripts/02_spark_transform.py"
        )

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
        index=False
    )

    print(
        f"Tabla '{TABLE_NAME}' cargada correctamente."
    )


def show_summary(df):
    print("\n--- RESUMEN DATA WAREHOUSE ---")

    print("\nColumnas:")
    print(df.columns.tolist())

    print("\nPrimeras filas:")
    print(df.head())

    print("\nResumen estadístico:")
    print(df.describe(include="all"))


def main():
    print("\n--- INICIO CARGA DATA WAREHOUSE ---\n")

    df_gold = read_gold_parquet()

    engine = create_connection()

    load_to_postgres(df_gold, engine)

    show_summary(df_gold)

    print("\nProceso ETL completado correctamente.")
    print("Datos disponibles en PostgreSQL.")

    print("\nConexión Power BI:")
    print(f"Servidor: localhost")
    print(f"Puerto: {POSTGRES_PORT}")
    print(f"Base de datos: {POSTGRES_DB}")
    print(f"Usuario: {POSTGRES_USER}")


if __name__ == "__main__":
    main()
