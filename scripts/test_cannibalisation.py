import streamlit as st
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import Counter
from unidecode import unidecode
import re
import time
import random

STOPWORDS = set(['de', 'à', 'pour', 'du', 'le', 'la', 'les', 'un', 'une', 'des', 'en', 'et'])

def preprocess_keyword(keyword):
    keyword = unidecode(keyword.lower())
    keyword = re.sub(r'[^\w\s]', '', keyword)
    return ' '.join([word for word in keyword.split() if word not in STOPWORDS])

def get_google_results(driver, keyword, num_results=10, delay_min=3, delay_max=5):
    url = f"https://www.google.fr/search?q={keyword}&num={num_results}"
    driver.get(url)
    
    try:
        # Attendre que les résultats soient chargés
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.yuRUbf"))
        )
        
        results = []
        for div in driver.find_elements(By.CSS_SELECTOR, "div.yuRUbf"):
            anchor = div.find_element(By.TAG_NAME, "a")
            title = div.find_element(By.TAG_NAME, "h3").text
            link = anchor.get_attribute("href")
            results.append((link, title))
            
            if len(results) >= num_results:
                break
        
        time.sleep(random.uniform(delay_min, delay_max))
        
        return results[:num_results]
    
    except Exception as e:
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

def process_keywords(df, keyword_column, volume_column, serp_similarity_threshold=0.4, delay_min=3, delay_max=5):
    start_time = time.time()
    st.write("\n🕒 Début du traitement...")

    keywords = df[keyword_column].tolist()
    volumes = df[volume_column].tolist()
    total_keywords = len(keywords)
    
    placeholder = st.empty()
    progress_bar = st.progress(0)
    progress_text = st.empty()

    st.write("\n📊 Récupération des résultats Google...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    with webdriver.Chrome(options=chrome_options) as driver:
        google_results = {}
        for i, kw in enumerate(keywords):
            results = get_google_results(driver, kw, delay_min=delay_min, delay_max=delay_max)
            if results:
                google_results[kw] = results
            else:
                st.write(f"Skipping keyword '{kw}' due to no results")

            elapsed_time = time.time() - start_time
            estimated_time_remaining = (elapsed_time / (i + 1)) * (total_keywords - (i + 1))
            
            progress_bar.progress((i + 1) / total_keywords)
            progress_text.text(f"Requêtes restantes: {total_keywords - (i + 1)}, Temps estimé restant: {int(estimated_time_remaining // 60)}m {int(estimated_time_remaining % 60)}s")

    st.write("\n🔍 Analyse de similarité...")
    similar_groups = []
    processed = set()

    for i, kw1 in enumerate(keywords):
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
    serp_similarity_threshold = st.select_slider(
        "Taux de similarité SERP", 
        options=[i/100 for i in range(10, 101, 10)],
        format_func=lambda x: f"{int(x*100)}%"
    )
    delay_range = st.slider(
        "Plage de délai des requêtes Google (en secondes)", 
        1, 30, (3, 5)
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
            result_df = process_keywords(df, keyword_column, volume_column, serp_similarity_threshold, delay_range[0], delay_range[1])
            
            st.write("Résultats de l'analyse:")
            st.dataframe(result_df)

            st.download_button(
                label="Télécharger le fichier de résultats",
                data=result_df.to_csv(index=False).encode('utf-8'),
                file_name="resultat_similarite.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    app()
