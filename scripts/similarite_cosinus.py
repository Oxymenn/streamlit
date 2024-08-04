import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import ast

def load_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1]
    if file_type == 'xlsx':
        # Charger toutes les feuilles dans un dictionnaire de DataFrames
        sheets_dict = pd.read_excel(uploaded_file, sheet_name=None, engine='openpyxl')
        return sheets_dict
    elif file_type == 'csv':
        df = pd.read_csv(uploaded_file)
        return {'Sheet1': df}  # Simuler une seule feuille pour les fichiers CSV
    return None

def preprocess_embeddings(df, embedding_col):
    # Convertir les chaînes de caractères en listes de nombres si nécessaire
    if isinstance(df[embedding_col].iloc[0], str):
        df[embedding_col] = df[embedding_col].apply(ast.literal_eval)
    return np.array(df[embedding_col].tolist())

def calculate_cosine_similarity(embeddings):
    similarities = cosine_similarity(embeddings)
    return similarities

def generate_similarity_table(df_main, url_col_embedded, df_secondary, url_col_depart, url_col_destination, similarities):
    similarity_data = []
    num_links = 5  # Fixer le nombre de liens similaires à 5
    for index, row in df_main.iterrows():
        similarity_scores = similarities[index]
        similar_indices = np.argsort(similarity_scores)[::-1]
        similar_urls = []
        count = 0
        for idx in similar_indices:
            if df_secondary[url_col_depart].iloc[idx] != row[url_col_embedded] and count < num_links:
                similar_urls.append(df_secondary[url_col_destination].iloc[idx])
                count += 1
        similarity_data.append([row[url_col_embedded]] + similar_urls)
    columns = ["URL embeddée"] + [f"URL similaire {i+1}" for i in range(num_links)]
    similarity_df = pd.DataFrame(similarity_data, columns=columns)
    return similarity_df

def app():
    st.title("Analyse de Similarité Cosinus des URL")
    uploaded_file = st.file_uploader("Choisissez un fichier Excel ou CSV", type=["xlsx", "csv"])

    if uploaded_file:
        # Charger le fichier et obtenir les noms des feuilles
        sheets_dict = load_file(uploaded_file)
        sheet_names = list(sheets_dict.keys())

        # Sélection de la feuille principale et secondaire
        main_sheet = st.selectbox("Sélectionner la feuille principale", sheet_names)
        secondary_sheet = st.selectbox("Sélectionner la feuille secondaire", sheet_names)

        df_main = sheets_dict[main_sheet]
        df_secondary = sheets_dict[secondary_sheet]

        st.write("Aperçu des données (feuille principale) :")
        st.write(df_main.head())
        st.write("Aperçu des données (feuille secondaire) :")
        st.write(df_secondary.head())

        # Sélection des colonnes pour la feuille principale
        embedding_column = st.selectbox("Sélectionnez la colonne des Embeddings", df_main.columns)
        url_column_embedded = st.selectbox("Sélectionner l'URL embeddée", df_main.columns)

        # Sélection des colonnes pour la feuille secondaire
        url_column_depart = st.selectbox("Sélectionner l'URL de départ", df_secondary.columns)
        url_column_destination = st.selectbox("Sélectionner l'URL de destination", df_secondary.columns)

        if st.button("Calculer la similarité cosinus"):
            with st.spinner("Calcul de la similarité en cours..."):
                embeddings_main = preprocess_embeddings(df_main, embedding_column)

                # Calculer les similarités pour les embeddings de la feuille principale
                similarities = calculate_cosine_similarity(embeddings_main)

                st.session_state.similarities = similarities
                st.session_state.df_main = df_main
                st.session_state.df_secondary = df_secondary
                st.session_state.url_column_embedded = url_column_embedded
                st.session_state.url_column_depart = url_column_depart
                st.session_state.url_column_destination = url_column_destination

                st.write("Calcul de la similarité terminé avec succès !")

    if 'similarities' in st.session_state:
        df_main = st.session_state.df_main
        df_secondary = st.session_state.df_secondary
        url_column_embedded = st.session_state.url_column_embedded
        url_column_depart = st.session_state.url_column_depart
        url_column_destination = st.session_state.url_column_destination
        similarities = st.session_state.similarities

        # Générer le tableau de similarité
        similarity_df = generate_similarity_table(df_main, url_column_embedded, df_secondary, url_column_depart, url_column_destination, similarities)
        st.write("Tableau de similarité :")
        st.write(similarity_df)

        # Concaténer les URLs similaires
        similarity_df['concatener'] = similarity_df.apply(
            lambda row: f"Lien 1 : {row['URL similaire 1']} ; Lien 2 : {row['URL similaire 2']} ; Lien 3 : {row['URL similaire 3']} ; Lien 4 : {row['URL similaire 4']} ; Lien 5 : {row['URL similaire 5']} ; ", axis=1
        )

        similarity_csv = similarity_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Télécharger le tableau de similarité en CSV", data=similarity_csv, file_name='similarity_table.csv', mime='text/csv')

if __name__ == "__main__":
    app()
