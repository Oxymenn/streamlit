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
st.title('Audit Sémantique')

# Téléchargement du fichier Excel
uploaded_file = st.file_uploader("Choisissez un fichier Excel", type="xlsx")

if uploaded_file is not None:
    try:
        # Lire le fichier Excel
        df = pd.read_excel(uploaded_file)
        st.write("Fichier Excel chargé avec succès.")

        # Afficher les colonnes disponibles
        st.write("Colonnes disponibles :", df.columns)

        # Sélection des colonnes des URL et des embeddings
        url_column = st.selectbox("Sélectionnez la colonne des URL", df.columns)
        embeddings_column = st.selectbox("Sélectionnez la colonne des embeddings", df.columns)

        if url_column and embeddings_column:
            try:
                # Extraire les URL et les embeddings
                urls = df[url_column]
                st.write("URLs extraites avec succès.")
                
                embeddings = df[embeddings_column].apply(eval)
                st.write("Embeddings extraits avec succès.")

                # Vérifier que les embeddings sont des listes de nombres
                if not all(isinstance(emb, list) and all(isinstance(x, (int, float)) for x in emb) for emb in embeddings):
                    st.error("Les embeddings doivent être des listes de nombres.")
                else:
                    embeddings = np.vstack(embeddings.values)
                    st.write("Embeddings convertis en tableau numpy avec succès.")

                    # Calculer la proximité sémantique
                    similarity_matrix = calculate_semantic_proximity(embeddings)
                    st.write("Matrice de similarité calculée avec succès.")

                    # Sélection d'une URL spécifique
                    selected_url = st.selectbox("Sélectionnez une URL pour trouver les URL similaires", urls)

                    # Curseur pour gérer le nombre de liens
                    num_links = st.slider("Nombre d'URL similaires à afficher", min_value=1, max_value=len(urls), value=5)

                    if selected_url:
                        # Trouver les URL les plus proches
                        similar_urls = find_most_similar_urls(selected_url, similarity_matrix, urls, n=num_links)
                        st.write("URLs similaires trouvées avec succès.")

                        # Afficher les résultats
                        st.write("Les URL les plus similaires à :", selected_url)
                        st.dataframe(similar_urls)
            except Exception as e:
                st.error(f"Erreur lors du traitement des données : {e}")
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")

if __name__ == "__main__":
    main()
