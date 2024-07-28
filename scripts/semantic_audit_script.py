import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def preprocess_embeddings(embedding_str):
    try:
        if isinstance(embedding_str, str):
            embedding_str = embedding_str.strip('[]').replace('\n', ' ')
        return np.array([float(x) for x in embedding_str.split()])
    except ValueError as e:
        st.error(f"Error in embedding format: {e}")
        return np.zeros(300)  # Assuming embeddings are of size 300, adjust if needed

def calculate_semantic_similarity(df_embeddings, url_column, embedding_column):
    df_embeddings[embedding_column] = df_embeddings[embedding_column].apply(preprocess_embeddings)
    embeddings = np.stack(df_embeddings[embedding_column].values)
    similarity_matrix = cosine_similarity(embeddings)
    return similarity_matrix

def app():
    st.title("Proximité Sémantique des URL")

    uploaded_file = st.file_uploader("Importer un fichier Excel avec deux feuilles", type=["xlsx"])

    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)

        if len(xls.sheet_names) >= 2:
            df_links = pd.read_excel(xls, xls.sheet_names[0])
            df_embeddings = pd.read_excel(xls, xls.sheet_names[1])

            # Sélectionner les colonnes dans chaque feuille
            url_source_column = st.selectbox("Sélectionner la colonne des URLs source", df_links.columns)
            url_destination_column = st.selectbox("Sélectionner la colonne des URLs destination", df_links.columns)
            embedding_url_column = st.selectbox("Sélectionner la colonne des URLs dans les embeddings", df_embeddings.columns)
            embedding_column = st.selectbox("Sélectionner la colonne des embeddings", df_embeddings.columns)

            # Calculer la similarité sémantique
            similarity_matrix = calculate_semantic_similarity(df_embeddings, embedding_url_column, embedding_column)

            # Sélectionner une URL spécifique pour voir la similarité sémantique avec les autres URLs
            selected_url = st.selectbox("Sélectionner une URL pour voir les détails", df_embeddings[embedding_url_column])

            if selected_url:
                selected_index = df_embeddings[df_embeddings[embedding_url_column] == selected_url].index[0]
                st.write("Détails pour l'URL sélectionnée:")
                
                num_links = st.slider("Nombre de liens à afficher", min_value=1, max_value=len(df_embeddings), value=5)

                # Obtenir les indices des URL les plus similaires en ordre décroissant
                similarities = similarity_matrix[selected_index]
                similar_indices = similarities.argsort()[::-1][1:num_links+1]  # Exclure soi-même
                similar_urls = df_embeddings.iloc[similar_indices][embedding_url_column]
                similar_scores = similarities[similar_indices]

                details_df = pd.DataFrame({
                    "URL": similar_urls,
                    "Proximité Sémantique": similar_scores
                })

                st.write("URLs les plus proches sémantiquement de l'URL sélectionnée:")
                st.dataframe(details_df)

        else:
            st.error("Le fichier Excel doit contenir au moins deux feuilles.")
        
if __name__ == "__main__":
    app()
