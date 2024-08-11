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
    try:
        api_key = st.secrets.get("valueserp_api_key")
    except Exception as e:
        st.error(f"Erreur lors de l'accès à st.secrets: {e}")
        api_key = None
    
    if not api_key:
        api_key = os.environ.get("VALUESERP_API_KEY")
    
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

def calculate_serp_similarity(results1, results2):
    common_results = set(results1) & set(results2)
    return len(common_results) / 10

def are_keywords_similar(kw1, kw2):
    processed_kw1 = preprocess_keyword(kw1)
    processed_kw2 = preprocess_keyword(kw2)

    if processed_kw1 == processed_kw2:
        return True

    words1 = Counter(processed_kw1.split())
    words2 = Counter(processed_kw2.split())

    if words1 == words2:
        return True

    intersection = sum((words1 & words2).values())
    union = sum((words1 | words2).values())
    jaccard_similarity = intersection / union if union > 0 else 0

    return jaccard_similarity > 0.8

def process_keywords(df, keyword_column, volume_column, serp_similarity_threshold=0.4):
    keywords = df[keyword_column].tolist()
    volumes = df[volume_column].tolist()
    
    result_data = []
    
    for i, (kw1, vol1) in enumerate(zip(keywords, volumes)):
        similar_keywords = []
        for j, (kw2, vol2) in enumerate(zip(keywords, volumes)):
            if i != j:
                if are_keywords_similar(kw1, kw2):
                    results1 = get_valueserp_results(kw1)
                    results2 = get_valueserp_results(kw2)
                    serp_similarity = calculate_serp_similarity(results1, results2)
                    
                    if serp_similarity >= serp_similarity_threshold:
                        similar_keywords.append({
                            'keyword': kw2,
                            'volume': vol2,
                            'serp_similarity': serp_similarity
                        })
        
        if similar_keywords:
            result_data.append({
                'keyword': kw1,
                'volume': vol1,
                'similar_keywords': similar_keywords
            })
    
    return pd.DataFrame(result_data)

def app():
    st.title("Analyse de cannibalisation de mots-clés SERP")

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
            
            if result_df is not None and not result_df.empty:
                st.write("Résultats de l'analyse:")
                st.dataframe(result_df)

                st.download_button(
                    label="Télécharger le fichier de résultats",
                    data=result_df.to_csv(index=False).encode('utf-8'),
                    file_name="resultat_similarite.csv",
                    mime="text/csv"
                )
            else:
                st.error("L'analyse n'a pas produit de résultats ou a rencontré une erreur.")

if __name__ == "__main__":
    app()
