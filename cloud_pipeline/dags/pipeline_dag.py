from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator

PIPELINE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PIPELINE_DIR / "scripts"

default_args = {
    "owner": "tfm_equipo_15",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="customer_shopping_pipeline",
    description="Pipeline ETL completo: Kaggle → S3 → PySpark → PostgreSQL",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["tfm", "cloud", "etl"],
) as dag:

    download_dataset = BashOperator(
        task_id="download_dataset",
        bash_command=f"python {SCRIPTS_DIR / '00_download_kaggle.py'}",
    )

    upload_to_s3 = BashOperator(
        task_id="upload_to_s3",
        bash_command=f"python {SCRIPTS_DIR / '01_upload_s3.py'}",
    )

    spark_transform = BashOperator(
        task_id="spark_transform",
        bash_command=f"python {SCRIPTS_DIR / '02_spark_transform.py'}",
    )

    load_postgres = BashOperator(
        task_id="load_postgres",
        bash_command=f"python {SCRIPTS_DIR / '03_load_postgres.py'}",
    )

    create_datamart = BashOperator(
        task_id="create_datamart",
        bash_command=f"python {SCRIPTS_DIR / '04_create_datamart.py'}",
    )

    download_dataset >> upload_to_s3 >> spark_transform >> load_postgres >> create_datamart
