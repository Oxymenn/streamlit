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
def extract_and_clean_content(url, include_class, exclude_class):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Utiliser la classe à inclure si elle est spécifiée
        if include_class:
            elements = soup.find_all(class_=include_class)
        else:
            elements = soup.find_all(class_='below-woocommerce-category')
        
        # Exclure les éléments avec la classe spécifiée
        if exclude_class:
            elements = [el for el in elements if exclude_class not in el.get('class', [])]
        
        if elements:
            content = ' '.join([element.get_text(separator=" ", strip=True) for element in elements])
        else:
            st.error(f"Éléments non trouvés dans l'URL: {url}")
            return None

        # Nettoyage du texte
        content = re.sub(r'\s+', ' ', content)
        content = content.lower()
        content = re.sub(r'[^\w\s]', '', content)

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

# Les autres fonctions restent inchangées

# Fonction principale de l'application
def app():
    st.title("Pages Similaires Sémantiquement - Woocommerce (Shoptimizer)")
    
    # Nouveaux filtres pour les classes HTML
    include_class = st.text_input("Classe HTML à inclure (laissez vide pour utiliser la classe par défaut)")
    exclude_class = st.text_input("Classe HTML à exclure (laissez vide pour ne rien exclure)")
    
    uploaded_file = st.file_uploader("Importer un fichier CSV ou Excel contenant des URLs", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Lire le fichier importé
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            file_name = uploaded_file.name.rsplit('.', 1)[0]
            column_option = st.selectbox("Sélectionnez la colonne contenant les URLs", df.columns)
            urls = df[column_option].dropna().unique()

            # Réinitialiser l'état de session si les filtres ont changé
            if 'last_include_class' not in st.session_state or st.session_state['last_include_class'] != include_class or \
               'last_exclude_class' not in st.session_state or st.session_state['last_exclude_class'] != exclude_class:
                st.session_state['contents'] = [extract_and_clean_content(url, include_class, exclude_class) for url in urls]
                st.session_state['embeddings'] = [get_embeddings(content) for content in st.session_state['contents'] if content]
                st.session_state['similarity_matrix'] = calculate_similarity(st.session_state['embeddings'])
                st.session_state['last_include_class'] = include_class
                st.session_state['last_exclude_class'] = exclude_class

            # Le reste du code reste inchangé

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {e}")

# Assurez-vous que la fonction `app` est appelée ici
if __name__ == "__main__":
    app()
