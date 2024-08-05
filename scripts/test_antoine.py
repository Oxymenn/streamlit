import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

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

def extract_and_clean_content(url, exclude_classes, include_classes):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Supprimer les éléments avec les classes à exclure
        for class_name in exclude_classes:
            for element in soup.find_all(class_=class_name):
                element.decompose()
        
        # Si des classes à inclure sont spécifiées, extraire seulement ces éléments
        if include_classes:
            content = ' '.join([element.get_text(separator=" ", strip=True) for class_name in include_classes for element in soup.find_all(class_=class_name)])
        else:
            content = soup.body.get_text(separator=" ", strip=True)
        
        # Nettoyage du texte
        content = re.sub(r'\s+', ' ', content.lower())
        content = re.sub(r'[^\w\s]', '', content)
        return ' '.join([word for word in content.split() if word not in stopwords_fr])
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de l'accès à {url}: {e}")
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du contenu de {url}: {e}")
    return None

# Les autres fonctions restent inchangées...

def app():
    st.title("Pages Similaires Sémantiquement - Woocommerce (Shoptimizer)")
    uploaded_file = st.file_uploader("Importer un fichier CSV ou Excel contenant des URLs", type=["csv", "xlsx"])

    # Ajout d'un champ pour les classes à exclure
    exclude_classes = st.text_input("Classes HTML à exclure (séparées par des virgules)", "")
    exclude_classes = [cls.strip() for cls in exclude_classes.split(',')] if exclude_classes else []

    # Ajout d'un champ pour les classes à inclure exclusivement
    include_classes = st.text_input("Classes HTML à inclure exclusivement (séparées par des virgules)", "")
    include_classes = [cls.strip() for cls in include_classes.split(',')] if include_classes else []

    # Ajout du bouton Exécuter
    execute_button = st.button("Exécuter")

    if uploaded_file is not None and execute_button:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            file_name = uploaded_file.name.rsplit('.', 1)[0]
            column_option = st.selectbox("Sélectionnez la colonne contenant les URLs", df.columns)
            urls = df[column_option].dropna().unique()

            st.session_state['contents'] = [extract_and_clean_content(url, exclude_classes, include_classes) for url in urls]
            st.session_state['embeddings'] = [get_embeddings(content) for content in st.session_state['contents'] if content]
            st.session_state['similarity_matrix'] = calculate_similarity(st.session_state['embeddings'])
            st.session_state['urls'] = urls
            st.session_state['file_name'] = file_name

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {e}")

    if 'similarity_matrix' in st.session_state and st.session_state['similarity_matrix'] is not None:
        selected_url = st.selectbox("Sélectionnez une URL spécifique à filtrer", st.session_state['urls'])
        max_results = st.slider("Nombre d'URLs similaires à afficher (par ordre décroissant)", 1, len(st.session_state['urls']) - 1, 5)

        similarity_df = create_similarity_df(st.session_state['urls'], st.session_state['similarity_matrix'], selected_url, max_results)
        st.dataframe(similarity_df)

        csv = similarity_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Télécharger les urls similaires à l'url filtrée (CSV)",
            data=csv,
            file_name=f'urls_similaires-{st.session_state["file_name"]}.csv',
            mime='text/csv'
        )

        links_df = create_links_table(st.session_state['urls'], st.session_state['similarity_matrix'], max_results)
        st.dataframe(links_df)

        csv_links = links_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Télécharger le tableau du maillage interne (CSV)",
            data=csv_links,
            file_name=f'maillage_interne-{st.session_state["file_name"]}.csv',
            mime='text/csv'
        )

if __name__ == "__main__":
    app()
