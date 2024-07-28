import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import streamlit as st

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
    selected_sheet1 = st.selectbox("Sélectionner la feuille pour les URLs source", sheet_names)
    selected_sheet2 = st.selectbox("Sélectionner la feuille pour les URLs destination", sheet_names)
    selected_sheet3 = st.selectbox("Sélectionner la feuille pour les URLs résultats", sheet_names)
    selected_sheet4 = st.selectbox("Sélectionner la feuille pour les embeddings", sheet_names)

    df_source = pd.read_excel(xls, sheet_name=selected_sheet1)
    df_destination = pd.read_excel(xls, sheet_name=selected_sheet2)
    df_results = pd.read_excel(xls, sheet_name=selected_sheet3)
    df_embeddings = pd.read_excel(xls, sheet_name=selected_sheet4)

    col_source = st.selectbox("Sélectionner la colonne pour les URLs source", df_source.columns)
    col_destination = st.selectbox("Sélectionner la colonne pour les URLs destination", df_destination.columns)
    col_results = st.selectbox("Sélectionner la colonne pour les URLs résultats", df_results.columns)
    col_embeddings = st.selectbox("Sélectionner la colonne pour les embeddings", df_embeddings.columns)

    return df_source[col_source], df_destination[col_destination], df_results[col_results], df_embeddings[col_embeddings]

def perform_audit(urls_source, urls_destination, urls_results, embeddings):
    try:
        # Convertir les embeddings en matrices
        embeddings_matrix = np.array(embeddings.tolist())

        # Calculer la similarité cosinus entre les embeddings
        similarity_matrix = cosine_similarity(embeddings_matrix)

        # Créer un DataFrame pour stocker les résultats
        results_df = pd.DataFrame({
            'URL Source': urls_source,
            'URL Destination': urls_destination,
            'Similarity Score': similarity_matrix.diagonal()
        })

        # Analyser le maillage interne existant et fournir des recommandations
        # (Cette partie peut être complexe et dépend de vos besoins spécifiques)

        return results_df

    except Exception as e:
        return f"Erreur lors de l'audit : {e}"

def app():
    st.title("Audit de Maillage Interne")

    # Upload du fichier Excel
    uploaded_file = st.file_uploader("Charger le fichier Excel", type="xlsx")

    if uploaded_file is not None:
        xls, sheet_names = load_excel_file(uploaded_file)
        if xls is not None and sheet_names is not None:
            urls_source, urls_destination, urls_results, embeddings = select_sheets_and_columns(xls, sheet_names)

            # Appeler le script d'audit
            if st.button("Exécuter l'audit"):
                results = perform_audit(
                    urls_source,
                    urls_destination,
                    urls_results,
                    embeddings
                )

                # Afficher les résultats de l'audit
                st.write("Résultats de l'audit :")
                st.write(results)
