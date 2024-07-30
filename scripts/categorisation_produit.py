import streamlit as st
import pandas as pd
import numpy as np
import re
import unicodedata
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

# Charger les stopwords français
with open('stopwords_fr.txt', 'r', encoding='utf-8') as f:
    stopwords_fr = set(f.read().splitlines())

# Initialiser le stemmer français
stemmer = SnowballStemmer("french")

def clean_text(text):
    if not isinstance(text, str):
        text = ''
    text = text.lower()  # Convertir en minuscule
    text = re.sub(r'<.*?>', '', text)  # Supprimer le format HTML
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')  # Supprimer les accents
    text = re.sub(r'[^\w\s]', '', text)  # Supprimer la ponctuation
    text = re.sub(r'\d+', '', text)  # Supprimer les chiffres
    words = text.split()
    words = [word for word in words if word not in stopwords_fr]  # Supprimer les stopwords
    words = [stemmer.stem(word) for word in words]  # Mettre au singulier (stemmer)
    text = ' '.join(words)
    return text

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

                # Nettoyer les noms de collection une fois pour toutes
                collections = df_secondary[collection_name_col].dropna().apply(clean_text).tolist()

                for i, row in df_primary.iterrows():
                    title = clean_text(row[product_title_col])
                    description = clean_text(row[product_desc_col])
                    combined_text = title + " " + description

                    max_similarity = 0
                    best_match = ''
                    for collection in collections:
                        similarity = find_similarities(combined_text, collection)
                        if similarity > max_similarity:
                            max_similarity = similarity
                            best_match = collection
                    
                    if max_similarity > 0.1:  # Seuil de similarité (ajustable)
                        df_primary.at[i, 'Catégorisation'] = best_match
                
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
# pip install streamlit pandas numpy scikit-learn beautifulsoup4 nltk openpyxl
# Pour télécharger les stopwords français : nltk.download('stopwords')
