import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import traceback

# Téléchargement des ressources NLTK nécessaires
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

download_nltk_resources()

# Fonction pour prétraiter le texte
def preprocess_text(text):
    if isinstance(text, str):
        # Conversion en minuscules
        text = text.lower()
        # Suppression des caractères spéciaux
        text = re.sub(r'[^\w\s]', '', text)
        # Tokenization
        tokens = word_tokenize(text)
        # Suppression des stop words
        stop_words = set(stopwords.words('french'))
        tokens = [word for word in tokens if word not in stop_words]
        return ' '.join(tokens)
    return ''

# Fonction pour charger et traiter le fichier
def load_and_process_file(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            st.error("Format de fichier non pris en charge. Veuillez utiliser un fichier CSV ou Excel.")
            return None
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {str(e)}")
        return None

# Fonction pour analyser et catégoriser les produits
def categorize_products(df, title_col, desc_col, collection_col):
    try:
        df['combined_text'] = df[title_col].fillna('') + ' ' + df[desc_col].fillna('')
        df['processed_text'] = df['combined_text'].apply(preprocess_text)
        df['processed_collection'] = df[collection_col].fillna('').apply(preprocess_text)
        
        tfidf = TfidfVectorizer()
        tfidf_matrix = tfidf.fit_transform(df['processed_text'])
        
        collections = df['processed_collection'].unique()
        collection_matrix = tfidf.transform(collections)
        
        similarity_matrix = cosine_similarity(tfidf_matrix, collection_matrix)
        
        threshold = 0.1  # Seuil de similarité, à ajuster selon vos besoins
        categorization = []
        
        for i, row in enumerate(similarity_matrix):
            categories = [collections[j] for j, sim in enumerate(row) if sim > threshold]
            categorization.append(', '.join(categories) if categories else 'Non catégorisé')
        
        df['Catégorisation'] = categorization
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la catégorisation: {str(e)}")
        return None

# Interface utilisateur Streamlit
try:
    st.title("Catégorisation de Produits E-commerce")

    uploaded_file = st.file_uploader("Choisissez un fichier CSV ou Excel", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None:
        df = load_and_process_file(uploaded_file)
        
        if df is not None:
            st.write("Aperçu des données :")
            st.write(df.head())
            
            # Sélection des colonnes
            columns = df.columns.tolist()
            title_col = st.selectbox("Sélectionnez la colonne pour le titre du produit", columns)
            desc_col = st.selectbox("Sélectionnez la colonne pour la description du produit", columns)
            collection_col = st.selectbox("Sélectionnez la colonne pour le nom de la collection", columns)
            
            if st.button("Lancer la catégorisation"):
                with st.spinner("Catégorisation en cours..."):
                    result_df = categorize_products(df, title_col, desc_col, collection_col)
                
                if result_df is not None:
                    st.success("Catégorisation terminée !")
                    st.write("Résultats de la catégorisation :")
                    st.write(result_df)
                    
                    # Option pour télécharger le fichier résultant
                    csv = result_df.to_csv(index=False)
                    st.download_button(
                        label="Télécharger les résultats (CSV)",
                        data=csv,
                        file_name="produits_categorises.csv",
                        mime="text/csv",
                    )

    st.sidebar.header("À propos")
    st.sidebar.info("Cette application permet de catégoriser automatiquement les produits d'une boutique e-commerce en fonction de leurs titres, descriptions et collections associées.")

except Exception as e:
    st.error("Une erreur inattendue s'est produite.")
    st.error(f"Détails de l'erreur : {str(e)}")
    st.error(traceback.format_exc())
