import streamlit as st
import pandas as pd
import scripts.semantic_audit_script as audit_script

# Titre de l'application
st.title("Audit de Maillage Interne")

# Upload du fichier Excel
uploaded_file = st.file_uploader("Charger le fichier Excel", type="xlsx")

if uploaded_file is not None:
    try:
        # Lire le fichier Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names

        # Vérifier si le fichier contient des feuilles
        if not sheet_names:
            st.error("Le fichier Excel ne contient aucune feuille.")
        else:
            # Sélection des feuilles
            selected_sheet1 = st.selectbox("Sélectionner la feuille pour les URLs source", sheet_names)
            selected_sheet2 = st.selectbox("Sélectionner la feuille pour les URLs destination", sheet_names)
            selected_sheet3 = st.selectbox("Sélectionner la feuille pour les URLs résultats", sheet_names)
            selected_sheet4 = st.selectbox("Sélectionner la feuille pour les embeddings", sheet_names)

            # Lire les feuilles sélectionnées
            df_source = pd.read_excel(uploaded_file, sheet_name=selected_sheet1)
            df_destination = pd.read_excel(uploaded_file, sheet_name=selected_sheet2)
            df_results = pd.read_excel(uploaded_file, sheet_name=selected_sheet3)
            df_embeddings = pd.read_excel(uploaded_file, sheet_name=selected_sheet4)

            # Sélection des colonnes
            col_source = st.selectbox("Sélectionner la colonne pour les URLs source", df_source.columns)
            col_destination = st.selectbox("Sélectionner la colonne pour les URLs destination", df_destination.columns)
            col_results = st.selectbox("Sélectionner la colonne pour les URLs résultats", df_results.columns)
            col_embeddings = st.selectbox("Sélectionner la colonne pour les embeddings", df_embeddings.columns)

            # Appeler le script d'audit
            if st.button("Exécuter l'audit"):
                results = audit_script.perform_audit(
                    df_source[col_source],
                    df_destination[col_destination],
                    df_results[col_results],
                    df_embeddings[col_embeddings]
                )

                # Afficher les résultats de l'audit
                st.write("Résultats de l'audit :")
                st.write(results)

    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier Excel : {e}")
