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
def extract_and_clean_content(url, include_class=None, exclude_class=None):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Assure que la requête est réussie
        soup = BeautifulSoup(response.text, 'html.parser')

        # Inclure une classe spécifique
        if include_class:
            elements = soup.find_all(class_=include_class)
        else:
            elements = [soup]

        # Exclure une classe spécifique
        for element in elements:
            if exclude_class:
                for tag in element.find_all(class_=exclude_class):
                    tag.decompose()

        # Extraire le texte des éléments sélectionnés
        content = " ".join(element.get_text(separator=" ", strip=True) for element in elements)

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

            # Extraire le nom du fichier sans extension
            file_name = uploaded_file.name.rsplit('.', 1)[0]

            # Afficher les colonnes disponibles et permettre à l'utilisateur de sélectionner la colonne des URLs
            column_option = st.selectbox("Sélectionnez la colonne contenant les URLs", df.columns)

            urls = df[column_option].dropna().unique()

            # Ajouter des champs pour inclure et exclure des classes HTML
            include_class = st.text_input("Classe HTML à inclure (optionnel)")
            exclude_class = st.text_input("Classe HTML à exclure (optionnel)")

            # Bouton pour exécuter l'analyse
            if st.button("Exécuter l'analyse"):
                # Initialiser les listes de contenus, embeddings, et URLs valides si non existantes
                if 'contents' not in st.session_state or st.session_state.get('reset', True):
                    st.session_state['contents'] = []
                    st.session_state['embeddings'] = []
                    st.session_state['valid_urls'] = []
                    st.session_state['similarity_matrix'] = None

                    # Extraire et traiter le contenu de chaque URL
                    for url in urls:
                        content = extract_and_clean_content(url, include_class, exclude_class)
                        if content:  # S'assurer que le contenu n'est pas None
                            embedding = get_embeddings(content)
                            if embedding:  # S'assurer que l'embedding n'est pas None
                                st.session_state['contents'].append(content)
                                st.session_state['embeddings'].append(embedding)
                                st.session_state['valid_urls'].append(url)

                    # Calculer la matrice de similarité
                    if len(st.session_state['contents']) == len(st.session_state['embeddings']):
                        st.session_state['similarity_matrix'] = calculate_similarity(st.session_state['embeddings'])
                    else:
                        st.error("Certains embeddings n'ont pas pu être calculés. Vérifiez les URLs pour des erreurs potentielles.")
                        return

                    # Marquer l'état comme non réinitialisé
                    st.session_state['reset'] = False

                # Vérification de la matrice de similarité
                if st.session_state.get('similarity_matrix') is not None:
                    # Utiliser les URLs valides uniquement
                    valid_urls = st.session_state['valid_urls']

                    # Sélecteur d'URL et curseur pour le nombre de résultats
                    selected_url = st.selectbox("Sélectionnez une URL spécifique à filtrer", valid_urls, key='url_select')
                    max_results = st.slider("Nombre d'URLs similaires à afficher (par ordre décroissant)", 1, len(valid_urls) - 1, 5, key='result_slider')

                    # Trouver l'index de l'URL sélectionnée
                    selected_index = valid_urls.index(selected_url)

                    # Obtenir les similarités pour l'URL sélectionnée
                    selected_similarities = st.session_state['similarity_matrix'][selected_index]

                    # Créer un DataFrame des similarités
                    similarity_df = pd.DataFrame({
                        'URL': valid_urls,
                        'Similarité': selected_similarities
                    })

                    # Exclure l'URL sélectionnée
                    similarity_df = similarity_df[similarity_df['URL'] != selected_url]

                    # Trier le DataFrame par similarité décroissante
                    similarity_df = similarity_df.sort_values(by='Similarité', ascending=False)

                    # Afficher le nombre de résultats spécifié par le curseur
                    st.dataframe(similarity_df.head(max_results))

                    # Télécharger le fichier CSV avec les résultats
                    csv = similarity_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Télécharger les urls similaires à l'url filtrée (CSV)",
                        data=csv,
                        file_name=f'urls_similaires_{file_name}.csv',
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

                    for i, url in enumerate(valid_urls):
                        # Obtenir les similarités pour l'URL en cours
                        similarities = st.session_state['similarity_matrix'][i]

                        # Créer un DataFrame temporaire pour trier les similarités
                        temp_df = pd.DataFrame({
                            'URL': valid_urls,
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
                        concatenated = f"Lien 1 : {top_similar_urls[0] if len(top_similar_urls) > 0 else ''}; Lien 2 : {top_similar_urls[1] if len(top_similar_urls) > 1 else ''}; Lien 3 : {top_similar_urls[2] if len(top_similar_urls) > 2 else ''}; Lien 4 : {top_similar_urls[3] if len(top_similar_urls) > 3 else ''}; Lien 5 : {top_similar_urls[4] if len(top_similar_urls) > 4 else ''}"
                        links_table['Concatener'].append(concatenated)

                    # Créer un DataFrame pour le second tableau
                    links_df = pd.DataFrame(links_table)

                    # Afficher le second tableau
                    st.dataframe(links_df)

                    # Télécharger le second tableau en CSV
                    csv_links = links_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Télécharger le tableau du maillage interne (CSV)",
                        data=csv_links,
                        file_name=f'maillage_interne_{file_name}.csv',
                        mime='text/csv'
                    )

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {e}")

# Assurez-vous que la fonction app est appelée ici
if __name__ == "__main__":
    app()
