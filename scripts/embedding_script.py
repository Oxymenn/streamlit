import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import inflect
import unidecode

# Liste de stopwords en français
STOPWORDS_FR = {
    'alors', 'au', 'aucuns', 'aussi', 'autre', 'avant', 'avec', 'avoir', 'bon', 'car', 'ce', 'cela',
    'ces', 'ceux', 'chaque', 'ci', 'comme', 'comment', 'dans', 'des', 'du', 'dedans', 'dehors', 'depuis',
    'devrait', 'doit', 'donc', 'dos', 'début', 'elle', 'elles', 'en', 'encore', 'essai', 'est', 'et', 'eu',
    'fait', 'faites', 'fois', 'font', 'force', 'haut', 'hors', 'ici', 'il', 'ils', 'je', 'juste', 'la', 'le',
    'les', 'leur', 'là', 'ma', 'maintenant', 'mais', 'mes', 'mine', 'moins', 'mon', 'mot', 'même', 'ni',
    'nommés', 'notre', 'nous', 'nouveaux', 'ou', 'où', 'par', 'parce', 'parole', 'pas', 'personnes', 'peut',
    'peu', 'pièce', 'plupart', 'pour', 'pourquoi', 'quand', 'que', 'quel', 'quelle', 'quelles', 'quels',
    'qui', 'sa', 'sans', 'ses', 'seulement', 'si', 'sien', 'son', 'sont', 'sous', 'soyez', 'sujet', 'sur',
    'ta', 'tandis', 'tellement', 'tels', 'tes', 'ton', 'tous', 'tout', 'trop', 'très', 'tu', 'valeur', 'voie',
    'voient', 'vont', 'votre', 'vous', 'vu', 'ça', 'étaient', 'état', 'étions', 'été', 'être'
}

# Initialiser l'outil de singularisation
p = inflect.engine()

# Récupérer l'API Key à partir du fichier secrets.toml
OPENAI_API_KEY = st.secrets["api_key"]

# Fonction pour nettoyer le texte
def clean_text(text):
    # Conversion en minuscules
    text = text.lower()
    # Suppression des accents
    text = unidecode.unidecode(text)
    # Suppression des stopwords en français
    words = text.split()
    words = [word for word in words if word not in STOPWORDS_FR]
    # Mise au singulier
    words = [p.singular_noun(word) if p.singular_noun(word) else word for word in words]
    # Reconstruction du texte
    text = ' '.join(words)
    return text

# Fonction pour tronquer le texte à une limite de tokens approximative
def truncate_token_limit(text, limit=8000):
    words = text.split()
    token_count = 0
    truncated_text = ''
    for word in words:
        # Estimation grossière : 1 mot = 1.3 tokens en moyenne
        token_count += len(word) / 3
        if token_count > limit:
            break
        truncated_text += word + ' '
    return truncated_text

# Fonction pour récupérer et nettoyer le contenu HTML
def get_and_clean_html(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find_all(class_='below-woocommerce-category')
        text = ' '.join([element.get_text() for element in content])
        cleaned_text = clean_text(text)
        return truncate_token_limit(cleaned_text)
    except Exception as e:
        st.error(f"Erreur lors de la récupération du contenu pour l'URL {url}: {e}")
        return ""

# Fonction pour obtenir les embeddings
def get_embeddings(text):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "text-embedding-3-small",
        "input": text,
        "encoding_format": "float",
    }
    try:
        response = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=data)
        response.raise_for_status()
        embedding = response.json()["data"][0]["embedding"]
        return embedding
    except requests.exceptions.HTTPError as err:
        st.error(f"Erreur lors de la récupération des embeddings: {err}")
        return []

# Fonction principale de l'application
def main():
    # Titre de l'application
    st.title("Embedding d'URLs avec OpenAI")

    # Téléchargement du fichier
    uploaded_file = st.file_uploader("Choisissez un fichier CSV ou Excel", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Lire le fichier dans un DataFrame pandas
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Vérifier si le DataFrame est vide
        if df.empty:
            st.error("Le fichier téléchargé est vide ou n'a pas pu être lu correctement.")
        else:
            # Sélection de la colonne des URLs
            url_column = st.selectbox("Sélectionnez la colonne contenant les URLs", df.columns)

            # Préparer une colonne pour les embeddings
            df["Embeddings"] = np.nan

            # Processus d'embedding
            with st.spinner("Traitement en cours..."):
                for i, url in enumerate(df[url_column]):
                    st.write(f"Traitement de l'URL {i+1}/{len(df)}: {url}")
                    cleaned_text = get_and_clean_html(url)
                    if cleaned_text:
                        embedding = get_embeddings(cleaned_text)
                        df.at[i, "Embeddings"] = str(embedding)

            # Affichage du DataFrame
            st.write(df)

            # Téléchargement du fichier modifié
            def convert_df_to_csv(df):
                return df.to_csv(index=False).encode('utf-8')

            csv = convert_df_to_csv(df)
            st.download_button(
                label="Télécharger le fichier avec embeddings",
                data=csv,
                file_name='embedded_urls.csv',
                mime='text/csv',
            )

# Appeler la fonction principale
if __name__ == "__main__":
    main()
