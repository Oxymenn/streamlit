import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def app():
    st.title("Proximité Sémantique des URL")

    # Étape 1: Charger le fichier Excel
    uploaded_file = st.file_uploader("Importer un fichier Excel", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)

        # Étape 2: Laisser l'utilisateur sélectionner les colonnes des URL et des embeddings
        url_column = st.selectbox("Sélectionner la colonne des URL", df.columns)
        embedding_column = st.selectbox("Sélectionner la colonne des embeddings", df.columns)

        # Convertir les embeddings en numpy array
        df[embedding_column] = df[embedding_column].apply(lambda x: np.fromstring(x.strip('[]'), sep=' '))

        # Étape 3: Calculer la proximité sémantique entre les URL
        embeddings = np.stack(df[embedding_column].values)
        similarity_matrix = cosine_similarity(embeddings)

        # Étape 4: Filtrer pour une URL spécifique
        selected_url = st.selectbox("Sélectionner une URL", df[url_column])

        # Trouver l'indice de l'URL sélectionnée
        selected_index = df[df[url_column] == selected_url].index[0]

        # Calculer les similarités pour l'URL sélectionnée
        similarities = similarity_matrix[selected_index]

        # Étape 5: Afficher les URL les plus proches sémantiquement
        num_links = st.slider("Nombre de liens à afficher", min_value=1, max_value=len(df), value=5)

        # Obtenir les indices des URL les plus similaires en ordre décroissant
        similar_indices = similarities.argsort()[::-1][:num_links+1]
        similar_indices = similar_indices[similar_indices != selected_index]  # Exclure l'URL sélectionnée

        # Créer un DataFrame des résultats
        results = pd.DataFrame({
            "URL": df.iloc[similar_indices][url_column],
            "Proximité Sémantique": similarities[similar_indices]
        }).reset_index(drop=True)

        st.write("URLs les plus proches sémantiquement de l'URL sélectionnée:")
        st.dataframe(results)

if __name__ == "__main__":
    app()
