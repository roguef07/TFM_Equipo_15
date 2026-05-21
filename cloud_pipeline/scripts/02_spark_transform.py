import os
import shutil

import boto3
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    count,
    max,
    min,
    make_date,
    regexp_extract,
    round,
    sum,
    trim,
    when,
)

BUCKET_NAME = "data-lake-crudo"
CSV_FILE = "customer_shopping_data.csv"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
GOLD_DIR = os.path.join(BASE_DIR, "data", "gold", "customer_sales_parquet")

LOCAL_RAW_FILE = os.path.join(RAW_DIR, CSV_FILE)
S3_RAW_KEY = f"raw/{CSV_FILE}"
S3_GOLD_PREFIX = "gold/customer_sales_parquet"


def create_s3_client():
    return boto3.client(
        "s3",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )


def download_raw_from_s3(s3_client):
    os.makedirs(RAW_DIR, exist_ok=True)

    print("Descargando CSV crudo desde LocalStack S3...")

    s3_client.download_file(
        BUCKET_NAME,
        S3_RAW_KEY,
        LOCAL_RAW_FILE
    )

    print(f"CSV descargado en: {LOCAL_RAW_FILE}")


def upload_gold_to_s3(s3_client):
    print("Subiendo capa Gold Parquet a LocalStack S3...")

    for root, _, files in os.walk(GOLD_DIR):
        for file in files:
            local_path = os.path.join(root, file)

            relative_path = os.path.relpath(
                local_path,
                GOLD_DIR
            ).replace("\\", "/")

            s3_key = f"{S3_GOLD_PREFIX}/{relative_path}"

            s3_client.upload_file(
                local_path,
                BUCKET_NAME,
                s3_key
            )

    print(
        f"Capa Gold subida a s3://{BUCKET_NAME}/{S3_GOLD_PREFIX}/"
    )


def create_spark_session():
    return (
        SparkSession.builder
        .appName("CustomerShoppingPipeline")
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
        .getOrCreate()
    )


def show_null_counts(df):
    df.select([
        sum(col(c).isNull().cast("int")).alias(c)
        for c in df.columns
    ]).show(truncate=False)


def parse_invoice_date(df):
    df = (
        df
        .withColumn(
            "date_part_1",
            regexp_extract(col("invoice_date"), r"^(\d{1,2})/", 1).cast("int")
        )
        .withColumn(
            "date_part_2",
            regexp_extract(col("invoice_date"), r"^\d{1,2}/(\d{1,2})/", 1).cast("int")
        )
        .withColumn(
            "date_year",
            regexp_extract(col("invoice_date"), r"(\d{4})$", 1).cast("int")
        )
    )

    df = df.withColumn(
        "invoice_date",
        when(
            col("date_part_1") > 12,
            make_date(col("date_year"), col("date_part_2"), col("date_part_1"))
        )
        .when(
            col("date_part_2") > 12,
            make_date(col("date_year"), col("date_part_1"), col("date_part_2"))
        )
        .otherwise(
            make_date(col("date_year"), col("date_part_2"), col("date_part_1"))
        )
    )

    return df.drop("date_part_1", "date_part_2", "date_year")


def main():
    s3_client = create_s3_client()
    download_raw_from_s3(s3_client)

    spark = create_spark_session()

    print("Leyendo datos con Spark...")

    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(LOCAL_RAW_FILE)
    )

    print("\n--- EDA INICIAL ---")

    total_rows = df.count()

    print(f"Total de registros iniciales: {total_rows}")
    print(f"Total de columnas: {len(df.columns)}")

    print("\nEsquema del dataset:")
    df.printSchema()

    print("\nPrimeras filas:")
    df.show(10, truncate=False)

    print("\nConteo de valores nulos por columna:")
    show_null_counts(df)

    duplicated_rows = total_rows - df.dropDuplicates().count()
    print(f"\nFilas duplicadas encontradas: {duplicated_rows}")

    print("\nResumen estadístico de variables numéricas:")
    df.describe(["age", "quantity", "price"]).show()

    print("\nDistribución por categoría:")
    df.groupBy("category").count().orderBy(col("count").desc()).show(truncate=False)

    print("\nDistribución por método de pago:")
    df.groupBy("payment_method").count().orderBy(col("count").desc()).show(truncate=False)

    print("\nDistribución por centro comercial:")
    df.groupBy("shopping_mall").count().orderBy(col("count").desc()).show(truncate=False)

    print("\n--- LIMPIEZA DE DATOS ---")

    df_clean = df.dropDuplicates()

    df_clean = df_clean.dropna(
        subset=[
            "invoice_no",
            "customer_id",
            "category",
            "quantity",
            "price",
            "invoice_date",
            "shopping_mall",
        ]
    )

    df_clean = (
        df_clean
        .withColumn("invoice_no", trim(col("invoice_no")))
        .withColumn("customer_id", trim(col("customer_id")))
        .withColumn("gender", trim(col("gender")))
        .withColumn("category", trim(col("category")))
        .withColumn("payment_method", trim(col("payment_method")))
        .withColumn("shopping_mall", trim(col("shopping_mall")))
        .withColumn("age", col("age").cast("int"))
        .withColumn("quantity", col("quantity").cast("int"))
        .withColumn("price", col("price").cast("double"))
    )

    df_clean = parse_invoice_date(df_clean)

    df_clean = df_clean.filter(
        (col("invoice_date").isNotNull())
        & (col("quantity") > 0)
        & (col("price") > 0)
        & (col("age").between(0, 120))
    )

    df_clean = df_clean.withColumn(
        "total_sales",
        round(col("quantity") * col("price"), 2)
    )

    print(
        f"Total de registros después de limpieza: {df_clean.count()}"
    )

    print("\n--- EDA DESPUÉS DE LIMPIEZA ---")

    print("\nIndicadores generales:")
    df_clean.agg(
        count("*").alias("total_transacciones"),
        round(sum("total_sales"), 2).alias("ventas_totales"),
        round(avg("total_sales"), 2).alias("ticket_promedio"),
    ).show(truncate=False)

    print("\nRango de fechas:")
    df_clean.agg(
        min("invoice_date").alias("fecha_minima"),
        max("invoice_date").alias("fecha_maxima"),
    ).show(truncate=False)

    print("\n--- TRANSFORMACIÓN CAPA GOLD ---")

    df_gold = (
        df_clean.groupBy(
            "invoice_date",
            "category",
            "shopping_mall",
        )
        .agg(
            round(sum("total_sales"), 2).alias("ventas_totales"),
            sum("quantity").alias("unidades_vendidas"),
            count("*").alias("cantidad_transacciones"),
            round(avg("total_sales"), 2).alias("ticket_promedio"),
        )
        .orderBy(
            "invoice_date",
            "category",
            "shopping_mall"
        )
    )

    df_gold.show(20, truncate=False)

    print("Guardando capa Gold local en formato Parquet...")

    if os.path.exists(GOLD_DIR):
        shutil.rmtree(GOLD_DIR)

    os.makedirs(GOLD_DIR, exist_ok=True)

    gold_file_path = os.path.join(
        GOLD_DIR,
        "customer_sales_gold.parquet"
    )

    df_gold.toPandas().to_parquet(
        gold_file_path,
        index=False
    )

    upload_gold_to_s3(s3_client)

    print("Proceso finalizado correctamente.")
    print(f"Capa Gold local: {gold_file_path}")

    spark.stop()


if __name__ == "__main__":
    main()
