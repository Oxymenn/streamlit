import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import ast
import openpyxl
from openpyxl.styles import PatternFill

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
        similar_scores = []
        count = 0
        for idx in similar_indices:
            if df[url_column].iloc[idx] != row[url_column] and count < num_links:
                similar_urls.append(df[url_column].iloc[idx])
                similar_scores.append(similarity_scores[idx])
                count += 1
        for url, score in zip(similar_urls, similar_scores):
            similarity_data.append({
                "URL de départ": row[url_column],
                "URL de destination": url,
                "Score de similarité": score
            })
    similarity_df = pd.DataFrame(similarity_data)
    similarity_df = similarity_df.sort_values(by="Score de similarité", ascending=False)
    return similarity_df

def apply_color(sheet, row, column, score):
    if 0.9 <= score <= 1:
        fill = PatternFill(start_color='149414', end_color='149414', fill_type='solid')
    elif 0.8 <= score < 0.9:
        fill = PatternFill(start_color='16B84E', end_color='16B84E', fill_type='solid')
    elif 0.75 <= score < 0.8:
        fill = PatternFill(start_color='B0F2B6', end_color='B0F2B6', fill_type='solid')
    elif 0.6 <= score < 0.75:
        fill = PatternFill(start_color='ff4c4c', end_color='ff4c4c', fill_type='solid')
    else:
        fill = PatternFill(start_color='e50000', end_color='e50000', fill_type='solid')
    sheet.cell(row=row, column=column).fill = fill

def save_to_excel(dataframe, file_name):
    dataframe.to_excel(file_name, index=False, engine='openpyxl')
    wb = openpyxl.load_workbook(file_name)
    sheet = wb.active

    for row in range(2, sheet.max_row + 1):
        score = sheet.cell(row=row, column=3).value
        if isinstance(score, (int, float)):
            apply_color(sheet, row, 3, score)

    wb.save(file_name)
    return file_name

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
                st.session_state.num_links = min(5, len(df))  # 5 liens au lieu de 4
                
                st.write("Calcul de la similarité terminé avec succès !")
                
                similarity_table = generate_similarity_table(df, url_column, similarities, st.session_state.num_links)
                st.session_state.similarity_table = similarity_table
                
                st.write("Tableau des similarités :")
                st.write(similarity_table)
                
                excel_file = save_to_excel(similarity_table, 'similarity_table.xlsx')
                with open(excel_file, 'rb') as f:
                    st.download_button(
                        label="Télécharger le tableau en Excel",
                        data=f,
                        file_name='similarity_table.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
    
    if 'similarities' in st.session_state:
        df = st.session_state.df
        url_column = st.session_state.url_column
        similarities = st.session_state.similarities
        
        # Curseur pour le nombre de liens à analyser
        num_links = st.slider("Nombre de liens à analyser", min_value=1, max_value=len(df), value=st.session_state.get('num_links', 5))  # 5 liens au lieu de 4
        st.session_state.num_links = num_links
        
        # Sélecteur pour l'URL
        selected_url = st.selectbox("Sélectionnez l'URL pour voir les liens similaires", df[url_column])
        
        if selected_url:
            selected_index = df[df[url_column] == selected_url].index[0]
            similarity_scores = similarities[selected_index]
            similar_indices = np.argsort(similarity_scores)[::-1]
            similar_urls = []
            similar_scores = []
            count = 0
            for idx in similar_indices:
                if df[url_column].iloc[idx] != selected_url and count < num_links:
                    similar_urls.append(df[url_column].iloc[idx])
                    similar_scores.append(similarity_scores[idx])
                    count += 1
            
            report_data = {
                "URL de référence": [selected_url] * len(similar_urls),
                "URLs similaires": similar_urls,
                "Scores de similarité": similar_scores
            }
            report_df = pd.DataFrame(report_data)
            report_df = report_df.sort_values(by="Scores de similarité", ascending=False)
            
            st.write(f"Top {num_links} URLs les plus similaires à {selected_url} :")
            st.write(report_df)
            
            excel_report_file = save_to_excel(report_df, f'similarity_report_{selected_url}.xlsx')
            with open(excel_report_file, 'rb') as f:
                st.download_button(
                    label="Télécharger le rapport en Excel",
                    data=f,
                    file_name=f'similarity_report_{selected_url}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

if __name__ == "__main__":
    app()
