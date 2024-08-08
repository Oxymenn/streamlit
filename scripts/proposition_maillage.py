import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import io

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

# Configuration de la clé API OpenAI
OPENAI_API_KEY = st.secrets.get("api_key", "default_key")

def extract_and_clean_content(url, include_classes, exclude_classes, additional_stopwords):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        if include_classes:
            elements = soup.find_all(class_=include_classes)
        else:
            elements = [soup]

        if exclude_classes:
            for cls in exclude_classes:
                for element in elements:
                    for excluded in element.find_all(class_=cls):
                        excluded.decompose()

        content = ' '.join([element.get_text(separator=" ", strip=True) for element in elements])

        content = re.sub(r'\s+', ' ', content)
        content = content.lower()
        content = re.sub(r'[^\w\s]', '', content)

        words = content.split()
        all_stopwords = stopwords_fr.union(set(additional_stopwords))
        content = ' '.join([word for word in words if word not in all_stopwords])

        return content
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de l'accès à {url}: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du contenu de {url}: {e}")
        return None

def get_embeddings(text):
    try:
        response = requests.post(
            'https://api.openai.com/v1/embeddings',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'text-embedding-3-small',
                'input': text,
                'encoding_format': 'float'
            }
        )
        response.raise_for_status()
        data = response.json()
        return data['data'][0]['embedding']
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as e:
        st.error(f"Erreur lors de la création des embeddings: {e}")
    return None

def calculate_similarity(embeddings):
    try:
        similarity_matrix = cosine_similarity(embeddings)
        return similarity_matrix
    except Exception as e:
        st.error(f"Erreur lors du calcul de la similarité cosinus: {e}")
        return None

@st.cache_data
def process_data(urls_list, df_excel, col_url, col_ancre, col_priorite, num_links, include_classes, exclude_classes, additional_stopwords):
    contents = [extract_and_clean_content(url, include_classes, exclude_classes, additional_stopwords) for url in urls_list]
    contents = [content for content in contents if content]

    if not contents:
        return None, "Aucun contenu n'a pu être extrait des URLs fournies."

    embeddings = [get_embeddings(content) for content in contents]
    embeddings = [emb for emb in embeddings if emb]

    if not embeddings:
        return None, "Impossible de générer des embeddings pour les contenus extraits."

    similarity_matrix = calculate_similarity(embeddings)

    if similarity_matrix is None:
        return None, "Erreur lors du calcul de la similarité."

    results = []
    for i, url_start in enumerate(urls_list):
        similarities = similarity_matrix[i]
        similar_urls = sorted(zip(urls_list, similarities), key=lambda x: x[1], reverse=True)
        
        # Exclure l'URL de départ elle-même et prendre les num_links suivantes
        similar_urls = [(url, sim) for url, sim in similar_urls if url != url_start][:num_links]

        for url_dest, sim in similar_urls:
            ancres_df = df_excel[df_excel[col_url] == url_dest].sort_values(col_priorite, ascending=False)[[col_ancre, col_priorite]]
            
            if not ancres_df.empty:
                ancres = ancres_df[col_ancre].tolist()
                
                # Sélectionner les ancres en respectant l'ordre de priorité
                selected_ancres = []
                for _ in range(num_links):
                    if ancres:
                        selected_ancres.append(ancres.pop(0))
                    else:
                        # Si on a épuisé toutes les ancres, on reprend celle avec le plus d'impressions
                        selected_ancres.append(ancres_df.iloc[0][col_ancre])
                
                for ancre in selected_ancres:
                    results.append({
                        'URL de départ': url_start, 
                        'URL de destination': url_dest, 
                        'Ancre': ancre,
                        'Score de similarité': sim
                    })
            else:
                # Si aucune ancre n'est trouvée, utiliser l'URL de destination comme ancre
                for _ in range(num_links):
                    results.append({
                        'URL de départ': url_start, 
                        'URL de destination': url_dest, 
                        'Ancre': url_dest,
                        'Score de similarité': sim
                    })

    df_results = pd.DataFrame(results)

    if df_results.empty:
        return None, "Aucun résultat n'a été trouvé avec les critères spécifiés."

    return df_results, None

def app():
    st.title("Proposition de Maillage Interne Personnalisé")

    # Initialiser session_state
    if 'df_results' not in st.session_state:
        st.session_state.df_results = None
    if 'urls_to_analyze' not in st.session_state:
        st.session_state.urls_to_analyze = ""
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'num_links' not in st.session_state:
        st.session_state.num_links = 5
    if 'include_classes' not in st.session_state:
        st.session_state.include_classes = ""
    if 'exclude_classes' not in st.session_state:
        st.session_state.exclude_classes = ""
    if 'additional_stopwords' not in st.session_state:
        st.session_state.additional_stopwords = ""

    # Interface utilisateur
    st.session_state.urls_to_analyze = st.text_area("Collez ici les URLs à analyser (une URL par ligne)", st.session_state.urls_to_analyze)
    
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

            urls_list = [url.strip() for url in st.session_state.urls_to_analyze.split('\n') if url.strip()]
            max_links = 10  # Vous pouvez ajuster cette valeur selon vos besoins
            st.session_state.num_links = st.slider("Nombre de liens à créer pour chaque URL de destination", min_value=1, max_value=max_links, value=st.session_state.num_links)

            st.subheader("Filtrer le contenu HTML et termes")
            st.session_state.include_classes = st.text_area("Classes HTML à analyser exclusivement (une classe par ligne, optionnel)", st.session_state.include_classes)
            st.session_state.exclude_classes = st.text_area("Classes HTML à exclure de l'analyse (une classe par ligne, optionnel)", st.session_state.exclude_classes)
            st.session_state.additional_stopwords = st.text_area("Termes/stopwords supplémentaires à exclure de l'analyse (un terme par ligne, optionnel)", st.session_state.additional_stopwords)

            if st.button("Exécuter l'analyse") or st.session_state.df_results is not None:
                if st.session_state.df_results is None:
                    include_classes = [cls.strip() for cls in st.session_state.include_classes.split('\n') if cls.strip()]
                    exclude_classes = [cls.strip() for cls in st.session_state.exclude_classes.split('\n') if cls.strip()]
                    additional_stopwords = [word.strip() for word in st.session_state.additional_stopwords.split('\n') if word.strip()]

                    st.session_state.df_results, error_message = process_data(urls_list, df_excel, col_url, col_ancre, col_priorite, st.session_state.num_links, include_classes, exclude_classes, additional_stopwords)

                    if error_message:
                        st.error(error_message)
                    elif st.session_state.df_results is None:
                        st.warning("Aucun résultat n'a été généré.")

                if st.session_state.df_results is not None:
                    st.dataframe(st.session_state.df_results)

                    csv = st.session_state.df_results.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Télécharger les résultats (CSV)",
                        data=csv,
                        file_name='maillage_interne_personnalise.csv',
                        mime='text/csv'
                    )

        except Exception as e:
            st.error(f"Erreur lors du traitement : {str(e)}")

    # Bouton pour réinitialiser l'analyse
    if st.button("Réinitialiser l'analyse"):
        st.session_state.df_results = None
        st.experimental_rerun()

if __name__ == "__main__":
    app()
