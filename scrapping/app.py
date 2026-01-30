import streamlit as st
import pandas as pd

# Título
st.title("Dataset: Brazilian E-Commerce Public Dataset by Olist")
st.markdown("Primer vistazo del dataset: ")
df = pd.read_csv("tabla_analitica_olist.csv")
st.dataframe(df.head(5))

lista_columnas = list(df.columns)

#Seleccionar un dataset
opcion = st.selectbox("Elige una variable:",lista_columnas)
df_2 = df[opcion].describe()
st.markdown("Descripción de los datos: ")
st.dataframe(df_2.head(5))