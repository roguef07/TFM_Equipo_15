import os

import boto3
from botocore.exceptions import ClientError


BUCKET_NAME = "data-lake-crudo"
CSV_FILE = "customer_shopping_data.csv"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOCAL_FILE_PATH = os.path.join(DATA_DIR, CSV_FILE)
S3_KEY = f"raw/{CSV_FILE}"


def create_s3_client():
    """Crea cliente boto3 apuntando a LocalStack S3."""
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localhost:5500"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        region_name="us-east-1",
    )


def create_bucket_if_not_exists(s3_client):
    """Crea el bucket S3 si no existe; no falla si ya existe."""
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print(f"El bucket '{BUCKET_NAME}' ya existe.")
    except ClientError:
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        print(f"Bucket creado: {BUCKET_NAME}")


def upload_file_to_s3(s3_client):
    """Sube el CSV crudo a s3://data-lake-crudo/raw/."""
    if not os.path.exists(LOCAL_FILE_PATH):
        raise FileNotFoundError(
            f"No se encontró el archivo {LOCAL_FILE_PATH}. "
            "Ejecuta primero scripts/00_download_kaggle.py"
        )

    s3_client.upload_file(
        LOCAL_FILE_PATH,
        BUCKET_NAME,
        S3_KEY,
    )

    print(f"Archivo subido correctamente a s3://{BUCKET_NAME}/{S3_KEY}")


def main():
    """Crea bucket y sube el CSV de ventas a LocalStack S3 (capa Raw)."""
    s3_client = create_s3_client()
    create_bucket_if_not_exists(s3_client)
    upload_file_to_s3(s3_client)


if __name__ == "__main__":
    main()

