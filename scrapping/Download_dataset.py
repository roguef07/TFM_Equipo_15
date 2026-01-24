#hay que instalar kaggle datasets list en la terminal

from kaggle.api.kaggle_api_extended import KaggleApi

# Inicializar la API
api = KaggleApi()
api.authenticate()

# Descargar dataset (ejemplo Olist)
api.dataset_download_files("olistbr/brazilian-ecommerce",path="SCRAPPING/data/",unzip=True)

