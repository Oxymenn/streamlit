import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

# Téléchargement des ressources NLTK nécessaires
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def preprocess_text(text):
    if isinstance(text, str):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        tokens = word_tokenize(text)
        stop_words = set(stopwords.words('french'))
        tokens = [word for word in tokens if word not in stop_words]
        return ' '.join(tokens)
    return ''

def load_and_process_file(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file)
    else:
        st.error("Format de fichier non pris en charge. Veuillez utiliser un fichier CSV ou Excel.")
        return None
    return df

def categorize_products(df, title_col, desc_col, collection_col):
    df['combined_text'] = df[title_col] + ' ' + df[desc_col]
    df['processed_text'] = df['combined_text'].apply(preprocess_text)
    df['processed_collection'] = df[collection_col].apply(preprocess_text)
    
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(df['processed_text'])
    
    collections = df['processed_collection'].unique()
    collection_matrix = tfidf.transform(collections)
    
    similarity_matrix = cosine_similarity(tfidf_matrix, collection_matrix)
    
    threshold = 0.1
    categorization = []
    
    for i, row in enumerate(similarity_matrix):
        categories = [collections[j] for j, sim in enumerate(row) if sim > threshold]
        categorization.append(', '.join(categories) if categories else 'Non catégorisé')
    
    df['Catégorisation'] = categorization
    
    return df

st.title("Catégorisation de Produits E-commerce")

uploaded_file = st.file_uploader("Choisissez un fichier CSV ou Excel", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    df = load_and_process_file(uploaded_file)
    
    if df is not None:
        st.write("Aperçu des données :")
        st.write(df.head())
        
        columns = df.columns.tolist()
        title_col = st.selectbox("Sélectionnez la colonne pour le titre du produit", columns)
        desc_col = st.selectbox("Sélectionnez la colonne pour la description du produit", columns)
        collection_col = st.selectbox("Sélectionnez la colonne pour le nom de la collection", columns)
        
        if st.button("Lancer la catégorisation"):
            with st.spinner("Catégorisation en cours..."):
                result_df = categorize_products(df, title_col, desc_col, collection_col)
            
            st.success("Catégorisation terminée !")
            st.write("Résultats de la catégorisation :")
            st.write(result_df)
            
            csv = result_df.to_csv(index=False)
            st.download_button(
                label="Télécharger les résultats (CSV)",
                data=csv,
                file_name="produits_categorises.csv",
                mime="text/csv",
            )

st.sidebar.header("À propos")
st.sidebar.info("Cette application permet de catégoriser automatiquement les produits d'une boutique e-commerce en fonction de leurs titres, descriptions et collections associées.")

