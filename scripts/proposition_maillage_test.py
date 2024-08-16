import streamlit as st
import pandas as pd
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import numpy as np
import re
import lxml
from io import BytesIO
import time
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity

# Liste de stopwords en français (inchangée)
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

# Compile regex patterns
WHITESPACE_REGEX = re.compile(r'\s+')
PUNCTUATION_REGEX = re.compile(r'[^\w\s]')

@st.cache_data
def load_excel_file(uploaded_file):
    return pd.read_excel(BytesIO(uploaded_file.getvalue()))

async def extract_and_clean_content(session, url, include_classes, exclude_classes, additional_stopwords):
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            text = await response.text()
        
        soup = BeautifulSoup(text, 'lxml')

        if include_classes:
            content = ' '.join([element.get_text(separator=" ", strip=True) 
                                for class_name in include_classes 
                                for element in soup.find_all(class_=class_name)])
        else:
            content = soup.get_text(separator=" ", strip=True)

        if exclude_classes:
            for class_name in exclude_classes:
                for element in soup.find_all(class_=class_name):
                    content = content.replace(element.get_text(separator=" ", strip=True), "")

        content = content.lower()
        content = PUNCTUATION_REGEX.sub('', content)
        content = WHITESPACE_REGEX.sub(' ', content)

        words = content.split()
        all_stopwords = stopwords_fr.union(set(additional_stopwords))
        content = ' '.join([word for word in words if word not in all_stopwords])

        return content
    except asyncio.TimeoutError:
        st.warning(f"Timeout lors de l'extraction du contenu de {url}")
        return None
    except Exception as e:
        st.warning(f"Erreur lors de l'extraction du contenu de {url}: {e}")
        return None

def get_embeddings(texts):
    # Tokenize les textes
    tokenized_texts = [text.split() for text in texts]
    
    # Entraîne le modèle Word2Vec
    model = Word2Vec(sentences=tokenized_texts, vector_size=100, window=5, min_count=1, workers=4)
    
    # Calcule les embeddings pour chaque texte
    embeddings = []
    for text in tokenized_texts:
        vec = np.zeros(model.vector_size)
        count = 0
        for word in text:
            if word in model.wv:
                vec += model.wv[word]
                count += 1
        if count != 0:
            vec /= count
        embeddings.append(vec)
    
    return embeddings

def calculate_similarity(embeddings):
    try:
        embeddings_array = np.array(embeddings)
        similarity_matrix = cosine_similarity(embeddings_array)
        return similarity_matrix
    except Exception as e:
        st.error(f"Erreur lors du calcul de la similarité cosinus: {e}")
        return None

