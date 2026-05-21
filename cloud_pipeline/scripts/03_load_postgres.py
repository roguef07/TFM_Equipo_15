import os

import pandas as pd
from sqlalchemy import create_engine, text


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


def read_gold_parquet():
    if not os.path.exists(PARQUET_DIR):
        raise FileNotFoundError(
            f"No se encontró la carpeta {PARQUET_DIR}. "
            "Ejecuta primero scripts/02_spark_transform.py"
        )

    print("Leyendo capa Gold desde archivos Parquet locales...")
    df = pd.read_parquet(PARQUET_DIR)

    print(f"Registros leídos: {len(df)}")
    print("Columnas disponibles:")
    print(df.columns.tolist())

    return df


def validate_dataframe(df):
    required_columns = [
        "invoice_date",
        "category",
        "shopping_mall",
        "ventas_totales",
        "unidades_vendidas",
        "cantidad_transacciones",
        "ticket_promedio",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Faltan columnas obligatorias en la capa Gold: {missing_columns}"
        )

    if df.empty:
        raise ValueError("La capa Gold está vacía. No hay datos para cargar.")

    print("Validación de datos completada correctamente.")


def load_to_postgres(df, engine):
    print(f"Cargando datos en PostgreSQL, tabla: {TABLE_NAME}")

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False,
    )

    print("Carga finalizada correctamente en PostgreSQL.")


def create_bi_view(engine):
    print("Creando vista resumen_ventas_bi para consumo en Power BI...")

    create_view_sql = """
    CREATE OR REPLACE VIEW resumen_ventas_bi AS
    SELECT
        category,
        shopping_mall,
        SUM(ventas_totales) AS ventas_totales,
        SUM(unidades_vendidas) AS unidades_vendidas,
        SUM(cantidad_transacciones) AS cantidad_transacciones,
        ROUND(AVG(ticket_promedio)::numeric, 2) AS ticket_promedio
    FROM fact_sales_gold
    GROUP BY
        category,
        shopping_mall;
    """

    with engine.begin() as connection:
        connection.execute(text(create_view_sql))

    print("Vista resumen_ventas_bi creada correctamente.")


def main():
    engine = create_postgres_engine()

    df_gold = read_gold_parquet()
    validate_dataframe(df_gold)
    load_to_postgres(df_gold, engine)
    create_bi_view(engine)

    print("Proceso completo finalizado correctamente.")


if __name__ == "__main__":
    main()
