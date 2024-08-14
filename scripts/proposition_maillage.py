import streamlit as st
import pandas as pd
import dask.dataframe as dd
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from openai import AsyncOpenAI
import time
import concurrent.futures
import pickle
import os
import logging
import json
from functools import partial
import multiprocessing

# Configuration du logging
logging.basicConfig(level=logging.INFO)

# Liste de stopwords en français
stopwords_fr = {
    "alors", "au", "aucuns", "aussi", "autre", "avant", "avec", "avoir", "bon", 
    "car", "ce", "cela", "ces", "ceux", "chaque", "ci", "comme", "comment", 
    "dans", "des", "du", "dedans", "dehors", "depuis", "devrait", "doit", 
    "donc", "dos", "début", "elle", "elles", "en", "encore", "essai", 
    "est", "et", "eu", "fait", "faites", "fois", "font", "hors", "ici", 
    "il", "ils", "je", "juste", "la", "le", "les", "leur", "là", "ma", 
    "maintenant", "mais", "mes", "mien", "moins", "mon", "mot", "même", 
    "ni", "nommés", "notre", "nous", "ou", "où", "par", "parce", "pas", 
    "peut", "peu", "plupart", "pour", "pourquoi", "quand", "que", "quel", 
    "quelle", "quelles", "quels", "qui", "sa", "sans", "ses", "seulement", 
    "si", "sien", "son", "sont", "sous", "soyez", "sujet", "sur", "ta", 
    "tandis", "tellement", "tels", "tes", "ton", "tous", "tout", "trop", 
    "très", "tu", "votre", "vous", "vu", "ça", "étaient", "état", "étions", 
    "été", "être"
}

@st.cache_data
def load_excel_file(file):
    df = pd.read_excel(file, engine='openpyxl')
    return dd.from_pandas(df, npartitions=10)

async def extract_and_clean_content(session, url, include_classes, exclude_classes, additional_stopwords):
    try:
        async with session.get(url, timeout=10) as response:
            html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')

        content = ""
        if include_classes:
            for class_name in include_classes:
                elements = soup.find_all(class_=class_name)
                content += ' '.join([element.get_text(separator=" ", strip=True) for element in elements])
        else:
            content = soup.get_text(separator=" ", strip=True)

        if not content.strip():
            logging.warning(f"Aucun contenu extrait pour l'URL: {url}")
            return url, None

        if exclude_classes:
            for class_name in exclude_classes:
                for element in soup.find_all(class_=class_name):
                    content = content.replace(element.get_text(separator=" ", strip=True), "")

        content = re.sub(r'\s+', ' ', content)
        content = content.lower()
        content = re.sub(r'[^\w\s]', '', content)

        words = content.split()
        all_stopwords = stopwords_fr.union(set(additional_stopwords))
        content = ' '.join([word for word in words if word not in all_stopwords])

        if not content.strip():
            logging.warning(f"Contenu vide après nettoyage pour l'URL: {url}")
            return url, None

        return url, content
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction du contenu pour l'URL {url}: {str(e)}")
        return url, None

class RateLimiter:
    def __init__(self, rate_limit, time_period):
        self.rate_limit = rate_limit
        self.time_period = time_period
        self.tokens = rate_limit
        self.last_update = time.monotonic()

    async def acquire(self):
        while True:
            current_time = time.monotonic()
            time_passed = current_time - self.last_update
            self.tokens += time_passed * (self.rate_limit / self.time_period)
            if self.tokens > self.rate_limit:
                self.tokens = self.rate_limit
            self.last_update = current_time

            if self.tokens >= 1:
                self.tokens -= 1
                return
            else:
                await asyncio.sleep(self.time_period / self.rate_limit)

rate_limiter = RateLimiter(rate_limit=50, time_period=60)  # 50 requests per minute

async def get_embeddings_batch(client, texts):
    await rate_limiter.acquire()
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        logging.error(f"Erreur lors de la création des embeddings: {str(e)}")
        return None

def calculate_similarity_chunk(embeddings_chunk):
    return cosine_similarity(embeddings_chunk)

def calculate_similarity(embeddings):
    try:
        with multiprocessing.Pool() as pool:
            chunk_size = 1000  # Adjust based on your system's capabilities
            chunks = [embeddings[i:i+chunk_size] for i in range(0, len(embeddings), chunk_size)]
            results = pool.map(calculate_similarity_chunk, chunks)
        
        return np.concatenate(results)
    except Exception as e:
        logging.error(f"Erreur lors du calcul de la similarité cosinus: {str(e)}")
        return None

async def process_urls(urls, include_classes, exclude_classes, additional_stopwords):
    async with aiohttp.ClientSession() as session:
        tasks = [extract_and_clean_content(session, url, include_classes, exclude_classes, additional_stopwords) for url in urls]
        return await asyncio.gather(*tasks)

