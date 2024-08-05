import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# Liste de stopwords en français
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

@st.cache_data
def extract_and_clean_content(url, include_classes, exclude_classes):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if include_classes:
            elements = []
            for class_name in include_classes:
                elements.extend(soup.find_all(class_=class_name.strip()))
        else:
            elements = soup.find_all(class_='below-woocommerce-category')
        
        if exclude_classes:
            elements = [el for el in elements if not any(cls.strip() in el.get('class', []) for cls in exclude_classes)]
        
        if elements:
            content = ' '.join([element.get_text(separator=" ", strip=True) for element in elements])
        else:
            st.error(f"Éléments non trouvés dans l'URL: {url}")
            return None

        content = re.sub(r'\s+', ' ', content)
        content = content.lower()
        content = re.sub(r'[^\w\s]', '', content)

        words = content.split()
        content = ' '.join([word for word in words if word not in stopwords_fr])

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

def app():
    st.title("Pages Similaires Sémantiquement - Woocommerce (Shoptimizer)")
    
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Classes à inclure")
        include_classes = st.text_area("Entrez les classes HTML à inclure (une par ligne)", 
                                       height=150, 
                                       help="Entrez une classe HTML par ligne à inclure dans l'analyse.")
    
    with col2:
        st.subheader("Classes à exclure")
        exclude_classes = st.text_area("Entrez les classes HTML à exclure (une par ligne)", 
                                       height=150, 
                                       help="Entrez une classe HTML par ligne à exclure de l'analyse.")
    
    include_classes_list = [cls.strip() for cls in include_classes.split('\n') if cls.strip()]
    exclude_classes_list = [cls.strip() for cls in exclude_classes.split('\n') if cls.strip()]
    
    uploaded_file = st.file_uploader("Importer un fichier CSV ou Excel contenant des URLs", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            file_name = uploaded_file.name.rsplit('.', 1)[0]
            column_option = st.selectbox("Sélectionnez la colonne contenant les URLs", df.columns)
            urls = df[column_option].dropna().unique()

            if st.button("Exécuter l'analyse") or st.session_state.analysis_complete:
                if not st.session_state.analysis_complete:
                    with st.spinner("Analyse en cours..."):
                        contents = [extract_and_clean_content(url, include_classes_list, exclude_classes_list) for url in urls]
                        embeddings = [get_embeddings(content) for content in contents if content]
                        similarity_matrix = calculate_similarity(embeddings)
                        
                        st.session_state.urls = urls
                        st.session_state.similarity_matrix = similarity_matrix
                        st.session_state.analysis_complete = True
                    
                    st.success("Analyse terminée!")
                
                similarity_matrix = st.session_state.similarity_matrix
                urls = st.session_state.urls

                selected_url = st.selectbox("Sélectionnez une URL spécifique à filtrer", urls)
                max_results = st.slider("Nombre d'URLs similaires à afficher (par ordre décroissant)", 1, len(urls) - 1, 5)

                selected_index = urls.tolist().index(selected_url)
                selected_similarities = similarity_matrix[selected_index]

                similarity_df = pd.DataFrame({
                    'URL': urls,
                    'Similarité': selected_similarities
                })

                similarity_df = similarity_df[similarity_df['URL'] != selected_url]
                similarity_df = similarity_df.sort_values(by='Similarité', ascending=False)

                st.dataframe(similarity_df.head(max_results))

                csv = similarity_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Télécharger les urls similaires à l'url filtrée (CSV)",
                    data=csv,
                    file_name=f'urls_similaires-{file_name}.csv',
                    mime='text/csv'
                )

                links_table = {'URL de départ': []}
                for n in range(1, max_results + 1):
                    links_table[f'URL similaire {n}'] = []
                links_table['Concatener'] = []

                for i, url in enumerate(urls):
                    similarities = similarity_matrix[i]
                    temp_df = pd.DataFrame({
                        'URL': urls,
                        'Similarité': similarities
                    })
                    temp_df = temp_df[temp_df['URL'] != url]
                    top_similar_urls = temp_df.sort_values(by='Similarité', ascending=False).head(max_results)['URL'].tolist()

                    links_table['URL de départ'].append(url)
                    for n in range(1, max_results + 1):
                        if len(top_similar_urls) >= n:
                            links_table[f'URL similaire {n}'].append(top_similar_urls[n - 1])
                        else:
                            links_table[f'URL similaire {n}'].append(None)

                    concatenated = '; '.join([f"Lien {n} : {top_similar_urls[n - 1]}" if len(top_similar_urls) >= n else f"Lien {n} : " for n in range(1, max_results + 1)])
                    links_table['Concatener'].append(concatenated)

                links_df = pd.DataFrame(links_table)
                st.dataframe(links_df)

                csv_links = links_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Télécharger le tableau du maillage interne (CSV)",
                    data=csv_links,
                    file_name=f'maillage_interne-{file_name}.csv',
                    mime='text/csv'
                )

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier ou de l'analyse: {e}")

if __name__ == "__main__":
    app()
