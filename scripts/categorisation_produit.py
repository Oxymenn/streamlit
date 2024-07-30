import streamlit as st
import pandas as pd
import re
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def remove_html_tags(text):
    if not isinstance(text, str):
        return ''
    return BeautifulSoup(text, "html.parser").get_text()

def find_similarities(text1, text2):
    vectorizer = CountVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    cosine_matrix = cosine_similarity(vectors)
    return cosine_matrix[0][1]

def app():
    st.title('Application de Catégorisation de Produits')
    uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])

    if uploaded_file is not None:
        # Lire le fichier Excel et afficher les noms des feuilles
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names

        st.write("Feuilles disponibles :", sheet_names)

        # Sélection de la feuille principale et secondaire
        primary_sheet = st.selectbox("Sélectionnez la feuille principale", sheet_names)
        secondary_sheet = st.selectbox("Sélectionnez la feuille secondaire", sheet_names)

        if primary_sheet and secondary_sheet:
            df_primary = pd.read_excel(xls, sheet_name=primary_sheet)
            df_secondary = pd.read_excel(xls, sheet_name=secondary_sheet)

            st.write("Aperçu des données de la feuille principale :", df_primary.head())
            st.write("Aperçu des données de la feuille secondaire :", df_secondary.head())

            # Sélection des colonnes
            product_title_col = st.selectbox("Sélectionnez la colonne pour le titre du produit", df_primary.columns)
            product_desc_col = st.selectbox("Sélectionnez la colonne pour la description du produit", df_primary.columns)
            collection_name_col = st.selectbox("Sélectionnez la colonne pour le nom de collection", df_secondary.columns)
            
            if st.button("Catégoriser les produits"):
                df_primary['Catégorisation'] = ''

                # Obtenir les noms de collections tels quels
                collections = df_secondary[collection_name_col].dropna().tolist()

                # Nettoyer la colonne de description
                df_primary[product_desc_col] = df_primary[product_desc_col].apply(remove_html_tags)

                for i, row in df_primary.iterrows():
                    title = row[product_title_col]
                    description = row[product_desc_col]
                    combined_text = title + " " + description

                    matched_collections = []
                    for collection in collections:
                        similarity_title = find_similarities(title, collection)
                        similarity_description = find_similarities(description, collection)
                        if similarity_title > 0.1 or similarity_description > 0.1:  # Seuil de similarité (ajustable)
                            matched_collections.append(collection)
                    
                    if matched_collections:
                        df_primary.at[i, 'Catégorisation'] = ', '.join(matched_collections)
                
                # S'assurer que chaque collection est associée au moins une fois
                for collection in collections:
                    if collection not in df_primary['Catégorisation'].str.cat(sep=', '):
                        st.warning(f"La collection '{collection}' n'a pas été associée à un produit.")
                
                st.write("Données après catégorisation :", df_primary.head())
                
                @st.cache
                def convert_df(df):
                    return df.to_csv(index=False).encode('utf-8')
                
                csv = convert_df(df_primary)
                
                st.download_button(
                    label="Télécharger les données avec catégorisation",
                    data=csv,
                    file_name='produits_categorises.csv',
                    mime='text/csv',
                )

# Assurez-vous d'installer les packages nécessaires :
# pip install streamlit pandas scikit-learn beautifulsoup4 openpyxl