@st.cache_data
def process_data(_urls_list, _df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords, api_key, _progress_callback, batch_size):
    if 'processed_urls' not in st.session_state:
        st.session_state.processed_urls = 0
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'embeddings_cache' not in st.session_state:
        st.session_state.embeddings_cache = {}
    if 'error_log' not in st.session_state:
        st.session_state.error_log = []

    total_urls = len(_urls_list)
    client = AsyncOpenAI(api_key=api_key)

    # Traitement par lots des URLs
    for i in range(st.session_state.processed_urls, total_urls, batch_size):
        batch_urls = _urls_list[i:i+batch_size]
        contents = {}
        
        try:
            # Extraction et nettoyage du contenu de manière asynchrone
            batch_results = asyncio.run(process_urls(batch_urls, include_classes, exclude_classes, additional_stopwords))
            for url, content in batch_results:
                if content:
                    contents[url] = content
                else:
                    st.session_state.error_log.append({"url": url, "error": "Contenu non extrait ou vide"})
                st.session_state.processed_urls += 1
                if st.session_state.processed_urls % 10 == 0:  # Mise à jour moins fréquente
                    _progress_callback(st.session_state.processed_urls, total_urls)

            # Traitement des embeddings pour ce batch
            urls_to_embed = [url for url in contents.keys() if url not in st.session_state.embeddings_cache]
            if urls_to_embed:
                for j in range(0, len(urls_to_embed), 100):  # Traitement par lots de 100 pour les embeddings
                    sub_batch = urls_to_embed[j:j+100]
                    try:
                        new_embeddings = asyncio.run(get_embeddings_batch(client, [contents[url] for url in sub_batch]))
                        for url, embedding in zip(sub_batch, new_embeddings):
                            st.session_state.embeddings_cache[url] = embedding
                    except Exception as e:
                        logging.error(f"Erreur lors de la création des embeddings: {str(e)}")
                        for url in sub_batch:
                            st.session_state.error_log.append({"url": url, "error": f"Échec de création d'embedding: {str(e)}"})

            # Calcul de similarité et ajout aux résultats pour ce batch
            batch_embeddings = [st.session_state.embeddings_cache[url] for url in batch_urls if url in st.session_state.embeddings_cache]
            if batch_embeddings:
                similarity_matrix = calculate_similarity(batch_embeddings)

                relevant_urls = set(batch_urls)
                df_excel_filtered = _df_excel[_df_excel[col_url].isin(relevant_urls)].compute()

                for j, url_start in enumerate(batch_urls):
                    if url_start in st.session_state.embeddings_cache:
                        similarities = similarity_matrix[j]
                        similar_urls = sorted(zip(batch_urls, similarities), key=lambda x: x[1], reverse=True)
                        
                        similar_urls = [(url, sim) for url, sim in similar_urls if url != url_start and url in st.session_state.embeddings_cache][:100]

                        for k, (url_dest, sim) in enumerate(similar_urls):
                            ancres_df = df_excel_filtered[df_excel_filtered[col_url] == url_dest]
                            ancres_df[col_priorite] = pd.to_numeric(ancres_df[col_priorite], errors='coerce')
                            ancres_df = ancres_df.sort_values(col_priorite, ascending=False)[[col_ancre, col_priorite]]
                            
                            if not ancres_df.empty:
                                ancres = ancres_df[col_ancre].tolist()
                                ancre = ancres[k] if k < len(ancres) else ancres[0]
                            else:
                                ancre = url_dest

                            st.session_state.results.append({
                                'URL de départ': url_start, 
                                'URL de destination': url_dest, 
                                'Ancre': ancre,
                                'Score de similarité': sim
                            })

        except Exception as e:
            logging.error(f"Erreur lors du traitement du batch {i}-{i+batch_size}: {str(e)}")
            for url in batch_urls:
                st.session_state.error_log.append({"url": url, "error": f"Erreur de traitement du batch: {str(e)}"})
            continue

    if not st.session_state.results:
        return None, "Aucun résultat n'a été trouvé avec les critères spécifiés."

    df_results = pd.DataFrame(st.session_state.results)
    return df_results, st.session_state.error_log

def count_urls(urls_text):
    urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
    return len(urls)

