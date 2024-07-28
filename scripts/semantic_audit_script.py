import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Fonction pour calculer la proximité sémantique
def calculate_semantic_proximity(embeddings):
    similarity_matrix = cosine_similarity(embeddings)
    return similarity_matrix

# Fonction pour trouver les URL les plus proches
def find_most_similar_urls(url, similarity_matrix, urls, n=5):
    url_index = urls[urls == url].index[0]
    similarity_scores = similarity_matrix[url_index]
    most_similar_indices = similarity_scores.argsort()[::-1][1:n+1]
    most_similar_urls = urls.iloc[most_similar_indices]
    most_similar_scores = similarity_scores[most_similar_indices]
    return pd.DataFrame({'URL': most_similar_urls, 'Similarity Score': most_similar_scores})

# Interface utilisateur
st.title('Semantic Audit')

# Téléchargement du fichier Excel
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    # Lire le fichier Excel
    df = pd.read_excel(uploaded_file)

    # Afficher les colonnes disponibles
    st.write("Available columns:", df.columns)

    # Sélection des colonnes des URL et des embeddings
    url_column = st.selectbox("Select the URL column", df.columns)
    embeddings_column = st.selectbox("Select the embeddings column", df.columns)

    if url_column and embeddings_column:
        # Extraire les URL et les embeddings
        urls = df[url_column]
        embeddings = df[embeddings_column].apply(eval)

        # Vérifier que les embeddings sont des listes de nombres
        if not all(isinstance(emb, list) and all(isinstance(x, (int, float)) for x in emb) for emb in embeddings):
            st.error("Embeddings must be lists of numbers.")
        else:
            embeddings = np.vstack(embeddings.values)

            # Calculer la proximité sémantique
            similarity_matrix = calculate_semantic_proximity(embeddings)

            # Sélection d'une URL spécifique
            selected_url = st.selectbox("Select a URL to find similar URLs", urls)

            # Curseur pour gérer le nombre de liens
            num_links = st.slider("Number of similar URLs to display", min_value=1, max_value=len(urls), value=5)

            if selected_url:
                # Trouver les URL les plus proches
                similar_urls = find_most_similar_urls(selected_url, similarity_matrix, urls, n=num_links)

                # Afficher les résultats
                st.write("Most similar URLs to:", selected_url)
                st.dataframe(similar_urls)
