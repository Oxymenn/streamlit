import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def calculate_cosine_similarity(embeddings):
    similarity_matrix = cosine_similarity(embeddings)
    return similarity_matrix

def app():
    st.title("Audit Sémantique des URL")

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

        if st.button("Calculer la Proximité Sémantique"):
            with st.spinner("Calcul des similarités cosinus en cours..."):
                embeddings = np.stack(df[embedding_column].apply(eval).values)
                similarity_matrix = calculate_cosine_similarity(embeddings)
                
                df_similarity = pd.DataFrame(similarity_matrix, index=df[url_column], columns=df[url_column])
                st.write("Matrice de Similarité Cosinus :")
                st.write(df_similarity)

                selected_url = st.selectbox("Sélectionnez une URL pour voir les URL les plus proches", df[url_column])
                selected_index = df[df[url_column] == selected_url].index[0]
                similarities = similarity_matrix[selected_index]

                sorted_indices = np.argsort(-similarities)
                top_n = st.slider("Nombre de résultats à afficher", 1, len(df), 5)

                st.write(f"Top {top_n} URL proches sémantiquement de {selected_url}:")
                top_urls = df[url_column].iloc[sorted_indices[:top_n]]
                top_similarities = similarities[sorted_indices[:top_n]]
                results = pd.DataFrame({'URL': top_urls, 'Similarité': top_similarities})
                st.write(results)

if __name__ == "__main__":
    app()
