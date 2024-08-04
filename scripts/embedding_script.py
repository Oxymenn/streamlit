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

# Fonction pour extraire et nettoyer le contenu HTML
def extract_and_clean_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Assure que la requête est réussie
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find(class_='below-woocommerce-category')
        
        if element:
            content = element.get_text(separator=" ", strip=True)
        else:
            st.error(f"Élément non trouvé dans l'URL: {url}")
            return None

        # Nettoyage du texte
        content = re.sub(r'\s+', ' ', content)  # Nettoyer les espaces
        content = content.lower()  # Mettre en minuscules
        content = re.sub(r'[^\w\s]', '', content)  # Supprimer la ponctuation

        # Retirer les mots vides
        words = content.split()
        content = ' '.join([word for word in words if word not in stopwords_fr])

        return content
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de l'accès à {url}: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du contenu de {url}: {e}")
        return None

# Fonction pour obtenir les embeddings d'un texte en utilisant l'API OpenAI
def get_embeddings(text):
    try:
        response = requests.post(
            'https://api.openai.com/v1/embeddings',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'text-embedding-3-small',  # Assurez-vous que ce modèle est disponible
                'input': text,
                'encoding_format': 'float'
            }
        )
        response.raise_for_status()  # Assurez-vous que la réponse est réussie
        data = response.json()
        return data['data'][0]['embedding']
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as e:
        st.error(f"Erreur lors de la création des embeddings: {e}")
    return None

# Fonction pour calculer la similarité cosinus
def calculate_similarity(embeddings):
    try:
        similarity_matrix = cosine_similarity(embeddings)
        return similarity_matrix
    except Exception as e:
        st.error(f"Erreur lors du calcul de la similarité cosinus: {e}")
        return None

# Fonction principale de l'application
def app():
    st.title("Analyse sémantique - Pages similaires")
    uploaded_file = st.file_uploader("Importer un fichier CSV ou Excel contenant des URLs", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Lire le fichier importé
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Afficher les colonnes disponibles et permettre à l'utilisateur de sélectionner la colonne des URLs
            column_option = st.selectbox("Sélectionnez la colonne contenant les URLs", df.columns)

            urls = df[column_option].dropna().unique()

            # Initialiser l'état de session si nécessaire
            if 'contents' not in st.session_state:
                st.session_state['contents'] = [extract_and_clean_content(url) for url in urls]
            if 'embeddings' not in st.session_state:
                st.session_state['embeddings'] = [get_embeddings(content) for content in st.session_state['contents'] if content]
            if 'similarity_matrix' not in st.session_state:
                st.session_state['similarity_matrix'] = calculate_similarity(st.session_state['embeddings'])

            # Vérification de la matrice de similarité
            if st.session_state['similarity_matrix'] is not None:
                # Sélecteur d'URL et curseur pour le nombre de résultats
                selected_url = st.selectbox("Sélectionnez une URL spécifique à filtrer", urls)
                max_results = st.slider("Nombre d'URLs similaires à afficher (par ordre décroissant)", 1, len(urls) - 1, 5)

                # Trouver l'index de l'URL sélectionnée
                selected_index = urls.tolist().index(selected_url)

                # Obtenir les similarités pour l'URL sélectionnée
                selected_similarities = st.session_state['similarity_matrix'][selected_index]

                # Créer un DataFrame des similarités
                similarity_df = pd.DataFrame({
                    'URL': urls,
                    'Similarité': selected_similarities
                })

                # Exclure l'URL sélectionnée
                similarity_df = similarity_df[similarity_df['URL'] != selected_url]

                # Trier le DataFrame par similarité décroissante
                similarity_df = similarity_df.sort_values(by='Similarité', ascending=False)

                # Afficher le nombre de résultats spécifié par le curseur
                st.dataframe(similarity_df.head(max_results))

                # Télécharger le fichier CSV avec les résultats
                csv = similarity_df.to_csv().encode('utf-8')
                st.download_button(
                    label="Télécharger les urls similaires à l'url filtrée (CSV)",
                    data=csv,
                    file_name='similarity_results.csv',
                    mime='text/csv'
                )

                # Créer le second tableau pour toutes les URLs de départ
                links_table = {
                    'URL de départ': [],
                    'URL similaire 1': [],
                    'URL similaire 2': [],
                    'URL similaire 3': [],
                    'URL similaire 4': [],
                    'URL similaire 5': [],
                    'Concatener': []
                }

                for i, url in enumerate(urls):
                    # Obtenir les similarités pour l'URL en cours
                    similarities = st.session_state['similarity_matrix'][i]
                    
                    # Créer un DataFrame temporaire pour trier les similarités
                    temp_df = pd.DataFrame({
                        'URL': urls,
                        'Similarité': similarities
                    })

                    # Exclure l'URL de départ
                    temp_df = temp_df[temp_df['URL'] != url]

                    # Trier et prendre les 5 meilleures similarités
                    top_similar_urls = temp_df.sort_values(by='Similarité', ascending=False).head(5)['URL'].tolist()

                    # Remplir les données dans le tableau
                    links_table['URL de départ'].append(url)
                    links_table['URL similaire 1'].append(top_similar_urls[0] if len(top_similar_urls) > 0 else None)
                    links_table['URL similaire 2'].append(top_similar_urls[1] if len(top_similar_urls) > 1 else None)
                    links_table['URL similaire 3'].append(top_similar_urls[2] if len(top_similar_urls) > 2 else None)
                    links_table['URL similaire 4'].append(top_similar_urls[3] if len(top_similar_urls) > 3 else None)
                    links_table['URL similaire 5'].append(top_similar_urls[4] if len(top_similar_urls) > 4 else None)

                    # Concatener les URLs
                    concatenated = f"Lien 1 : {top_similar_urls[0]}; Lien 2 : {top_similar_urls[1]}; Lien 3 : {top_similar_urls[2]}; Lien 4 : {top_similar_urls[3]}; Lien 5 : {top_similar_urls[4]}"
                    links_table['Concatener'].append(concatenated)

                # Créer un DataFrame pour le second tableau
                links_df = pd.DataFrame(links_table)

                # Afficher le second tableau
                st.dataframe(links_df)

                # Télécharger le second tableau en CSV
                csv_links = links_df.to_csv().encode('utf-8')
                st.download_button(
                    label="Télécharger le tableau du maillage interne (CSV)",
                    data=csv_links,
                    file_name='links_table.csv',
                    mime='text/csv'
                )

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {e}")

# Assurez-vous que la fonction `app` est appelée ici
if __name__ == "__main__":
    app()

