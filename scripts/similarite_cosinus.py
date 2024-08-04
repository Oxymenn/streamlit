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

def calculate_cosine_similarity(embedding_a, embedding_b):
    # Calculer la similarité cosinus entre deux embeddings
    similarity = cosine_similarity([embedding_a], [embedding_b])
    return similarity[0][0]

def evaluate_link_quality(similarity_score, threshold=0.75):
    # Déterminer si un lien est de qualité
    if similarity_score >= threshold:
        return "Qualité"
    else:
        return "Mauvaise qualité"

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

def generate_link_analysis(df_main, url_col_embedded, embeddings_main, df_secondary, url_col_depart, url_col_destination):
    results = []
    for index, row in df_secondary.iterrows():
        url_depart = row[url_col_depart]
        url_destination = row[url_col_destination]

        # Vérifier si l'URL de destination est dans la feuille principale
        if url_destination in df_main[url_col_embedded].values:
            # Obtenir les indices des URLs pour récupérer les embeddings
            index_dest = df_main[df_main[url_col_embedded] == url_destination].index[0]
            embedding_dest = embeddings_main[index_dest]

            # Obtenir l'indice de l'URL de départ pour les embeddings
            if url_depart in df_main[url_col_embedded].values:
                index_depart = df_main[df_main[url_col_embedded] == url_depart].index[0]
                embedding_depart = embeddings_main[index_depart]

                # Calculer le score de similarité entre l'URL de départ et l'URL de destination
                similarity_score = calculate_cosine_similarity(embedding_depart, embedding_dest)

                # Évaluer la qualité du lien
                link_quality = evaluate_link_quality(similarity_score)

                results.append({
                    "URL de départ": url_depart,
                    "URL de destination": url_destination,
                    "Score de similarité": similarity_score,
                    "Qualité du lien": link_quality
                })

    return pd.DataFrame(results)

def app():
    st.title("Audit du Maillage Interne des URLs")
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

        if st.button("Analyser les liens"):
            with st.spinner("Analyse en cours..."):
                embeddings_main = preprocess_embeddings(df_main, embedding_column)

                # Calculer les similarités pour les embeddings de la feuille principale
                similarities = calculate_cosine_similarity(embeddings_main)

                # Générer le tableau de similarité
                similarity_df = generate_similarity_table(df_main, url_column_embedded, similarities, num_links=5)
                st.write("Tableau de similarité :")
                st.write(similarity_df)

                # Générer le tableau d'analyse des liens
                link_analysis_df = generate_link_analysis(df_main, url_column_embedded, embeddings_main, df_secondary, url_column_depart, url_column_destination)
                st.write("Résultats de l'analyse des liens :")
                st.write(link_analysis_df)

                # Télécharger le tableau d'analyse des liens
                analysis_csv = link_analysis_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Télécharger le tableau d'analyse des liens en CSV", data=analysis_csv, file_name='link_analysis.csv', mime='text/csv')

if __name__ == "__main__":
    app()
