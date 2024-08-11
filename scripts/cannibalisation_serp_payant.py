import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
from unidecode import unidecode
import re
import time
import random
import requests
import json
import os

STOPWORDS = set(['de', 'à', 'pour', 'du', 'le', 'la', 'les', 'un', 'une', 'des', 'en', 'et'])

def preprocess_keyword(keyword):
    keyword = unidecode(keyword.lower())
    keyword = re.sub(r'[^\w\s]', '', keyword)
    return ' '.join([word for word in keyword.split() if word not in STOPWORDS])

def get_api_key():
    # Essayez d'abord d'obtenir la clé API depuis st.secrets
    try:
        api_key = st.secrets.get("valueserp_api_key")
    except Exception as e:
        st.error(f"Erreur lors de l'accès à st.secrets: {e}")
        api_key = None
    
    # Si ce n'est pas dans st.secrets, essayez les variables d'environnement
    if not api_key:
        api_key = os.environ.get("VALUESERP_API_KEY")
    
    # Si toujours pas de clé, demandez à l'utilisateur
    if not api_key:
        api_key = st.text_input("Veuillez entrer votre clé API ValueSERP:", type="password")
    
    if not api_key:
        st.error("Aucune clé API ValueSERP n'a été fournie. L'application ne peut pas fonctionner sans cette clé.")
        st.stop()
    
    return api_key

def get_valueserp_results(keyword, num_results=10):
    api_key = get_api_key()
    url = "https://api.valueserp.com/search"
    params = {
        'api_key': api_key,
        'q': keyword,
        'location': "France",
        'gl': "fr",
        'hl': "fr",
        'google_domain': "google.fr",
        'num': num_results,
        'output': "json"
    }

    try:
        api_result = requests.get(url, params=params)
        api_result.raise_for_status()
        data = api_result.json()
        
        results = []
        if 'organic_results' in data:
            for result in data['organic_results']:
                link = result.get('link', '')
                title = result.get('title', '')
                results.append((link, title))
        
        return results[:num_results]
    
    except Exception as e:
        st.error(f"Error fetching results for '{keyword}': {e}")
        return []

# Le reste du code reste inchangé...

def app():
    st.title("Analyse de cannibalisation de mots-clés SERP")

    # Déplacer l'appel à get_api_key() ici pour s'assurer que la clé est disponible avant le traitement
    api_key = get_api_key()
    if not api_key:
        st.error("Une clé API ValueSERP valide est requise pour continuer.")
        st.stop()

    uploaded_file = st.file_uploader("Importer un fichier Excel ou CSV", type=["xlsx", "csv"])
    serp_similarity_threshold = st.select_slider(
        "Taux de similarité SERP", 
        options=[i/100 for i in range(10, 101, 10)],
        value=0.4,
        format_func=lambda x: f"{int(x*100)}%"
    )

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            st.error("Type de fichier non supporté!")
            st.stop()

        keyword_column = st.selectbox("Sélectionner la colonne des mots-clés", df.columns)
        volume_column = st.selectbox("Sélectionner la colonne des volumes", df.columns)

        st.write("Aperçu du fichier importé:")
        st.dataframe(df.head())

        if st.button("Exécuter l'analyse"):
            result_df = process_keywords(df, keyword_column, volume_column, serp_similarity_threshold)
            
            if result_df is not None:
                st.write("Résultats de l'analyse:")
                st.dataframe(result_df)

                st.download_button(
                    label="Télécharger le fichier de résultats",
                    data=result_df.to_csv(index=False).encode('utf-8'),
                    file_name="resultat_similarite.csv",
                    mime="text/csv"
                )
            else:
                st.error("L'analyse n'a pas pu être complétée en raison d'erreurs.")

if __name__ == "__main__":
    app()
