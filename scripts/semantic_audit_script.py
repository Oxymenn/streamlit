import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import streamlit as st
import ast
import matplotlib.pyplot as plt

def load_excel_file(uploaded_file):
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        if not sheet_names:
            st.error("Le fichier Excel ne contient aucune feuille.")
            return None, None
        return xls, sheet_names
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier Excel : {e}")
        return None, None

def select_sheets_and_columns(xls, sheet_names):
    selected_sheet1 = st.selectbox("Sélectionner la feuille pour les liens internes", sheet_names)
    selected_sheet2 = st.selectbox("Sélectionner la feuille pour les embeddings", sheet_names)

    df_links = pd.read_excel(xls, sheet_name=selected_sheet1)
    df_embeddings = pd.read_excel(xls, sheet_name=selected_sheet2)

    col_source = st.selectbox("Sélectionner la colonne pour les URLs source", df_links.columns)
    col_destination = st.selectbox("Sélectionner la colonne pour les URLs destination", df_links.columns)
    col_embeddings = st.selectbox("Sélectionner la colonne pour les embeddings", df_embeddings.columns)

    return df_links[col_source], df_links[col_destination], df_embeddings[col_embeddings]

def align_dataframes(df1, df2, df3):
    min_length = min(len(df1), len(df2), len(df3))
    return df1[:min_length], df2[:min_length], df3[:min_length]

def convert_embeddings(embeddings):
    try:
        return embeddings.apply(ast.literal_eval)
    except Exception as e:
        st.error(f"Erreur lors de la conversion des embeddings : {e}")
        return embeddings

def calculate_internal_linking_score(urls_source, urls_destination, embeddings, min_links=5):
    try:
        # Aligner les DataFrames pour qu'ils aient le même nombre de lignes
        urls_source, urls_destination, embeddings = align_dataframes(urls_source, urls_destination, embeddings)

        # Convertir les embeddings en matrices
        embeddings = convert_embeddings(embeddings)
        embeddings_matrix = np.array(embeddings.tolist())

        # Calculer la similarité cosinus entre les embeddings
        similarity_matrix = cosine_similarity(embeddings_matrix)

        # Créer un DataFrame pour stocker les résultats
        results_df = pd.DataFrame({
            'URL Source': urls_source,
            'URL Destination': urls_destination,
            'Similarity Score': similarity_matrix.diagonal()
        })

        # Calculer le score de maillage interne
        results_df['Link Count'] = results_df.groupby('URL Destination')['URL Source'].transform('count')
        results_df['Minimum Links'] = min_links
        results_df['Links to Add/Replace'] = results_df['Link Count'].apply(lambda x: max(0, min_links - x))

        # Calculer le score global de maillage interne
        total_links = results_df['Link Count'].sum()
        total_urls = results_df['URL Destination'].nunique()
        global_score = (total_links / (total_urls * min_links)) * 100

        return results_df, global_score

    except Exception as e:
        return f"Erreur lors du calcul du score de maillage interne : {e}", None

def plot_gauge(score, title):
    fig, ax = plt.subplots()
    ax.axis('equal')
    ax.pie([score, 100-score], startangle=90, colors=['green', 'red'])
    ax.text(0, 0, f"{score:.2f}%", ha='center', va='center', fontsize=20)
    ax.set_title(title)
    st.pyplot(fig)

def app():
    st.title("Audit de Maillage Interne")

    # Upload du fichier Excel
    uploaded_file = st.file_uploader("Charger le fichier Excel", type="xlsx")

    if uploaded_file is not None:
        xls, sheet_names = load_excel_file(uploaded_file)
        if xls is not None and sheet_names is not None:
            urls_source, urls_destination, embeddings = select_sheets_and_columns(xls, sheet_names)

            # Définir le nombre minimum de liens
            min_links = st.number_input("Nombre minimum de liens par URL de destination", min_value=1, max_value=100, value=5)

            # Appeler le script d'audit
            if st.button("Exécuter l'audit"):
                results_df, global_score = calculate_internal_linking_score(
                    urls_source,
                    urls_destination,
                    embeddings,
                    min_links
                )

                # Afficher les résultats de l'audit
                st.write("Résultats de l'audit :")
                st.write(results_df)
                st.write(f"Score global de maillage interne : {global_score:.2f}%")

                # Afficher les recommandations spécifiques pour chaque URL
                st.write("Recommandations spécifiques pour chaque URL :")
                for url in results_df['URL Destination'].unique():
                    st.write(f"URL : {url}")
                    url_data = results_df[results_df['URL Destination'] == url]
                    st.write(f"Nombre de liens existants : {url_data['Link Count'].iloc[0]}")
                    st.write(f"Nombre de liens à ajouter/remplacer : {url_data['Links to Add/Replace'].iloc[0]}")
                    st.write("Liens à ajouter/remplacer :")
                    st.write(url_data[url_data['Links to Add/Replace'] > 0])

                # Afficher le score de maillage interne sous forme de jauge
                plot_gauge(global_score, "Score global de maillage interne")

                # Filtrer par URL spécifique
                selected_url = st.selectbox("Sélectionner une URL pour des recommandations spécifiques", results_df['URL Destination'].unique())
                if selected_url:
                    url_data = results_df[results_df['URL Destination'] == selected_url]
                    st.write(f"URL sélectionnée : {selected_url}")
                    st.write("Liens actuels les plus proches sémantiquement :")
                    st.write(url_data.sort_values(by='Similarity Score', ascending=False).head(min_links))
                    st.write("Liens actuels les moins proches sémantiquement :")
                    st.write(url_data.sort_values(by='Similarity Score', ascending=True).head(min_links))

                    # Afficher le score de maillage interne pour l'URL spécifique sous forme de jauge
                    url_score = (url_data['Link Count'].iloc[0] / min_links) * 100
                    plot_gauge(url_score, f"Score de maillage interne pour {selected_url}")
