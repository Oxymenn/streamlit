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
    uploaded_file = st.file_uploader("Choisissez un fichier Excel ou CSV", type=["xlsx", "csv"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        
        st.write("Aperçu des données :", df.head())
        
        product_title_col = st.selectbox("Sélectionnez la colonne pour le titre du produit", df.columns)
        product_desc_col = st.selectbox("Sélectionnez la colonne pour la description du produit", df.columns)
        collection_name_col = st.selectbox("Sélectionnez la colonne pour le nom de collection", df.columns)
        
        if st.button("Catégoriser les produits"):
            df['Catégorisation'] = ''

            for i, row in df.iterrows():
                title = clean_text(row[product_title_col])
                description = clean_text(row[product_desc_col])
                collection_name = clean_text(row[collection_name_col])
                
                combined_text = title + " " + description
                similarity = find_similarities(combined_text, collection_name)
                
                if similarity > 0.1:
                    df.at[i, 'Catégorisation'] = collection_name
            
            st.write("Données après catégorisation :", df.head())
            
            @st.cache
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')
            
            csv = convert_df(df)
            
            st.download_button(
                label="Télécharger les données avec catégorisation",
                data=csv,
                file_name='produits_categorises.csv',
                mime='text/csv',
            )

# Assurez-vous d'installer les packages nécessaires :
# pip install streamlit pandas numpy scikit-learn beautifulsoup4 nltk
# Pour télécharger les stopwords français : nltk.download('stopwords')
