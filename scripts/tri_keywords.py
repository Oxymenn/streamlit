import streamlit as st
import pandas as pd
import numpy as np
import re
from unidecode import unidecode
from nltk.stem.snowball import FrenchStemmer
from nltk.corpus import stopwords
import nltk

# Télécharger les ressources NLTK nécessaires
nltk.download('stopwords')

# Initialiser le stemmer français et la liste des stopwords
stemmer = FrenchStemmer()
stop_words = set(stopwords.words('french'))

def preprocess_keyword(keyword):
    # Convertir en minuscules et supprimer les accents
    keyword = unidecode(keyword.lower())
    # Supprimer la ponctuation
    keyword = re.sub(r'[^\w\s]', '', keyword)
    # Supprimer les stopwords
    keyword = ' '.join([word for word in keyword.split() if word not in stop_words])
    # Appliquer le stemming
    keyword = ' '.join([stemmer.stem(word) for word in keyword.split()])
    # Trier les mots
    keyword = ' '.join(sorted(keyword.split()))
    return keyword

def clean_keywords(df):
    # Créer une copie du DataFrame
    df_cleaned = df.copy()
    
    # Prétraiter les mots-clés
    df_cleaned['cleaned_keyword'] = df_cleaned['keyword'].apply(preprocess_keyword)
    
    # Grouper par mot-clé nettoyé et garder celui avec le volume le plus élevé
    df_cleaned = df_cleaned.loc[df_cleaned.groupby('cleaned_keyword')['volume'].idxmax()]
    
    # Trier par volume décroissant
    df_cleaned = df_cleaned.sort_values('volume', ascending=False)
    
    return df_cleaned

# Interface utilisateur Streamlit
st.title("Nettoyage de mots-clés")

# Upload du fichier CSV
uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

if uploaded_file is not None:
    # Lire le fichier CSV
    df = pd.read_csv(uploaded_file)
    
    # Afficher les premières lignes du DataFrame original
    st.subheader("Données originales")
    st.write(df.head())
    
    # Sélection des colonnes
    keyword_col = st.selectbox("Sélectionnez la colonne des mots-clés", df.columns)
    volume_col = st.selectbox("Sélectionnez la colonne des volumes", df.columns)
    
    # Options de nettoyage
    st.subheader("Options de nettoyage")
    remove_accents = st.checkbox("Supprimer les accents", value=True)
    remove_plurals = st.checkbox("Supprimer les pluriels", value=True)
    ignore_word_order = st.checkbox("Ignorer l'ordre des mots", value=True)
    remove_stopwords = st.checkbox("Supprimer les stopwords", value=True)
    
    if st.button("Nettoyer les mots-clés"):
        # Renommer les colonnes
        df = df.rename(columns={keyword_col: 'keyword', volume_col: 'volume'})
        
        # Appliquer le nettoyage
        df_cleaned = clean_keywords(df)
        
        # Afficher les résultats
        st.subheader("Résultats du nettoyage")
        st.write(f"Nombre de mots-clés originaux : {len(df)}")
        st.write(f"Nombre de mots-clés après nettoyage : {len(df_cleaned)}")
        
        # Afficher les mots-clés nettoyés
        st.subheader("Mots-clés nettoyés")
        st.write(df_cleaned[['keyword', 'volume', 'cleaned_keyword']])
        
        # Téléchargement du fichier CSV nettoyé
        csv = df_cleaned.to_csv(index=False)
        st.download_button(
            label="Télécharger les résultats en CSV",
            data=csv,
            file_name="mots_cles_nettoyes.csv",
            mime="text/csv",
        )