async def process_data(urls_list, df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords, progress_bar, status_text, timer_text):
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        contents = []
        for i, url in enumerate(urls_list):
            content = await extract_and_clean_content(session, url, include_classes, exclude_classes, additional_stopwords)
            if content:
                contents.append(content)
            
            progress = (i + 1) / len(urls_list)
            progress_bar.progress(progress)
            
            elapsed_time = time.time() - start_time
            estimated_total_time = elapsed_time / progress
            remaining_time = estimated_total_time - elapsed_time
            
            hours, rem = divmod(remaining_time, 3600)
            minutes, seconds = divmod(rem, 60)
            
            status_text.text(f"URLs analysées : {i+1}/{len(urls_list)}")
            timer_text.text(f"Temps restant estimé : {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    
    if not contents:
        return None, "Aucun contenu n'a pu être extrait des URLs fournies."

    embeddings = get_embeddings(contents)

    similarity_matrix = calculate_similarity(embeddings)

    if similarity_matrix is None:
        return None, "Erreur lors du calcul de la similarité."

    results = []
    for i, url_start in enumerate(urls_list):
        similarities = similarity_matrix[i]
        similar_urls = sorted(zip(urls_list, similarities), key=lambda x: x[1], reverse=True)
        
        similar_urls = [(url, sim) for url, sim in similar_urls if url != url_start]

        ancres_df = df_excel[df_excel[col_url].isin([url for url, _ in similar_urls])]
        ancres_df[col_priorite] = pd.to_numeric(ancres_df[col_priorite], errors='coerce')
        ancres_df = ancres_df.sort_values(col_priorite, ascending=False)[[col_url, col_ancre, col_priorite]]
        
        for j, (url_dest, sim) in enumerate(similar_urls):
            ancre = ancres_df[ancres_df[col_url] == url_dest][col_ancre].iloc[0] if not ancres_df[ancres_df[col_url] == url_dest].empty else url_dest

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

def app():
    st.title("Proposition de Maillage Interne Personnalisé")

    if 'df_results' not in st.session_state:
        st.session_state.df_results = None
    if 'urls_to_analyze' not in st.session_state:
        st.session_state.urls_to_analyze = ""
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'df_excel' not in st.session_state:
        st.session_state.df_excel = None
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
    num_urls = len(urls_list)
    st.write(f"Nombre d'URLs entrées : {num_urls}")
    
    uploaded_file = st.file_uploader("Importer le fichier Excel contenant les URLs, ancres et indices de priorité", type=["xlsx"])
    if uploaded_file is not None and uploaded_file != st.session_state.uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        with st.spinner("Chargement du fichier Excel..."):
            st.session_state.df_excel = load_excel_file(uploaded_file)
        st.success("Fichier Excel chargé avec succès!")

    if st.session_state.df_excel is not None and st.session_state.urls_to_analyze:
        df_excel = st.session_state.df_excel

        col1, col2, col3 = st.columns(3)
        with col1:
            col_url = st.selectbox("Sélectionnez la colonne contenant les URLs", df_excel.columns)
        with col2:
            col_ancre = st.selectbox("Sélectionnez la colonne contenant les ancres", df_excel.columns)
        with col3:
            col_priorite = st.selectbox("Sélectionnez la colonne contenant l'indice de priorité (nombre d'impressions)", df_excel.columns)

        if not all(col in df_excel.columns for col in [col_url, col_ancre, col_priorite]):
            st.error("Erreur: Une ou plusieurs colonnes sélectionnées n'existent pas dans le fichier Excel.")
            return

        if not pd.to_numeric(df_excel[col_priorite], errors='coerce').notna().all():
            st.error(f"Erreur: La colonne '{col_priorite}' contient des valeurs non numériques.")
            return

        max_similar_urls = len(urls_list) - 1
        st.session_state.num_similar_urls = st.slider("Nombre d'URLs similaires à considérer", min_value=1, max_value=max_similar_urls, value=st.session_state.num_similar_urls)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.include_classes = st.text_area("Classes HTML à analyser exclusivement (une classe par ligne, optionnel)", st.session_state.include_classes)
        with col2:
            st.session_state.exclude_classes = st.text_area("Classes HTML à exclure de l'analyse (une classe par ligne, optionnel)", st.session_state.exclude_classes)
        with col3:
            st.session_state.additional_stopwords = st.text_area("Termes/stopwords supplémentaires à exclure de l'analyse (un terme par ligne, optionnel)", st.session_state.additional_stopwords)

        if st.button("Exécuter l'analyse"):
            include_classes = [cls.strip() for cls in st.session_state.include_classes.split('\n') if cls.strip()]
            exclude_classes = [cls.strip() for cls in st.session_state.exclude_classes.split('\n') if cls.strip()]
            additional_stopwords = [word.strip() for word in st.session_state.additional_stopwords.split('\n') if word.strip()]

            progress_bar = st.progress(0)
            status_text = st.empty()
            timer_text = st.empty()

            with st.spinner("Analyse en cours..."):
                st.session_state.df_results, error_message = asyncio.run(process_data(urls_list, df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords, progress_bar, status_text, timer_text))

            progress_bar.empty()
            status_text.empty()
            timer_text.empty()

            if error_message:
                st.error(error_message)
            elif st.session_state.df_results is None:
                st.warning("Aucun résultat n'a été généré.")

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

    if st.button("Réinitialiser l'analyse"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

if __name__ == "__main__":
    app()
