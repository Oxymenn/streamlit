import streamlit as st
import pandas as pd
import csv
from woocommerce import API

# Configuration de l'API WooCommerce en utilisant les secrets de Streamlit
wcapi = API(
    url=st.secrets["woocommerce"]["url"],
    consumer_key=st.secrets["woocommerce"]["consumer_key"],
    consumer_secret=st.secrets["woocommerce"]["consumer_secret"],
    version="wc/v3"
)

def import_products(df, num_products):
    for index, row in df.head(num_products).iterrows():
        product_data = {
            "name": row['Nom'],
            "type": row['Type'],
            "regular_price": str(row['Prix régulier']),
            "description": row['Description'],
            "short_description": row['Description courte'],
            "categories": [{"id": cat_id} for cat_id in str(row['Catégories']).split(',')],
            "images": [{"src": img_url} for img_url in str(row['Images']).split(',')],
            "sku": row['UGS']
        }
        wcapi.post("products", product_data).json()

st.title("Importation de produits WooCommerce")

uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write(df)

    num_products = st.number_input("Nombre de produits à importer", min_value=1, max_value=len(df), value=1)

    if st.button("Importer les produits"):
        import_products(df, num_products)
        st.success(f"{num_products} produits ont été importés avec succès!")

        # Supprimer les lignes importées et créer un nouveau CSV
        df_remaining = df.iloc[num_products:]
        csv_remaining = df_remaining.to_csv(index=False)
        st.download_button(
            label="Télécharger le fichier CSV mis à jour",
            data=csv_remaining,
            file_name="produits_restants.csv",
            mime="text/csv"
        )
