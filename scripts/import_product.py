import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

def app():
    st.title("Importation et mise à jour de produits WooCommerce")

    # Configuration de l'API WooCommerce
    url = st.secrets["woocommerce"]["url"]
    consumer_key = st.secrets["woocommerce"]["consumer_key"]
    consumer_secret = st.secrets["woocommerce"]["consumer_secret"]
    
    def import_or_update_products(df, num_products, column_mapping):
        for index, row in df.head(num_products).iterrows():
            product_data = {}
            
            for woo_field, csv_field in column_mapping.items():
                if csv_field and csv_field in df.columns:
                    if woo_field == 'categories':
                        product_data[woo_field] = [{"id": cat_id} for cat_id in str(row[csv_field]).split(',') if cat_id]
                    elif woo_field == 'images':
                        product_data[woo_field] = [{"src": img_url} for img_url in str(row[csv_field]).split(',') if img_url]
                    elif woo_field in ['regular_price', 'id']:
                        product_data[woo_field] = str(row[csv_field])
                    else:
                        product_data[woo_field] = row[csv_field]
            
            # Vérifier si le produit existe déjà
            product_id = product_data.get('id')
            sku = product_data.get('sku')
            
            existing_product = None
            if product_id:
                response = requests.get(
                    f"{url}/wp-json/wc/v3/products/{product_id}",
                    auth=HTTPBasicAuth(consumer_key, consumer_secret)
                )
                if response.status_code == 200:
                    existing_product = response.json()
            elif sku:
                response = requests.get(
                    f"{url}/wp-json/wc/v3/products",
                    auth=HTTPBasicAuth(consumer_key, consumer_secret),
                    params={'sku': sku}
                )
                if response.status_code == 200:
                    products = response.json()
                    if products:
                        existing_product = products[0]
            
            if existing_product:
                # Mettre à jour le produit existant
                product_id = existing_product['id']
                response = requests.put(
                    f"{url}/wp-json/wc/v3/products/{product_id}",
                    auth=HTTPBasicAuth(consumer_key, consumer_secret),
                    json=product_data
                )
            else:
                # Créer un nouveau produit
                response = requests.post(
                    f"{url}/wp-json/wc/v3/products",
                    auth=HTTPBasicAuth(consumer_key, consumer_secret),
                    json=product_data
                )
            
            response.raise_for_status()

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Aperçu des données :")
        st.write(df.head())
        
        st.write("Associez les colonnes de votre CSV aux champs WooCommerce :")
        
        woo_fields = ['id', 'name', 'type', 'regular_price', 'description', 'short_description', 'categories', 'images', 'sku']
        column_options = [''] + df.columns.tolist()
        column_mapping = {}
        
        for field in woo_fields:
            column_mapping[field] = st.selectbox(f"Champ WooCommerce '{field}'", column_options)

        num_products = st.number_input("Nombre de produits à importer/mettre à jour", min_value=1, max_value=len(df), value=1)

        if st.button("Importer/Mettre à jour les produits"):
            import_or_update_products(df, num_products, column_mapping)
            st.success(f"{num_products} produits ont été importés ou mis à jour avec succès!")

            # Supprimer les lignes traitées et créer un nouveau CSV
            df_remaining = df.iloc[num_products:]
            csv_remaining = df_remaining.to_csv(index=False)
            st.download_button(
                label="Télécharger le fichier CSV mis à jour",
                data=csv_remaining,
                file_name="produits_restants.csv",
                mime="text/csv"
            )
