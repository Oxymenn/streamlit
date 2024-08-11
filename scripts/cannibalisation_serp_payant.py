import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
from unidecode import unidecode
import re
import requests
import traceback

STOPWORDS = set(['de', 'à', 'pour', 'du', 'le', 'la', 'les', 'un', 'une', 'des', 'en', 'et'])

def preprocess_keyword(keyword):
    keyword = unidecode(keyword.lower())
    keyword = re.sub(r'[^\w\s]', '', keyword)
    return ' '.join([word for word in keyword.split() if word not in STOPWORDS])

def get_valueserp_results(keyword, api_key, num_results=10):
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
    
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la requête API pour '{keyword}': {e}")
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

def process_keywords(df, keyword_column, volume_column, serp_similarity_threshold, api_key):
    keywords = df[keyword_column].tolist()
    volumes = df[volume_column].tolist()
    
    st.write(f"Nombre total de mots-clés : {len(keywords)}")
    
    result_data = []
    
    for i, (kw1, vol1) in enumerate(zip(keywords, volumes)):
        st.write(f"Traitement du mot-clé {i+1}/{len(keywords)}: {kw1}")
        similar_keywords = []
        for j, (kw2, vol2) in enumerate(zip(keywords, volumes)):
            if i != j:
                if are_keywords_similar(kw1, kw2):
                    st.write(f"  Comparaison avec : {kw2}")
                    results1 = get_valueserp_results(kw1, api_key)
                    results2 = get_valueserp_results(kw2, api_key)
                    if not results1 or not results2:
                        st.warning(f"  Impossible d'obtenir les résultats SERP pour '{kw1}' ou '{kw2}'")
                        continue
                    serp_similarity = calculate_serp_similarity(results1, results2)
                    st.write(f"  Similarité SERP : {serp_similarity}")
                    
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
    
    st.write(f"Nombre de résultats : {len(result_data)}")
    return pd.DataFrame(result_data)

def app():
    st.title("Analyse de cannibalisation de mots-clés SERP")

    api_key = st.text_input("Veuillez entrer votre clé API ValueSERP:", type="password")

    if not api_key:
        st.warning("Une clé API ValueSERP est requise pour continuer.")
        st.stop()

    uploaded_file = st.file_uploader("Importer un fichier Excel ou CSV", type=["xlsx", "csv"])
    serp_similarity_threshold = st.select_slider(
        "Taux de similarité SERP", 
        options=[i/100 for i in range(10, 101, 10)],
        value=0.4,
        format_func=lambda x: f"{int(x*100)}%"
    )

    if uploaded_file is not None:
        try:
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
                with st.spinner("Analyse en cours..."):
                    result_df = process_keywords(df, keyword_column, volume_column, serp_similarity_threshold, api_key)
                
                if result_df is not None:
                    if not result_df.empty:
                        st.success("Analyse terminée avec succès!")
                        st.write("Résultats de l'analyse:")
                        st.dataframe(result_df)

                        st.download_button(
                            label="Télécharger le fichier de résultats",
                            data=result_df.to_csv(index=False).encode('utf-8'),
                            file_name="resultat_similarite.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("L'analyse n'a trouvé aucun mot-clé similaire selon les critères définis.")
                else:
                    st.error("Une erreur s'est produite lors de l'analyse. Veuillez vérifier vos données d'entrée et votre clé API.")
        except Exception as e:
            st.error(f"Une erreur s'est produite lors de l'analyse : {str(e)}")
            st.error(f"Détails de l'erreur : {traceback.format_exc()}")

if __name__ == "__main__":
    app()
