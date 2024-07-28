import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def load_excel_file():
    uploaded_file = st.file_uploader("Choisissez un fichier Excel", type="xlsx")
    if uploaded_file is not None:
        try:
            return pd.read_excel(uploaded_file, sheet_name=None)
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier Excel : {e}")
    return None

def safe_convert_embedding(embedding_str):
    try:
        return np.fromstring(embedding_str.strip('[]'), sep=',')
    except:
        st.warning(f"Impossible de convertir l'embedding : {embedding_str}")
        return np.array([])

def main():
    st.title("Audit de maillage interne sémantique")

    excel_data = load_excel_file()

    if excel_data is not None:
        st.subheader("Choisissez les feuilles contenant les données")
        main_sheet = st.selectbox("Choisissez la feuille contenant les données principales", options=list(excel_data.keys()))
        secondary_sheet = st.selectbox("Choisissez la feuille contenant les données secondaires", options=list(excel_data.keys()))

        main_df = excel_data[main_sheet]
        secondary_df = excel_data[secondary_sheet]

        st.subheader("Associez les colonnes")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            source_url_col = st.selectbox("Colonne des URL de départ", options=main_df.columns)
        with col2:
            dest_url_col = st.selectbox("Colonne des URL de destination", options=main_df.columns)
        with col3:
            anchor_col = st.selectbox("Colonne des ancres de liens", options=main_df.columns)
        with col4:
            url_col = st.selectbox("Colonne des URL", options=secondary_df.columns)
        with col5:
            embedding_col = st.selectbox("Colonne des embeddings", options=secondary_df.columns)

        min_links = st.number_input("Nombre minimum de liens pour une URL de destination", min_value=1, value=5)

        if st.button("Valider"):
            try:
                embedding_dict = dict(zip(secondary_df[url_col], secondary_df[embedding_col]))
                embedding_dict = {k: safe_convert_embedding(v) for k, v in embedding_dict.items()}
                
                results = analyze_internal_linking(main_df, embedding_dict, source_url_col, dest_url_col, anchor_col, min_links)
                
                st.subheader("Résultats de l'audit de maillage interne")
                st.write(results)
            except Exception as e:
                st.error(f"Une erreur s'est produite lors de l'analyse : {e}")

def analyze_internal_linking(df, embedding_dict, source_col, dest_col, anchor_col, min_links):
    urls = list(set(df[source_col].unique()) | set(df[dest_col].unique()))
    
    # Vérifier si tous les URLs ont des embeddings
    missing_embeddings = [url for url in urls if url not in embedding_dict]
    if missing_embeddings:
        st.warning(f"Embeddings manquants pour les URLs : {', '.join(missing_embeddings)}")
    
    # Utiliser un embedding par défaut pour les URLs manquantes
    default_embedding = np.zeros_like(next(iter(embedding_dict.values())))
    embeddings = np.array([embedding_dict.get(url, default_embedding) for url in urls])
    
    similarity_matrix = cosine_similarity(embeddings)
    url_to_index = {url: i for i, url in enumerate(urls)}

    results = []
    for dest_url in df[dest_col].unique():
        existing_links = df[df[dest_col] == dest_url]
        num_links = len(existing_links)
        
        dest_index = url_to_index[dest_url]
        semantic_scores = similarity_matrix[dest_index]
        
        top_similar_urls = [urls[i] for i in semantic_scores.argsort()[::-1] if urls[i] != dest_url][:min_links]
        
        existing_source_urls = set(existing_links[source_col])
        links_to_add = [url for url in top_similar_urls if url not in existing_source_urls]
        links_to_remove = [url for url in existing_source_urls if url not in top_similar_urls]

        results.append({
            "URL de destination": dest_url,
            "Nombre de liens existants": num_links,
            "Liens à ajouter": links_to_add,
            "Liens à supprimer": links_to_remove,
            "Score de maillage interne": (len(set(existing_source_urls) & set(top_similar_urls)) / min_links) * 100
        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    main()
