import os
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi


DATASET = "mehmettahiraslan/customer-shopping-dataset"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ZIP_FILE = os.path.join(DATA_DIR, "customer-shopping-dataset.zip")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("Autenticando con Kaggle...")
    api = KaggleApi()
    api.authenticate()

    print("Descargando dataset desde Kaggle...")
    api.dataset_download_files(
        DATASET,
        path=DATA_DIR,
        unzip=False,
    )

    print("Descomprimiendo archivo...")
    with zipfile.ZipFile(ZIP_FILE, "r") as zip_ref:
        zip_ref.extractall(DATA_DIR)

    print(f"Dataset descargado correctamente en: {DATA_DIR}")


if __name__ == "__main__":
    main()
