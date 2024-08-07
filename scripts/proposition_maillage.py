import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# Liste de stopwords en français (inchangée)
default_stopwords_fr = {
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

# Fonctions existantes inchangées
def extract_and_clean_content(url, exclude_classes, include_classes, stopwords):
    # ... (code inchangé)

def get_embeddings(text):
    # ... (code inchangé)

def calculate_similarity(embeddings):
    # ... (code inchangé)

def create_similarity_df(urls, similarity_matrix, selected_url, max_results):
    # ... (code inchangé)

def create_links_table(urls, similarity_matrix, max_results):
    # ... (code inchangé)

def app():
    st.title("Pages Similaires Sémantiquement - Woocommerce (Shoptimizer)")
    uploaded_file = st.file_uploader("Importer un fichier Excel contenant des URLs", type=["xlsx"])

    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names

        # Nouveau filtre pour sélectionner la feuille contenant les URLs à embedder
        urls_sheet = st.selectbox("Sélectionnez la feuille contenant les URLs à embedder", sheet_names)

        # Nouveau filtre pour sélectionner la feuille contenant le maillage interne existant
        maillage_sheet = st.selectbox("Sélectionnez la feuille contenant le maillage interne existant", sheet_names)

        # Lire les données des feuilles sélectionnées
        df_urls = pd.read_excel(uploaded_file, sheet_name=urls_sheet)
        df_maillage = pd.read_excel(uploaded_file, sheet_name=maillage_sheet)

        # Nouveau filtre pour sélectionner la colonne des URLs dans la feuille 1
        url_column = st.selectbox("Sélectionnez la colonne contenant les URLs à embedder", df_urls.columns)

        # Nouveaux filtres pour sélectionner les colonnes des URLs de départ et de destination
        url_depart_column = st.selectbox("Sélectionnez la colonne des URLs de départ", df_maillage.columns)
        url_destination_column = st.selectbox("Sélectionnez la colonne des URLs de destination", df_maillage.columns)

    # Reste du code existant
    exclude_classes = st.text_input("Classes HTML à exclure (séparées par des virgules)", "")
    exclude_classes = [cls.strip() for cls in exclude_classes.split(',')] if exclude_classes else []

    include_classes = st.text_input("Classes HTML à inclure exclusivement (séparées par des virgules)", "")
    include_classes = [cls.strip() for cls in include_classes.split(',')] if include_classes else []

    additional_stopwords = st.text_input("Stopwords supplémentaires à exclure (séparés par des virgules)", "")
    additional_stopwords = [word.strip().lower() for word in additional_stopwords.split(',')] if additional_stopwords else []

    stopwords = default_stopwords_fr.union(set(additional_stopwords))

    execute_button = st.button("Exécuter")

    if uploaded_file is not None and execute_button:
        try:
            urls = df_urls[url_column].dropna().unique()
            file_name = uploaded_file.name.rsplit('.', 1)[0]

            st.session_state['contents'] = [extract_and_clean_content(url, exclude_classes, include_classes, stopwords) for url in urls]
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
