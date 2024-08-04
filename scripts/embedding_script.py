import streamlit as st
import pandas as pd
import numpy as np
import re
import requests
from bs4 import BeautifulSoup
import concurrent.futures

# Liste des stopwords français (complète)
stopwords_fr = [
    "et", "boutique", "découvrez", "découvrir", "découvrer", "site", "explorez", "explorer", "produit", "ou", "mais", "donc", "or", "ni", "car", "à", "le", "la", "les", "un", "une", "des", "du", "de", "dans", "en",
    "par", "pour", "avec", "sans", "sous", "sur", "chez", "entre", "contre", "vers", "après", "avant", "comme", "lorsque"
]

def clean_text(text):
    # Convertir en minuscules
    text = text.lower()
    # Supprimer les caractères spéciaux et diviser en mots
    words = re.findall(r'\b\w+\b', text)
    # Filtrer les stopwords
    words = [word for word in words if word not in stopwords_fr]
    # Mettre les mots au singulier (simplifié)
    words = [word.rstrip('s') for word in words] 
    return ' '.join(words)

def extract_content_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extraire le texte de la classe 'below-woocommerce-category'
        content = soup.find(class_='below-woocommerce-category')
        return content.get_text(separator=' ') if content else ''
    except requests.RequestException as e:
        st.warning(f"Erreur lors de l'extraction de l'URL {url}: {e}")
        return ''

def get_openai_embeddings(text, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "text-embedding-ada-002",
        "input": text,
        "encoding_format": "float"
    }
    for attempt in range(3):  # Réessayer jusqu'à 3 fois en cas d'échec
        response = requests.post('https://api.openai.com/v1/embeddings', headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['data'][0]['embedding']
        else:
            st.warning(f"Tentative {attempt + 1} échouée. Réessai...")
    st.error("Erreur lors de la récupération des embeddings depuis l'API OpenAI après plusieurs tentatives")
    return None

def generate_embeddings(texts, api_key):
    embeddings = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_text = {executor.submit(get_openai_embeddings, clean_text(text), api_key): text for text in texts}
        for future in concurrent.futures.as_completed(future_to_text):
            embedding = future.result()
            if embedding:
                # Convertir l'embedding en chaîne de caractères
                embeddings.append(','.join(map(str, embedding)))
            else:
                # Placeholder pour les échecs d'API
                embeddings.append(','.join(['0']*768))
    return embeddings

def app():
    st.title("Transformer le contenu de vos URLs en Embeddings")

    # Lire la clé API depuis les secrets
    try:
        api_key = st.secrets["api_key"]
    except KeyError:
        st.error("Clé API OpenAI manquante dans les secrets. Veuillez la définir dans les paramètres de votre application Streamlit.")
        return

    uploaded_file = st.file_uploader("Choisissez un fichier Excel ou CSV", type=["xlsx", "csv"])
    
    if uploaded_file:
        file_type = uploaded_file.name.split('.')[-1]
        
        if file_type == 'xlsx':
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif file_type == 'csv':
            df = pd.read_csv(uploaded_file)
        
        st.write("Aperçu des données :")
        st.write(df.head())
        
        url_column = st.selectbox("Sélectionnez la colonne des URL", df.columns)

        if st.button("Générer les Embeddings"):
            if api_key:
                with st.spinner("Extraction et génération des embeddings en cours..."):
                    # Extraire le contenu pertinent de chaque URL
                    texts = [extract_content_from_url(url) for url in df[url_column].tolist()]
                    # Générer les embeddings
                    embeddings = generate_embeddings(texts, api_key)
                    
                    # Ajouter les embeddings en tant que nouvelle colonne
                    df['Embeddings'] = embeddings
                    
                    st.write("Embeddings générés avec succès !")
                    st.write(df.head())

                st.download_button(label="Télécharger le fichier avec Embeddings",
                                   data=df.to_csv(index=False).encode('utf-8'),
                                   file_name='embeddings_output.csv',
                                   mime='text/csv')
            else:
                st.error("Veuillez entrer votre clé API OpenAI")

if __name__ == "__main__":
    app()
