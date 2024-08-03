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

def generate_similarity_table(df, url_column, similarities, num_links):
    similarity_data = []
    for index, row in df.iterrows():
        similarity_scores = similarities[index]
        similar_indices = np.argsort(similarity_scores)[::-1]
        similar_urls = []
        count = 0
        for idx in similar_indices:
            if df[url_column].iloc[idx] != row[url_column] and count < num_links:
                similar_urls.append(df[url_column].iloc[idx])
                count += 1
        similarity_data.append([row[url_column]] + similar_urls)
    columns = ["URL de départ"] + [f"URL similaire {i+1}" for i in range(num_links)]
    similarity_df = pd.DataFrame(similarity_data, columns=columns)
    return similarity_df

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

                st.session_state.similarities = similarities
                st.session_state.df = df
                st.session_state.url_column = url_column
                st.session_state.embedding_column = embedding_column
                st.session_state.num_links = 5  # 5 liens

                st.write("Calcul de la similarité terminé avec succès !")

    if 'similarities' in st.session_state:
        df = st.session_state.df
        url_column = st.session_state.url_column
        similarities = st.session_state.similarities

        # Curseur pour le nombre de liens à analyser
        num_links = st.slider("Nombre de liens à analyser", min_value=1, max_value=5, value=st.session_state.get('num_links', 5))  # 5 liens
        st.session_state.num_links = num_links

        # Générer le tableau de similarité
        similarity_df = generate_similarity_table(df, url_column, similarities, st.session_state.num_links)
        st.write("Tableau de similarité :")
        st.write(similarity_df)

        # Ajouter les colonnes G et H avec les valeurs calculées
        similarity_df['concatener'] = similarity_df.apply(lambda row: f"Lien 1 : {row['URL similaire 1']} ; Lien 2 : {row['URL similaire 2']} ; Lien 3 : {row['URL similaire 3']} ; Lien 4 : {row['URL similaire 4']} ; Lien 5 : {row['URL similaire 5']} ; ", axis=1)

        # Calculate the NB.SI by checking URL matches
        similarity_df['NB.SI'] = similarity_df.apply(lambda row: sum(row[1:6] == row['URL de départ']), axis=1)

        similarity_csv = similarity_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Télécharger le tableau de similarité en CSV", data=similarity_csv, file_name='similarity_table.csv', mime='text/csv')

if __name__ == "__main__":
    app()
