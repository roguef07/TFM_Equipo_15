import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    coalesce,
    col,
    count,
    countDistinct,
    max,
    min,
    round,
    sum,
    to_date,
    trim,
)


BUCKET_NAME = "data-lake-crudo"

INPUT_PATH = f"s3a://{BUCKET_NAME}/raw/customer_shopping_data.csv"

OUTPUT_PATH_S3 = f"s3a://{BUCKET_NAME}/gold/customer_sales_parquet"
OUTPUT_PATH_LOCAL = "data/gold/customer_sales_parquet"


def create_spark_session():
    return (
        SparkSession.builder
        .appName("CustomerShoppingPipeline")
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566")
        .config("spark.hadoop.fs.s3a.access.key", "test")
        .config("spark.hadoop.fs.s3a.secret.key", "test")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )


def show_null_counts(df):
    df.select([
        sum(col(c).isNull().cast("int")).alias(c)
        for c in df.columns
    ]).show(truncate=False)


def main():
    os.makedirs("data/gold", exist_ok=True)

    spark = create_spark_session()

    print("Leyendo datos desde S3 Raw...")
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(INPUT_PATH)
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
    (
        df.groupBy("category")
        .count()
        .orderBy(col("count").desc())
        .show(truncate=False)
    )

    print("\nDistribución por método de pago:")
    (
        df.groupBy("payment_method")
        .count()
        .orderBy(col("count").desc())
        .show(truncate=False)
    )

    print("\nDistribución por centro comercial:")
    (
        df.groupBy("shopping_mall")
        .count()
        .orderBy(col("count").desc())
        .show(truncate=False)
    )

    print("\n--- LIMPIEZA DE DATOS ---")

    df_clean = df.dropDuplicates()

    df_clean = df_clean.dropna(subset=[
        "invoice_no",
        "customer_id",
        "category",
        "quantity",
        "price",
        "invoice_date",
        "shopping_mall",
    ])

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

    df_clean = df_clean.withColumn(
        "invoice_date",
        coalesce(
            to_date(col("invoice_date"), "dd/MM/yyyy"),
            to_date(col("invoice_date"), "d/M/yyyy"),
            to_date(col("invoice_date"), "yyyy-MM-dd"),
        )
    )

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

    print(f"Total de registros después de limpieza: {df_clean.count()}")

    print("\nVista de datos limpios:")
    df_clean.show(10, truncate=False)

    print("\n--- EDA DESPUÉS DE LIMPIEZA ---")

    print("\nVentas totales por categoría:")
    (
        df_clean.groupBy("category")
        .agg(
            round(sum("total_sales"), 2).alias("ventas_totales"),
            sum("quantity").alias("unidades_vendidas"),
            count("*").alias("cantidad_transacciones"),
        )
        .orderBy(col("ventas_totales").desc())
        .show(truncate=False)
    )

    print("\nVentas totales por centro comercial:")
    (
        df_clean.groupBy("shopping_mall")
        .agg(
            round(sum("total_sales"), 2).alias("ventas_totales"),
            count("*").alias("cantidad_transacciones"),
        )
        .orderBy(col("ventas_totales").desc())
        .show(truncate=False)
    )

    print("\nVentas por método de pago:")
    (
        df_clean.groupBy("payment_method")
        .agg(
            round(sum("total_sales"), 2).alias("ventas_totales"),
            count("*").alias("cantidad_transacciones"),
        )
        .orderBy(col("ventas_totales").desc())
        .show(truncate=False)
    )

    print("\nIndicadores generales:")
    df_clean.agg(
        count("*").alias("total_transacciones"),
        countDistinct("customer_id").alias("clientes_unicos"),
        round(sum("total_sales"), 2).alias("ventas_totales"),
        round(avg("total_sales"), 2).alias("ticket_promedio"),
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
        .orderBy("invoice_date", "category", "shopping_mall")
    )

    print("\nVista de la capa Gold:")
    df_gold.show(20, truncate=False)

    print("Guardando capa Gold en S3 LocalStack en formato Parquet...")
    (
        df_gold.write
        .mode("overwrite")
        .parquet(OUTPUT_PATH_S3)
    )

    print("Guardando copia local de capa Gold en formato Parquet...")
    (
        df_gold.write
        .mode("overwrite")
        .parquet(OUTPUT_PATH_LOCAL)
    )

    print("Proceso finalizado correctamente.")
    print(f"Capa Gold en S3: {OUTPUT_PATH_S3}")
    print(f"Copia local: {OUTPUT_PATH_LOCAL}")

    spark.stop()


if __name__ == "__main__":
    main()
