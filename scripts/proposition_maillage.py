import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import io

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

# Fonction pour extraire et nettoyer le contenu HTML (inchangée)
def extract_and_clean_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find(class_='article-template__content')
        
        if element:
            content = element.get_text(separator=" ", strip=True)
        else:
            st.error(f"Élément non trouvé dans l'URL: {url}")
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

# Fonction pour obtenir les embeddings d'un texte (inchangée)
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

# Fonction pour calculer la similarité cosinus (inchangée)
def calculate_similarity(embeddings):
    try:
        similarity_matrix = cosine_similarity(embeddings)
        return similarity_matrix
    except Exception as e:
        st.error(f"Erreur lors du calcul de la similarité cosinus: {e}")
        return None

# Fonction principale de l'application
def app():
    st.title("Proposition de Maillage Interne Personnalisé")

    # Champ pour coller les URLs à analyser
    urls_to_analyze = st.text_area("Collez ici les URLs à analyser (une URL par ligne)")
    
    # Importer le fichier Excel
    uploaded_file = st.file_uploader("Importer le fichier Excel contenant les URLs, ancres et indices de priorité", type=["xlsx"])

    if uploaded_file is not None and urls_to_analyze:
        # Lire le fichier Excel importé
        try:
            df_excel = pd.read_excel(uploaded_file)

            # Vérifier les colonnes nécessaires
            required_columns = ['URL', 'Ancre', 'Impressions']
            if not all(col in df_excel.columns for col in required_columns):
                st.error("Le fichier Excel doit contenir les colonnes 'URL', 'Ancre' et 'Impressions'")
                return

            # Traiter les URLs à analyser
            urls = [url.strip() for url in urls_to_analyze.split('\n') if url.strip()]

            if st.button("Exécuter l'analyse"):
                # Extraire et nettoyer le contenu des URLs
                contents = [extract_and_clean_content(url) for url in urls]
                contents = [content for content in contents if content]

                # Obtenir les embeddings
                embeddings = [get_embeddings(content) for content in contents]
                embeddings = [emb for emb in embeddings if emb]

                # Calculer la matrice de similarité
                similarity_matrix = calculate_similarity(embeddings)

                if similarity_matrix is not None:
                    # Créer le DataFrame de résultats
                    results = []
                    for i, url_start in enumerate(urls):
                        similarities = similarity_matrix[i]
                        similar_urls = sorted(zip(urls, similarities), key=lambda x: x[1], reverse=True)[1:6]  # Top 5 similaires

                        for url_dest, sim in similar_urls:
                            if sim >= 0.75:  # Seulement si la similarité est >= 0.75
                                ancres = df_excel[df_excel['URL'] == url_dest].sort_values('Impressions', ascending=False)['Ancre'].tolist()
                                ancre = ancres[0] if ancres else df_excel.sort_values('Impressions', ascending=False)['Ancre'].iloc[0]
                                results.append({'URL de départ': url_start, 'URL de destination': url_dest, 'Ancre': ancre})

                    # Créer le DataFrame final
                    df_results = pd.DataFrame(results)

                    # Afficher les résultats
                    st.dataframe(df_results)

                    # Option de téléchargement
                    csv = df_results.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Télécharger les résultats (CSV)",
                        data=csv,
                        file_name='maillage_interne_personnalise.csv',
                        mime='text/csv'
                    )
                else:
                    st.error("Erreur lors du calcul de la similarité.")
        except Exception as e:
            st.error(f"Erreur lors du traitement : {e}")

# Exécution de l'application
if __name__ == "__main__":
    app()
