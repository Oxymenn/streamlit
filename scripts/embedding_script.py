import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import re

# Liste de stopwords en français
stopwords_fr = {
    "alors", "boutique", "site", "collection", "gamme", "découvrez", "explorez", "nettoyer", "nettoyez", "entretien", "entretenir", "au", "aucuns", "aussi", "autre", "avant", "avec", "avoir", "bon", 
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
    st.title("Analyse de similarité de contenu Web")
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

            # Ajouter un bouton pour lancer l'analyse
            if st.button("Lancer l'analyse"):
                # Extraire et nettoyer le contenu des URLs
                contents = [extract_and_clean_content(url) for url in urls]
                embeddings = [get_embeddings(content) for content in contents if content]

                if embeddings:
                    # Calculer la similarité cosinus
                    similarity_matrix = calculate_similarity(embeddings)

                    if similarity_matrix is not None:
                        # Sélecteur d'URL et curseur pour le nombre de résultats
                        selected_url = st.selectbox("Sélectionnez une URL", urls)
                        max_results = st.slider("Nombre d'URLs les plus proches à afficher", 1, len(urls), 5)

                        # Trouver l'index de l'URL sélectionnée
                        selected_index = urls.tolist().index(selected_url)

                        # Obtenir les similarités pour l'URL sélectionnée
                        selected_similarities = similarity_matrix[selected_index]

                        # Créer un DataFrame des similarités
                        similarity_df = pd.DataFrame({
                            'URL': urls,
                            'Similarité': selected_similarities
                        })

                        # Trier le DataFrame par similarité décroissante
                        similarity_df = similarity_df.sort_values(by='Similarité', ascending=False)

                        # Afficher le nombre de résultats spécifié par le curseur
                        st.dataframe(similarity_df.head(max_results))

                        # Télécharger le fichier CSV avec les résultats
                        csv = similarity_df.to_csv().encode('utf-8')
                        st.download_button(
                            label="Télécharger les résultats en CSV",
                            data=csv,
                            file_name='similarity_results.csv',
                            mime='text/csv'
                        )
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {e}")

# Assurez-vous que la fonction `app` est appelée ici
if __name__ == "__main__":
    app()
