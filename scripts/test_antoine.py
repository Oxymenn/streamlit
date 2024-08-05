import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from functools import lru_cache

# Liste de stopwords en français (inchangée)
stopwords_fr = {
    "alors", "boutique", "site", "collection", "gamme", "découvrez", "sélection", "explorez", "nettoyer", "nettoyez", "entretien", "entretenir", "au", "aucuns", "aussi", "autre", "avant", "avec", "avoir", "bon", 
    "car", "ce", "cela", "ces", "ceux", "chaque", "ci", "comme", "comment", 
    "dans", "des", "du", "dedans", "dehors", "depuis", "devrait", "doit", 
    "donc", "dos", "droite", "début", "elle", "elles", "en", "encore", "essai", 
    "est", "et", "eu", "fait", "faites", "fois", "font", "force", "haut", 
    "hors", "ici", "il", "ils", "je", "juste", "la", "le", "les", "leur", 
    "là", "ma", "maintenant", "mais", "mes", "mien", "moins", "mon", "mot", 
    "même", "ni", "nommés", "notre", "nous", "nouveaux", "ou", "où", "par", 
    "parce", "parole", "pas", "personnes", "peut", "peu", "pièce", "plupart", 
    "pour", "pourquoi", "quand", "que", "quel", "quelle", "quelles", "quels", 
    "qui", "sa", "sans", "ses", "seulement", "si", "sien", "son", "sont", 
    "sous", "soyez", "sujet", "sur", "ta", "tandis", "tellement", "tels", 
    "tes", "ton", "tous", "tout", "trop", "très", "tu", "valeur", "voie", 
    "voient", "vont", "votre", "vous", "vu", "ça", "étaient", "état", "étions", 
    "été", "être"
}

# Configuration de la clé API OpenAI
OPENAI_API_KEY = st.secrets.get("api_key", "default_key")

@lru_cache(maxsize=None)
def extract_and_clean_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find(class_='below-woocommerce-category')
        
        if not element:
            st.error(f"Élément non trouvé dans l'URL: {url}")
            return None

        content = element.get_text(separator=" ", strip=True)
        content = re.sub(r'\s+', ' ', content.lower())
        content = re.sub(r'[^\w\s]', '', content)
        return ' '.join([word for word in content.split() if word not in stopwords_fr])
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de l'accès à {url}: {e}")
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du contenu de {url}: {e}")
    return None

@lru_cache(maxsize=None)
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
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()['data'][0]['embedding']
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as e:
        st.error(f"Erreur lors de la création des embeddings: {e}")
    return None

def calculate_similarity(embeddings):
    try:
        return cosine_similarity(embeddings)
    except Exception as e:
        st.error(f"Erreur lors du calcul de la similarité cosinus: {e}")
        return None

def create_similarity_df(urls, similarity_matrix, selected_url, max_results):
    selected_index = urls.tolist().index(selected_url)
    selected_similarities = similarity_matrix[selected_index]
    similarity_df = pd.DataFrame({
        'URL': urls,
        'Similarité': selected_similarities
    })
    similarity_df = similarity_df[similarity_df['URL'] != selected_url]
    return similarity_df.sort_values(by='Similarité', ascending=False).head(max_results)

def create_links_table(urls, similarity_matrix, max_results):
    links_table = {'URL de départ': []}
    for n in range(1, max_results + 1):
        links_table[f'URL similaire {n}'] = []
    links_table['Concatener'] = []

    for i, url in enumerate(urls):
        similarities = similarity_matrix[i]
        temp_df = pd.DataFrame({'URL': urls, 'Similarité': similarities})
        temp_df = temp_df[temp_df['URL'] != url]
        top_similar_urls = temp_df.sort_values(by='Similarité', ascending=False).head(max_results)['URL'].tolist()

        links_table['URL de départ'].append(url)
        for n in range(1, max_results + 1):
            links_table[f'URL similaire {n}'].append(top_similar_urls[n - 1] if len(top_similar_urls) >= n else None)

        concatenated = '; '.join([f"Lien {n} : {top_similar_urls[n - 1]}" if len(top_similar_urls) >= n else f"Lien {n} : " for n in range(1, max_results + 1)])
        links_table['Concatener'].append(concatenated)

    return pd.DataFrame(links_table)

def app():
    st.title("Pages Similaires Sémantiquement - Woocommerce (Shoptimizer)")
    uploaded_file = st.file_uploader("Importer un fichier CSV ou Excel contenant des URLs", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            file_name = uploaded_file.name.rsplit('.', 1)[0]
            column_option = st.selectbox("Sélectionnez la colonne contenant les URLs", df.columns)
            urls = df[column_option].dropna().unique()

            if 'contents' not in st.session_state:
                st.session_state['contents'] = [extract_and_clean_content(url) for url in urls]
            if 'embeddings' not in st.session_state:
                st.session_state['embeddings'] = [get_embeddings(content) for content in st.session_state['contents'] if content]
            if 'similarity_matrix' not in st.session_state:
                st.session_state['similarity_matrix'] = calculate_similarity(st.session_state['embeddings'])

            if st.session_state['similarity_matrix'] is not None:
                selected_url = st.selectbox("Sélectionnez une URL spécifique à filtrer", urls)
                max_results = st.slider("Nombre d'URLs similaires à afficher (par ordre décroissant)", 1, len(urls) - 1, 5)

                similarity_df = create_similarity_df(urls, st.session_state['similarity_matrix'], selected_url, max_results)
                st.dataframe(similarity_df)

                csv = similarity_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Télécharger les urls similaires à l'url filtrée (CSV)",
                    data=csv,
                    file_name=f'urls_similaires-{file_name}.csv',
                    mime='text/csv'
                )

                links_df = create_links_table(urls, st.session_state['similarity_matrix'], max_results)
                st.dataframe(links_df)

                csv_links = links_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Télécharger le tableau du maillage interne (CSV)",
                    data=csv_links,
                    file_name=f'maillage_interne-{file_name}.csv',
                    mime='text/csv'
                )

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {e}")

if __name__ == "__main__":
    app()
