import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import json
import math

def app():
    st.title("Importation et mise à jour de produits WooCommerce")

    # Configuration de l'API WooCommerce
    url = st.secrets["woocommerce"]["url"]
    consumer_key = st.secrets["woocommerce"]["consumer_key"]
    consumer_secret = st.secrets["woocommerce"]["consumer_secret"]
    
    def clean_data(value):
        if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
            return None
        elif isinstance(value, float) and math.isinf(value):
            return str(value)
        return value

    def import_or_update_products(df, num_products, column_mapping):
        for index, row in df.head(num_products).iterrows():
            product_data = {}
            
            for woo_field, csv_field in column_mapping.items():
                if csv_field and csv_field in df.columns:
                    value = clean_data(row[csv_field])
                    if value is not None:
                        if woo_field == 'categories':
                            product_data[woo_field] = [{"id": cat_id} for cat_id in str(value).split(',') if cat_id]
                        elif woo_field == 'images':
                            product_data[woo_field] = [{"src": img_url} for img_url in str(value).split(',') if img_url]
                        elif woo_field in ['regular_price', 'id']:
                            product_data[woo_field] = str(value)
                        else:
                            product_data[woo_field] = value
            
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
            
            try:
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
                st.write(f"Produit {'mis à jour' if existing_product else 'créé'} avec succès : {product_data.get('name', 'Sans nom')}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur lors de l'importation/mise à jour du produit : {e}")
                st.error(f"Données du produit : {json.dumps(product_data, ensure_ascii=False, indent=2)}")

    # Le reste du code reste inchangé...
