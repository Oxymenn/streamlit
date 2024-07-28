import streamlit as st
import pandas as pd
import numpy as np
import openai
import re
import os

# Récupérer la clé API OpenAI depuis les secrets Streamlit
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Charger les stopwords français depuis le fichier local
stopwords_path = os.path.join(os.path.dirname(__file__), '../stopwords_fr.txt')
with open(stopwords_path, 'r', encoding='utf-8') as f:
    stopwords_fr = set(f.read().splitlines())

def clean_text(text):
    # Convertir en minuscules
    text = text.lower()
    # Supprimer les caractères spéciaux et diviser en mots
    words = re.findall(r'\b\w+\b', text)
    # Filtrer les stopwords
    words = [word for word in words if word not in stopwords_fr]
    return ' '.join(words)

def get_embedding(text, model="text-embedding-3-small"):
    response = openai.Embedding.create(input=[text], model=model)
    embedding = response['data'][0]['embedding']
    return embedding

def generate_embeddings(texts):
    cleaned_texts = [clean_text(text) for text in texts]
    embeddings = []
    for text in cleaned_texts:
        embedding = get_embedding(text)
        embeddings.append(embedding)
    return embeddings

def app():
    st.title("Génération des Embeddings pour un site E-commerce")

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
        embedding_column = st.selectbox("Sélectionnez la colonne pour les Embeddings", df.columns)

        if st.button("Générer les Embeddings"):
            with st.spinner("Génération des embeddings en cours..."):
                texts = df[url_column].tolist()
                embeddings = generate_embeddings(texts)
                
                df[embedding_column] = embeddings
                st.write("Embeddings générés avec succès !")
                st.write(df.head())

            st.download_button(label="Télécharger le fichier avec Embeddings",
                               data=df.to_csv(index=False).encode('utf-8'),
                               file_name='embeddings_output.csv',
                               mime='text/csv')

if __name__ == "__main__":
    app()
