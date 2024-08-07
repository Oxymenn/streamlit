import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from io import BytesIO

# ... (Le reste du code reste inchangé jusqu'à la fonction create_links_table)

def analyze_existing_links(df_maillage, url_depart_column, url_destination_column, similarity_matrix, urls):
    analysis_results = []
    
    for _, row in df_maillage.iterrows():
        url_depart = row[url_depart_column]
        url_destination = row[url_destination_column]
        
        if url_depart in urls and url_destination in urls:
            depart_index = urls.tolist().index(url_depart)
            destination_index = urls.tolist().index(url_destination)
            similarity_score = similarity_matrix[depart_index][destination_index]
            
            if similarity_score >= 0.75:
                decision = "À garder"
            else:
                decision = "À supprimer"
            
            analysis_results.append({
                "URL de départ": url_depart,
                "URL de destination": url_destination,
                "Score de similarité": similarity_score,
                "Décision": decision
            })
        else:
            analysis_results.append({
                "URL de départ": url_depart,
                "URL de destination": url_destination,
                "Score de similarité": "N/A (URL non trouvée)",
                "Décision": "À vérifier manuellement"
            })
    
    return pd.DataFrame(analysis_results)

def app():
    st.title("Pages Similaires Sémantiquement - Woocommerce (Shoptimizer)")
    uploaded_file = st.file_uploader("Importer un fichier Excel contenant des URLs", type=["xlsx"])

    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names

        urls_sheet = st.selectbox("Sélectionnez la feuille contenant les URLs à embedder", sheet_names)
        maillage_sheet = st.selectbox("Sélectionnez la feuille contenant le maillage interne existant", sheet_names)

        df_urls = pd.read_excel(uploaded_file, sheet_name=urls_sheet)
        df_maillage = pd.read_excel(uploaded_file, sheet_name=maillage_sheet)

        url_column = st.selectbox("Sélectionnez la colonne contenant les URLs à embedder", df_urls.columns)
        url_depart_column = st.selectbox("Sélectionnez la colonne des URLs de départ", df_maillage.columns)
        url_destination_column = st.selectbox("Sélectionnez la colonne des URLs de destination", df_maillage.columns)

        # ... (Le reste du code reste inchangé jusqu'au bouton Exécuter)

        if execute_button:
            try:
                urls = df_urls[url_column].dropna().unique()
                file_name = uploaded_file.name.rsplit('.', 1)[0]

                st.session_state['contents'] = [extract_and_clean_content(url, exclude_classes, include_classes, stopwords) for url in urls]
                st.session_state['embeddings'] = [get_embeddings(content) for content in st.session_state['contents'] if content]
                st.session_state['similarity_matrix'] = calculate_similarity(st.session_state['embeddings'])
                st.session_state['urls'] = urls
                st.session_state['file_name'] = file_name

                # Analyse du maillage existant
                analysis_df = analyze_existing_links(df_maillage, url_depart_column, url_destination_column, st.session_state['similarity_matrix'], urls)
                
                # Ajout de la nouvelle feuille au fichier Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    xls.to_excel(writer, index=False, sheet_name='Original')
                    analysis_df.to_excel(writer, index=False, sheet_name='Analyse maillage existant')
                
                st.download_button(
                    label="Télécharger le fichier Excel avec l'analyse du maillage",
                    data=output.getvalue(),
                    file_name=f'analyse_maillage-{file_name}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")

        # ... (Le reste du code reste inchangé)

if __name__ == "__main__":
    app()