def app():
    st.title("Proposition de Maillage Interne Personnalisé")

    api_key = st.text_input("Entrez votre clé API OpenAI", type="password")

    if 'df_results' not in st.session_state:
        st.session_state.df_results = None
    if 'urls_to_analyze' not in st.session_state:
        st.session_state.urls_to_analyze = ""
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'num_similar_urls' not in st.session_state:
        st.session_state.num_similar_urls = 5
    if 'include_classes' not in st.session_state:
        st.session_state.include_classes = ""
    if 'exclude_classes' not in st.session_state:
        st.session_state.exclude_classes = ""
    if 'additional_stopwords' not in st.session_state:
        st.session_state.additional_stopwords = ""

    st.session_state.urls_to_analyze = st.text_area("Collez ici les URLs à analyser (une URL par ligne)", st.session_state.urls_to_analyze)
    
    url_count = count_urls(st.session_state.urls_to_analyze)
    st.info(f"Nombre d'URLs copiées : {url_count}")
    
    uploaded_file = st.file_uploader("Importer le fichier Excel contenant les URLs, ancres et indices de priorité", type=["xlsx"])
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file

    if st.session_state.uploaded_file is not None and st.session_state.urls_to_analyze and api_key:
        try:
            df_excel = load_excel_file(st.session_state.uploaded_file)

            st.subheader("Sélectionnez les données GSC")
            col_url = st.selectbox("Sélectionnez la colonne contenant les URLs", df_excel.columns)
            col_ancre = st.selectbox("Sélectionnez la colonne contenant les ancres", df_excel.columns)
            col_priorite = st.selectbox("Sélectionnez la colonne contenant l'indice de priorité (nombre d'impressions)", df_excel.columns)

            if not all(col in df_excel.columns for col in [col_url, col_ancre, col_priorite]):
                st.error("Erreur: Une ou plusieurs colonnes sélectionnées n'existent pas dans le fichier Excel.")
                return

            urls_list = [url.strip() for url in st.session_state.urls_to_analyze.split('\n') if url.strip()]
            max_similar_urls = min(len(urls_list) - 1, 100)  # Limit to 100 max similar URLs

            st.subheader("Paramètres d'analyse")
            batch_size = st.selectbox("Taille du batch d'URLs à analyser", options=[10, 20, 50, 100, 200, 500], index=3)
            st.session_state.num_similar_urls = st.number_input(
                "Nombre d'URLs similaires à considérer", 
                min_value=1, 
                max_value=max_similar_urls, 
                value=min(5, max_similar_urls)
            )

            st.subheader("Filtrer le contenu HTML et termes")
            st.session_state.include_classes = st.text_area("Classes HTML à analyser exclusivement (une classe par ligne, optionnel)", st.session_state.include_classes)
            st.session_state.exclude_classes = st.text_area("Classes HTML à exclure de l'analyse (une classe par ligne, optionnel)", st.session_state.exclude_classes)
            st.session_state.additional_stopwords = st.text_area("Termes/stopwords supplémentaires à exclure de l'analyse (un terme par ligne, optionnel)", st.session_state.additional_stopwords)

            if st.button("Exécuter l'analyse"):
                include_classes = [cls.strip() for cls in st.session_state.include_classes.split('\n') if cls.strip()]
                exclude_classes = [cls.strip() for cls in st.session_state.exclude_classes.split('\n') if cls.strip()]
                additional_stopwords = [word.strip() for word in st.session_state.additional_stopwords.split('\n') if word.strip()]

                progress_bar = st.progress(0)
                status_text = st.empty()
                start_time = time.time()

                def update_progress(current, total):
                    progress = int((current / total) * 100)
                    progress_bar.progress(progress)
                    elapsed_time = time.time() - start_time
                    estimated_total_time = elapsed_time * (total / current) if current > 0 else 0
                    remaining_time = max(0, estimated_total_time - elapsed_time)
                    status_text.text(f"Progression : {progress}% | URLs analysées : {current}/{total} | Temps restant estimé : {remaining_time:.2f} secondes")

                with st.spinner("Analyse en cours..."):
                    st.session_state.df_results, error_log = process_data(urls_list, df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords, api_key, update_progress, batch_size)

                end_time = time.time()
                execution_time = end_time - start_time
                st.success(f"Analyse terminée en {execution_time:.2f} secondes.")

                if isinstance(error_log, str):
                    st.error(error_log)
                elif st.session_state.df_results is None:
                    st.warning("Aucun résultat n'a été généré.")
                else:
                    st.info(f"Nombre d'erreurs rencontrées : {len(error_log)}")
                    if error_log:
                        st.download_button(
                            label="Télécharger le log d'erreurs (JSON)",
                            data=json.dumps(error_log, indent=2),
                            file_name='error_log.json',
                            mime='application/json'
                        )

            if st.session_state.df_results is not None:
                st.subheader("Résultats")
                num_similar_urls = st.number_input(
                    "Nombre d'URLs similaires à afficher", 
                    min_value=1, 
                    max_value=max_similar_urls, 
                    value=st.session_state.num_similar_urls
                )
                filtered_results = st.session_state.df_results.groupby('URL de départ').apply(lambda x: x.nlargest(num_similar_urls, 'Score de similarité')).reset_index(drop=True)
                st.dataframe(filtered_results)

                csv = filtered_results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Télécharger les résultats (CSV)",
                    data=csv,
                    file_name='maillage_interne_personnalise.csv',
                    mime='text/csv'
                )

        except Exception as e:
            st.error(f"Erreur lors du traitement : {str(e)}")

    elif not api_key:
        st.warning("Veuillez entrer votre clé API OpenAI pour continuer.")

    if st.button("Réinitialiser l'analyse"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

if __name__ == "__main__":
    app()
