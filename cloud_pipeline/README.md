# Cloud Pipeline – Customer Shopping Data

## Descripción del Proyecto

Este proyecto implementa un pipeline de datos en la nube utilizando tecnologías de Big Data y Cloud Computing.

Se utiliza el dataset "Customer Shopping Data" obtenido desde Kaggle, el cual contiene información de compras realizadas por clientes, incluyendo categorías de productos, métodos de pago, género, ubicación y montos de compra.

El objetivo es simular una arquitectura moderna de procesamiento de datos similar a la utilizada en entornos empresariales.

---

## Arquitectura Utilizada

El pipeline implementa las siguientes etapas:

1. Ingesta de datos desde Kaggle
2. Almacenamiento en Data Lake local (LocalStack S3)
3. Procesamiento con Apache Spark
4. Persistencia en PostgreSQL
5. Orquestación y despliegue con Docker y Kubernetes
6. Visualización en Power BI

---

## Tecnologías Utilizadas

- Python
- Docker
- Kubernetes (Minikube)
- Apache Spark
- PostgreSQL
- LocalStack (S3)
- Power BI
- GitHub

---

## Dataset

Dataset utilizado:

Customer Shopping Dataset – Kaggle

Variables principales:
- invoice_no
- customer_id
- gender
- age
- category
- quantity
- price
- payment_method
- shopping_mall

---

## Objetivo General

Diseñar un pipeline de datos escalable basado en tecnologías cloud para el procesamiento y visualización de información comercial.

---
