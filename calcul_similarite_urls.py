import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import openai
import os

# Charger la clé API OpenAI à partir des variables d'environnement
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_embeddings(text, model="text-embedding-ada-002"):
    response = openai.Embedding.create(
        input=text,
        model=model
    )
    return response['data'][0]['embedding']

def calculate_cosine_similarity(embeddings):
    similarity_matrix = cosine_similarity(embeddings)
    return similarity_matrix

def calcul_similarite_urls():
    st.title("Audit de Proximité Sémantique des URL")

    uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        url_column = st.selectbox("Sélectionnez la colonne des URL", df.columns)
        if url_column:
            urls = df[url_column].tolist()
            embeddings = []
            with st.spinner("Génération des embeddings..."):
                for url in urls:
                    embedding = get_embeddings(url)
                    embeddings.append(embedding)
            embeddings = np.array(embeddings)
            with st.spinner("Calcul de la similarité cosinus..."):
                similarity_matrix = calculate_cosine_similarity(embeddings)
            similarity_df = pd.DataFrame(similarity_matrix, index=urls, columns=urls)
            st.write("Matrice de Similarité Cosinus")
            st.dataframe(similarity_df)
            def convert_df(df):
                return df.to_csv().encode('utf-8')
            csv = convert_df(similarity_df)
            st.download_button(
                label="Télécharger la matrice de similarité en CSV",
                data=csv,
                file_name='similarity_matrix.csv',
                mime='text/csv',
            )

# Assurez-vous de l'appeler correctement dans main.py
