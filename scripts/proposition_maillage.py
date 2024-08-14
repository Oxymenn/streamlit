import streamlit as st
import pandas as pd
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from openai import AsyncOpenAI
import time
import logging
import json
import hashlib
import os

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

class Cache:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, key):
        return os.path.join(self.cache_dir, hashlib.md5(key.encode()).hexdigest() + '.json')

    def get(self, key):
        path = self._get_cache_path(key)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None

    def set(self, key, value):
        path = self._get_cache_path(key)
        with open(path, 'w') as f:
            json.dump(value, f)

cache = Cache()

@st.cache_data
def load_excel_file(file):
    return pd.read_excel(file, engine='openpyxl')

async def extract_and_clean_content(session, url, include_classes, exclude_classes, additional_stopwords):
    cache_key = f"content_{url}"
    cached_content = cache.get(cache_key)
    if cached_content:
        return url, cached_content

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

        cache.set(cache_key, content)
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

async def get_embedding(client, text):
    cache_key = f"embedding_{hashlib.md5(text.encode()).hexdigest()}"
    cached_embedding = cache.get(cache_key)
    if cached_embedding:
        return cached_embedding

    await rate_limiter.acquire()
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=[text]
        )
        embedding = response.data[0].embedding
        cache.set(cache_key, embedding)
        return embedding
    except Exception as e:
        logging.error(f"Erreur lors de la création de l'embedding: {str(e)}")
        return None

def calculate_similarity(embeddings):
    try:
        return cosine_similarity(embeddings)
    except Exception as e:
        logging.error(f"Erreur lors du calcul de la similarité cosinus: {str(e)}")
        return None

async def process_url(session, client, url, include_classes, exclude_classes, additional_stopwords):
    _, content = await extract_and_clean_content(session, url, include_classes, exclude_classes, additional_stopwords)
    if content:
        embedding = await get_embedding(client, content)
        return url, embedding
    return url, None

async def analyze_urls(urls_list, df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords, api_key):
    client = AsyncOpenAI(api_key=api_key)
    embeddings_cache = {}
    results = []
    error_log = []

    async with aiohttp.ClientSession() as session:
        tasks = [process_url(session, client, url, include_classes, exclude_classes, additional_stopwords) for url in urls_list]
        processed_urls = await asyncio.gather(*tasks)

    for url, embedding in processed_urls:
        if embedding:
            embeddings_cache[url] = embedding
        else:
            error_log.append({"url": url, "error": "Échec de l'extraction du contenu ou de la création de l'embedding"})

    valid_urls = [url for url in urls_list if url in embeddings_cache]
    embeddings = [embeddings_cache[url] for url in valid_urls]
    
    if not embeddings:
        return results, error_log

    similarity_matrix = calculate_similarity(embeddings)

    if similarity_matrix is not None:
        for i, url_start in enumerate(valid_urls):
            similarities = similarity_matrix[i]
            similar_urls = sorted(zip(valid_urls, similarities), key=lambda x: x[1], reverse=True)
            
            similar_urls = [(url, sim) for url, sim in similar_urls if url != url_start][:100]

            for j, (url_dest, sim) in enumerate(similar_urls):
                ancres_df = df_excel[df_excel[col_url] == url_dest]
                ancres_df[col_priorite] = pd.to_numeric(ancres_df[col_priorite], errors='coerce')
                ancres_df = ancres_df.sort_values(col_priorite, ascending=False)[[col_ancre, col_priorite]]
                
                if not ancres_df.empty:
                    ancres = ancres_df[col_ancre].tolist()
                    ancre = ancres[j] if j < len(ancres) else ancres[0]
                else:
                    ancre = url_dest

                results.append({
                    'URL de départ': url_start, 
                    'URL de destination': url_dest, 
                    'Ancre': ancre,
                    'Score de similarité': sim
                })

    return results, error_log

def app():
    st.title("Proposition de Maillage Interne Personnalisé")

    api_key = st.text_input("Entrez votre clé API OpenAI", type="password")

    if 'results' not in st.session_state:
        st.session_state.results = []
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
    
    url_count = len([url.strip() for url in st.session_state.urls_to_analyze.split('\n') if url.strip()])
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

                with st.spinner("Analyse en cours..."):
                    results, error_log = asyncio.run(analyze_urls(urls_list, df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords, api_key))
                    st.session_state.results = results

                end_time = time.time()
                execution_time = end_time - start_time
                st.success(f"Analyse terminée en {execution_time:.2f} secondes.")

                if not results:
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

            if st.session_state.results:
                st.subheader("Résultats")
                df_results = pd.DataFrame(st.session_state.results)
                filtered_results = df_results.groupby('URL de départ').apply(lambda x: x.nlargest(st.session_state.num_similar_urls, 'Score de similarité')).reset_index(drop=True)
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
