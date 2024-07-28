import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from collections import Counter
from unidecode import unidecode
import re
import time
import random
from tqdm import tqdm

STOPWORDS = set(['de', 'à', 'pour', 'du', 'le', 'la', 'les', 'un', 'une', 'des', 'en', 'et'])

def preprocess_keyword(keyword):
    keyword = unidecode(keyword.lower())
    keyword = re.sub(r'[^\w\s]', '', keyword)
    return ' '.join([word for word in keyword.split() if word not in STOPWORDS])

def get_google_results(keyword, num_results=10, delay=3):
    url = f"https://www.google.fr/search?q={keyword}&num={num_results}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        for div in soup.find_all('div', class_='yuRUbf'):
            anchor = div.find('a')
            if anchor and 'href' in anchor.attrs:
                link = anchor['href']
                title = div.find('h3').text if div.find('h3') else ''
                results.append((link, title))

            if len(results) >= num_results:
                break

        # Augmentation du délai entre les requêtes
        time.sleep(random.uniform(delay - 1, delay + 1))

        return results[:num_results]

    except requests.RequestException as e:
        st.error(f"Error fetching results for '{keyword}': {e}")
        return []

def calculate_serp_similarity(results1, results2):
    common_results = set(results1) & set(results2)
    return len(common_results) / 10  # 10 est le nombre total de résultats

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

def process_keywords(df, keyword_column, volume_column, serp_similarity_threshold=0.4, delay=3):
    start_time = time.time()
    st.write("\n🕒 Début du traitement...")

    keywords = df[keyword_column].tolist()
    volumes = df[volume_column].tolist()

    st.write("\n📊 Récupération des résultats Google...")
    google_results = {}
    for kw in tqdm(keywords, desc="Traitement des mots-clés"):
        results = get_google_results(kw, delay=delay)
        if results:
            google_results[kw] = results
        else:
            st.write(f"Skipping keyword '{kw}' due to no results")

    st.write("\n🔍 Analyse de similarité...")
    similar_groups = []
    processed = set()

    for i, kw1 in enumerate(tqdm(keywords, desc="Comparaison des mots-clés")):
        if i in processed:
            continue

        group = [i]
        for j, kw2 in enumerate(keywords[i + 1:], start=i + 1):
            if j in processed:
                continue

            serp_similarity = calculate_serp_similarity(google_results.get(kw1, []), google_results.get(kw2, []))
            keyword_similarity = are_keywords_similar(kw1, kw2)

            if serp_similarity > serp_similarity_threshold or keyword_similarity:
                group.append(j)

        similar_groups.append(group)
        processed.update(group)

    st.write("\n🔤 Création des mots-clés uniques...")
    unique_keywords = {}
    for group in similar_groups:
        max_volume_index = max(group, key=lambda x: volumes[x])
        unique_keywords[keywords[max_volume_index]] = volumes[max_volume_index]

    df['mots-clés uniques'] = ''
    df['volumes'] = ''

    for kw, vol in unique_keywords.items():
        mask = df[keyword_column] == kw
        df.loc[mask, 'mots-clés uniques'] = kw
        df.loc[mask, 'volumes'] = vol

    df['volumes_sort'] = pd.to_numeric(df['volumes'].fillna(0), errors='coerce').fillna(0).astype(int)
    df = df.sort_values('volumes_sort', ascending=False)
    df = df.drop('volumes_sort', axis=1)

    end_time = time.time()
    total_time = end_time - start_time
    hours, rem = divmod(total_time, 3600)
    minutes, seconds = divmod(rem, 60)

    st.write(f"\n✅ Traitement terminé en {int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}")

    return df

def app():
    st.title("Analyse de cannibalisation de mots-clés SERP")

    uploaded_file = st.file_uploader("Importer un fichier Excel ou CSV", type=["xlsx", "csv"])
    serp_similarity_threshold = st.slider("Taux de similarité SERP", 0.0, 1.0, 0.4)
    delay = st.slider("Délai des requêtes Google (en secondes)", 1, 10, 3)

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
            result_df = process_keywords(df, keyword_column, volume_column, serp_similarity_threshold, delay)
            
            st.write("Résultats de l'analyse:")
            st.dataframe(result_df)

            st.download_button(
                label="Télécharger le fichier de résultats",
                data=result_df.to_csv(index=False).encode('utf-8'),
                file_name="resultat_similarite.csv",
                mime="text/csv"
            )
