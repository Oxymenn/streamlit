import streamlit as st
import pandas as pd
import requests
import json
import math

def app():
    st.title("Importation de produits WooCommerce via WordPress REST API")

    # Configuration
    url = st.secrets["wordpress"]["url"]
    username = st.secrets["wordpress"]["username"]
    password = st.secrets["wordpress"]["password"]

    def clean_data(value):
        if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
            return None
        elif isinstance(value, float) and math.isinf(value):
            return str(value)
        return value

    def create_or_update_product(product_data):
        endpoint = f"{url}/wp-json/wc/v3/products"  # Notez l'utilisation de wc/v3 pour WooCommerce
        auth = (username, password)
        headers = {"Content-Type": "application/json"}

        # Vérifier si le produit existe déjà
        if 'id' in product_data:
            existing_product = requests.get(f"{endpoint}/{product_data['id']}", auth=auth)
            if existing_product.status_code == 200:
                # Mise à jour du produit existant
                response = requests.put(f"{endpoint}/{product_data['id']}", auth=auth, headers=headers, data=json.dumps(product_data))
            else:
                # Création d'un nouveau produit
                response = requests.post(endpoint, auth=auth, headers=headers, data=json.dumps(product_data))
        else:
            # Création d'un nouveau produit
            response = requests.post(endpoint, auth=auth, headers=headers, data=json.dumps(product_data))

        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, response.text

    def import_products(df, num_products, column_mapping):
        for index, row in df.head(num_products).iterrows():
            product_data = {}
            
            for woo_field, csv_field in column_mapping.items():
                if csv_field and csv_field in df.columns:
                    value = clean_data(row[csv_field])
                    if value is not None:
                        if woo_field == 'categories':
                            # Assurez-vous que les catégories sont au format attendu par WooCommerce
                            product_data[woo_field] = [{"id": int(cat_id)} for cat_id in str(value).split(',') if cat_id.isdigit()]
                        elif woo_field == 'images':
                            product_data[woo_field] = [{"src": img_url} for img_url in str(value).split(',') if img_url]
                        else:
                            product_data[woo_field] = value

            success, result = create_or_update_product(product_data)
            if success:
                st.write(f"Produit {'mis à jour' if 'id' in product_data else 'créé'} avec succès : {product_data.get('name', 'Sans nom')}")
            else:
                st.error(f"Erreur lors de l'importation/mise à jour du produit : {result}")
                st.error(f"Données du produit : {json.dumps(product_data, ensure_ascii=False, indent=2)}")

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Aperçu des données :")
        st.write(df.head())
        
        st.write("Associez les colonnes de votre CSV aux champs WooCommerce :")
        
        woo_fields = ['id', 'sku', 'type', 'name', 'short_description', 'description', 'categories', 'images', 'regular_price']
        column_options = [''] + df.columns.tolist()
        column_mapping = {}
        
        for field in woo_fields:
            column_mapping[field] = st.selectbox(f"Champ WooCommerce '{field}'", column_options)

        num_products = st.number_input("Nombre de produits à importer/mettre à jour", min_value=1, max_value=len(df), value=1)

        if st.button("Importer/Mettre à jour les produits"):
            import_products(df, num_products, column_mapping)
            st.success(f"{num_products} produits ont été traités !")

            # Supprimer les lignes traitées et créer un nouveau CSV
            df_remaining = df.iloc[num_products:]
            csv_remaining = df_remaining.to_csv(index=False)
            st.download_button(
                label="Télécharger le fichier CSV mis à jour",
                data=csv_remaining,
                file_name="produits_restants.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    app()
