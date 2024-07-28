import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def preprocess_embeddings(embedding_str):
    return np.array([float(x) for x in embedding_str.strip('[]').split()])

def calculate_internal_link_score(df, url_column, embedding_column, anchor_column, min_links):
    df[embedding_column] = df[embedding_column].apply(preprocess_embeddings)
    embeddings = np.stack(df[embedding_column].values)
    similarity_matrix = cosine_similarity(embeddings)
    
    # Initialiser les colonnes pour le score et le nombre de liens à ajouter/retirer
    df['score_maillage'] = 0
    df['liens_existants'] = 0
    df['liens_à_conserver'] = 0
    df['liens_à_ajouter'] = 0
    df['liens_à_remplacer'] = 0
    
    for i, url in enumerate(df[url_column]):
        similarities = similarity_matrix[i]
        similar_indices = similarities.argsort()[::-1][1:]  # Exclure soi-même
        similar_urls = df.iloc[similar_indices][url_column]
        similar_scores = similarities[similar_indices]

        existing_links = len(similar_urls)
        df.at[i, 'liens_existants'] = existing_links

        links_to_keep = min(existing_links, min_links)
        df.at[i, 'liens_à_conserver'] = links_to_keep

        links_to_add = max(0, min_links - existing_links)
        df.at[i, 'liens_à_ajouter'] = links_to_add

        links_to_replace = max(0, existing_links - links_to_keep)
        df.at[i, 'liens_à_remplacer'] = links_to_replace

        internal_link_score = (links_to_keep + links_to_add - links_to_replace) / min_links * 100
        df.at[i, 'score_maillage'] = internal_link_score

    return df

def app():
    st.title("Proximité Sémantique des URL")

    # Charger le fichier Excel
    uploaded_file = st.file_uploader("Importer un fichier Excel", type=["xlsx"])

    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
        sheet_name = st.selectbox("Sélectionner la feuille", xls.sheet_names)
        df = pd.read_excel(xls, sheet_name)

        # Sélectionner les colonnes
        url_column = st.selectbox("Sélectionner la colonne des URL", df.columns)
        embedding_column = st.selectbox("Sélectionner la colonne des embeddings", df.columns)
        anchor_column = st.selectbox("Sélectionner la colonne des ancres de liens", df.columns)

        # Définir le nombre minimum de liens
        min_links = st.slider("Nombre minimum de liens", min_value=1, max_value=20, value=5)
        
        if st.button("Calculer le score de maillage interne"):
            result_df = calculate_internal_link_score(df, url_column, embedding_column, anchor_column, min_links)
            
            st.write("Résultats de l'analyse:")
            st.dataframe(result_df)
            
            st.download_button(
                label="Télécharger le fichier de résultats",
                data=result_df.to_csv(index=False).encode('utf-8'),
                file_name="resultat_maillage_interne.csv",
                mime="text/csv"
            )

            # Filtrer pour une URL spécifique
            selected_url = st.selectbox("Sélectionner une URL pour voir les détails", df[url_column])

            # Afficher les détails pour l'URL sélectionnée
            if selected_url:
                selected_index = df[df[url_column] == selected_url].index[0]
                st.write("Détails pour l'URL sélectionnée:")
                st.write(result_df.loc[selected_index])

                num_links = st.slider("Nombre de liens à afficher", min_value=1, max_value=len(df), value=5)
                
                # Obtenir les indices des URL les plus similaires en ordre décroissant
                similarities = cosine_similarity([df.at[selected_index, embedding_column]], embeddings).flatten()
                similar_indices = similarities.argsort()[::-1][1:num_links+1]  # Exclure soi-même
                similar_urls = df.iloc[similar_indices][url_column]
                similar_scores = similarities[similar_indices]

                details_df = pd.DataFrame({
                    "URL": similar_urls,
                    "Proximité Sémantique": similar_scores
                })

                st.write("URLs les plus proches sémantiquement de l'URL sélectionnée:")
                st.dataframe(details_df)

if __name__ == "__main__":
    app()
