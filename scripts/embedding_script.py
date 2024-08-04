import streamlit as st
import pandas as pd
import openai
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import re

# Définir une liste de stopwords en français
stopwords_fr = {
    "alors", "au", "aucuns", "aussi", "autre", "avant", "avec", "avoir", "bon", 
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

# Configure OpenAI API Key à partir de secret.toml
openai.api_key = st.secrets["api_key"]

# Fonction pour extraire et nettoyer le contenu HTML
def extract_and_clean_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find(class_='below-woocommerce-category').get_text(separator=" ", strip=True)

        # Nettoyage du texte
        content = re.sub(r'\s+', ' ', content)  # Nettoyer les espaces
        content = content.lower()  # Mettre en minuscules
        content = re.sub(r'[^\w\s]', '', content)  # Supprimer la ponctuation

        # Retirer les mots vides
        words = content.split()
        content = ' '.join([word for word in words if word not in stopwords_fr])

        return content
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du contenu de {url}: {e}")
        return None

# Fonction pour obtenir les embeddings d'un texte
def get_embeddings(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

# Fonction pour calculer la similarité cosinus
def calculate_similarity(embeddings):
    similarity_matrix = cosine_similarity(embeddings)
    return similarity_matrix

# Interface Streamlit
st.title("Analyse de similarité de contenu Web")
uploaded_file = st.file_uploader("Importer un fichier CSV ou Excel contenant des URLs", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Lire le fichier importé
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    urls = df['URL']  # Assurez-vous que le fichier a une colonne nommée 'URL'

    # Extraire et nettoyer le contenu des URLs
    contents = [extract_and_clean_content(url) for url in urls]
    embeddings = [get_embeddings(content) for content in contents if content]

    if embeddings:
        # Calculer la similarité cosinus
        similarity_matrix = calculate_similarity(embeddings)

        # Création d'un DataFrame pour l'affichage
        similarity_df = pd.DataFrame(similarity_matrix, columns=urls, index=urls)

        # Affichage du tableau interactif
        st.dataframe(similarity_df)

        # Télécharger le fichier CSV avec les résultats
        csv = similarity_df.to_csv().encode('utf-8')
        st.download_button(
            label="Télécharger les résultats en CSV",
            data=csv,
            file_name='similarity_results.csv',
            mime='text/csv'
        )
