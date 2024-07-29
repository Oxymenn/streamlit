import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import ast

def load_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1]
    if file_type == 'xlsx':
        df = pd.read_excel(uploaded_file, engine='openpyxl')
    elif file_type == 'csv':
        df = pd.read_csv(uploaded_file)
    return df

def preprocess_embeddings(df, embedding_col):
    # Convertir les chaînes de caractères en listes de nombres si nécessaire
    if isinstance(df[embedding_col].iloc[0], str):
        df[embedding_col] = df[embedding_col].apply(ast.literal_eval)
    return np.array(df[embedding_col].tolist())

def calculate_cosine_similarity(embeddings):
    similarities = cosine_similarity(embeddings)
    return similarities

def app():
    st.title("Analyse de Similarité Cosinus des URL")

    uploaded_file = st.file_uploader("Choisissez un fichier Excel ou CSV", type=["xlsx", "csv"])
    
    if uploaded_file:
        df = load_file(uploaded_file)
        
        st.write("Aperçu des données :")
        st.write(df.head())
        
        url_column = st.selectbox("Sélectionnez la colonne des URL", df.columns)
        embedding_column = st.selectbox("Sélectionnez la colonne des Embeddings", df.columns)
        
        if st.button("Calculer la similarité cosinus"):
            with st.spinner("Calcul de la similarité en cours..."):
                embeddings = preprocess_embeddings(df, embedding_column)
                similarities = calculate_cosine_similarity(embeddings)
                df['similarities'] = similarities.tolist()
                st.write("Calcul de la similarité terminé avec succès !")

            num_links = st.slider("Nombre de liens à analyser", min_value=1, max_value=20, value=5)
            selected_url = st.selectbox("Sélectionnez l'URL pour voir les liens similaires", df[url_column])

            if selected_url:
                selected_index = df[df[url_column] == selected_url].index[0]
                similarity_scores = similarities[selected_index]
                similar_indices = np.argsort(similarity_scores)[::-1][1:num_links+1]
                similar_urls = df[url_column].iloc[similar_indices].tolist()
                similar_scores = similarity_scores[similar_indices]
                
                st.write(f"Top {num_links} URLs les plus similaires à {selected_url} :")
                for url, score in zip(similar_urls, similar_scores):
                    st.write(f"{url} (Score: {score})")

if __name__ == "__main__":
    app()
