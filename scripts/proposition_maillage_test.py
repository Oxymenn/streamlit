import streamlit as st
import pandas as pd
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import time
from concurrent.futures import ThreadPoolExecutor

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

@st.cache_resource
def get_sentence_model():
    return SentenceTransformer('distiluse-base-multilingual-cased-v1')

@st.cache_resource
def get_keybert_model():
    sentence_model = get_sentence_model()
    return KeyBERT(model=sentence_model)

async def fetch_content(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            return await response.text()
    except Exception as e:
        st.error(f"Erreur lors de la récupération de {url}: {e}")
        return None

def clean_content(content, include_classes, exclude_classes, additional_stopwords):
    if content is None:
        return None
    soup = BeautifulSoup(content, 'html.parser')

    if include_classes:
        text = ' '.join([element.get_text(separator=" ", strip=True) for class_name in include_classes for element in soup.find_all(class_=class_name)])
    else:
        text = soup.get_text(separator=" ", strip=True)

    if exclude_classes:
        for class_name in exclude_classes:
            for element in soup.find_all(class_=class_name):
                text = text.replace(element.get_text(separator=" ", strip=True), "")

    text = re.sub(r'\s+', ' ', text.lower())
    text = re.sub(r'[^\w\s]', '', text)

    all_stopwords = stopwords_fr.union(set(additional_stopwords))
    words = ' '.join([word for word in text.split() if word not in all_stopwords])

    return words

def extract_keywords(kw_model, content, top_n=5):
    keywords = kw_model.extract_keywords(content, top_n=top_n, keyphrase_ngram_range=(1, 2))
    return ' '.join([kw for kw, _ in keywords])

def calculate_similarity(model, contents):
    embeddings = model.encode(contents)
    return cosine_similarity(embeddings)

@st.cache_data
def process_data(urls_list, df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords):
    kw_model = get_keybert_model()
    sentence_model = get_sentence_model()

    async def fetch_all_content():
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_content(session, url) for url in urls_list]
            return await asyncio.gather(*tasks)

    contents = asyncio.run(fetch_all_content())

    # Ajustement dynamique du nombre de threads
    max_workers = min(20, len(urls_list) // 10 + 1)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        clean_contents = list(executor.map(
            lambda x: clean_content(x, include_classes, exclude_classes, additional_stopwords),
            contents
        ))

    clean_contents = [content for content in clean_contents if content]

    if not clean_contents:
        return None, "Aucun contenu n'a pu être extrait des URLs fournies."

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        keyword_contents = list(executor.map(
            lambda x: extract_keywords(kw_model, x),
            clean_contents
        ))

    similarity_matrix = calculate_similarity(sentence_model, keyword_contents)

    results = []
    for i, url_start in enumerate(urls_list):
        similarities = similarity_matrix[i]
        similar_urls = sorted(zip(urls_list, similarities), key=lambda x: x[1], reverse=True)
        
        similar_urls = [(url, sim) for url, sim in similar_urls if url != url_start]

        for j, (url_dest, sim) in enumerate(similar_urls):
            ancres_df = df_excel[df_excel[col_url] == url_dest]
            ancres_df[col_priorite] = pd.to_numeric(ancres_df[col_priorite], errors='coerce')
            ancres_df = ancres_df.sort_values(col_priorite, ascending=False)[[col_ancre, col_priorite]]
            
            ancre = ancres_df[col_ancre].iloc[min(j, len(ancres_df) - 1)] if not ancres_df.empty else url_dest

            results.append({
                'URL de départ': url_start, 
                'URL de destination': url_dest, 
                'Ancre': ancre,
                'Score de similarité': sim
            })

    df_results = pd.DataFrame(results)

    if df_results.empty:
        return None, "Aucun résultat n'a été trouvé avec les critères spécifiés."

    return df_results, None

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def app():
    st.title("Proposition de Maillage Interne Personnalisé")

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
    
    urls_list = [url.strip() for url in st.session_state.urls_to_analyze.split('\n') if url.strip()]
    st.write(f"Nombre d'URLs à analyser : {len(urls_list)}")

    uploaded_file = st.file_uploader("Importer le fichier Excel contenant les URLs, ancres et indices de priorité", type=["xlsx"])
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file

    if st.session_state.uploaded_file is not None and st.session_state.urls_to_analyze:
        try:
            df_excel = pd.read_excel(st.session_state.uploaded_file)

            st.subheader("Sélectionnez les données GSC")
            col_url = st.selectbox("Sélectionnez la colonne contenant les URLs", df_excel.columns)
            col_ancre = st.selectbox("Sélectionnez la colonne contenant les ancres", df_excel.columns)
            col_priorite = st.selectbox("Sélectionnez la colonne contenant l'indice de priorité (nombre d'impressions)", df_excel.columns)

            if not all(col in df_excel.columns for col in [col_url, col_ancre, col_priorite]):
                st.error("Erreur: Une ou plusieurs colonnes sélectionnées n'existent pas dans le fichier Excel.")
                return

            if not pd.to_numeric(df_excel[col_priorite], errors='coerce').notna().all():
                st.error(f"Erreur: La colonne '{col_priorite}' contient des valeurs non numériques.")
                return

            max_similar_urls = len(urls_list) - 1
            st.session_state.num_similar_urls = st.slider("Nombre d'URLs similaires à considérer", min_value=1, max_value=max_similar_urls, value=st.session_state.num_similar_urls)

            st.subheader("Filtrer le contenu HTML et termes")
            st.session_state.include_classes = st.text_area("Classes HTML à analyser exclusivement (une classe par ligne, optionnel)", st.session_state.include_classes)
            st.session_state.exclude_classes = st.text_area("Classes HTML à exclure de l'analyse (une classe par ligne, optionnel)", st.session_state.exclude_classes)
            st.session_state.additional_stopwords = st.text_area("Termes/stopwords supplémentaires à exclure de l'analyse (un terme par ligne, optionnel)", st.session_state.additional_stopwords)

            if st.button("Exécuter l'analyse"):
                with st.spinner("L'analyse est en cours. Veuillez patienter..."):
                    include_classes = [cls.strip() for cls in st.session_state.include_classes.split('\n') if cls.strip()]
                    exclude_classes = [cls.strip() for cls in st.session_state.exclude_classes.split('\n') if cls.strip()]
                    additional_stopwords = [word.strip() for word in st.session_state.additional_stopwords.split('\n') if word.strip()]

                    start_time = time.time()
                    st.session_state.df_results, error_message = process_data(urls_list, df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords)
                    end_time = time.time()

                    if error_message:
                        st.error(error_message)
                    elif st.session_state.df_results is None:
                        st.warning("Aucun résultat n'a été généré.")
                    else:
                        st.success(f"Analyse terminée en {format_time(end_time - start_time)}. {len(urls_list)} URLs traitées.")

            if st.session_state.df_results is not None:
                filtered_results = st.session_state.df_results.groupby('URL de départ').apply(lambda x: x.nlargest(st.session_state.num_similar_urls, 'Score de similarité')).reset_index(drop=True)
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

    if st.button("Réinitialiser l'analyse"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

if __name__ == "__main__":
    app()
