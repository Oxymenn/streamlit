import streamlit as st
import pandas as pd
import io
import re
from unidecode import unidecode

def slugify(text):
    text = unidecode(text).lower()
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')

def process_image_url(url, product_name, index):
    base_url = url.rsplit('/', 1)[0] + '/'
    extension = url.split('.')[-1]
    new_name = slugify(product_name)
    if index > 0:
        new_name += f"-{index + 1}"
    return f"{base_url}{new_name}.{extension}"

def limit_and_rename_images(row, image_column, name_column, max_images=5):
    urls = row[image_column].split(', ')
    product_name = row[name_column]
    new_urls = [process_image_url(url, product_name, i) for i, url in enumerate(urls[:max_images])]
    return ', '.join(new_urls)

def process_csv(df, image_column, name_column):
    df['processed_images'] = df.apply(lambda row: limit_and_rename_images(row, image_column, name_column), axis=1)
    return df

st.title('Traitement d\'images pour CSV de produits')

uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Aperçu des données originales :")
    st.write(df.head())

    columns = df.columns.tolist()
    image_column = st.selectbox("Sélectionnez la colonne contenant les URLs des images", columns)
    name_column = st.selectbox("Sélectionnez la colonne contenant les noms des produits", columns)

    if st.button('Traiter le CSV'):
        processed_df = process_csv(df, image_column, name_column)
        st.write("Aperçu des données traitées :")
        st.write(processed_df.head())

        # Création d'un buffer en mémoire pour stocker le CSV
        csv_buffer = io.StringIO()
        processed_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # Bouton de téléchargement
        st.download_button(
            label="Télécharger le CSV traité",
            data=csv_buffer,
            file_name="produits_images_traitees.csv",
            mime="text/csv"
        )

st.write("Note : Ce script limitera le nombre d'images à 5 pour chaque produit et renommera les images selon le nom du produit.")
