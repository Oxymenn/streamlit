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
        similar_indices = np.argsort(similarity_scores)[::-1][1:num_links+1]
        similar_urls = df[url_column].iloc[similar_indices].tolist()
        similarity_data.append({
            "URL de départ": row[url_column],
            "URLs de destination": ", ".join(similar_urls)
        })
    similarity_df = pd.DataFrame(similarity_data)
    return similarity_df

def close_loop(df, url_column, similarity_df, similarities):
    for idx, row in similarity_df.iterrows():
        destination_urls = row["URLs de destination"].split(", ")
        last_url = destination_urls[-1]
        last_url_idx = df[df[url_column] == last_url].index[0]
        last_url_similarities = similarities[last_url_idx]
        
        # Vérifier et ajouter l'URL de départ si elle est parmi les plus proches
        original_url = row["URL de départ"]
        if original_url not in destination_urls:
            similar_indices = np.argsort(last_url_similarities)[::-1]
            for similar_idx in similar_indices:
                similar_url = df[url_column].iloc[similar_idx]
                if similar_url == original_url:
                    destination_urls[-1] = original_url
                    break
        similarity_df.at[idx, "URLs de destination"] = ", ".join(destination_urls)
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
                st.session_state.num_links = min(4, len(df))  # 4 liens au lieu de 5
                
                st.write("Calcul de la similarité terminé avec succès !")
                
                similarity_table = generate_similarity_table(df, url_column, similarities, st.session_state.num_links)
                similarity_table = close_loop(df, url_column, similarity_table, similarities)
                st.session_state.similarity_table = similarity_table
                
                st.write("Tableau des similarités :")
                st.write(similarity_table)
                
                csv = similarity_table.to_csv(index=False).encode('utf-8')
                st.download_button(label="Télécharger le tableau en CSV", data=csv, file_name='similarity_table.csv', mime='text/csv')
    
    if 'similarities' in st.session_state:
        df = st.session_state.df
        url_column = st.session_state.url_column
        similarities = st.session_state.similarities
        
        # Curseur pour le nombre de liens à analyser
        num_links = st.slider("Nombre de liens à analyser", min_value=1, max_value=len(df), value=st.session_state.get('num_links', 4))  # 4 liens au lieu de 5
        st.session_state.num_links = num_links
        
        # Sélecteur pour l'URL
        selected_url = st.selectbox("Sélectionnez l'URL pour voir les liens similaires", df[url_column])
        
        if selected_url:
            selected_index = df[df[url_column] == selected_url].index[0]
            similarity_scores = similarities[selected_index]
            similar_indices = np.argsort(similarity_scores)[::-1][1:num_links+1]
            similar_urls = df[url_column].iloc[similar_indices].tolist()
            similar_scores = similarity_scores[similar_indices]
            
            st.write(f"Top {num_links} URLs les plus similaires à {selected_url} :")
            for url, score in zip(similar_urls, similar_scores):
                st.write(f"{url} (Score: {score})")

if __name__ == "__main__":
    app()
