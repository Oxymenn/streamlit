import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import altair as alt

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
        df[embedding_col] = df[embedding_col].apply(eval)
    return np.array(df[embedding_col].tolist())

def calculate_cosine_similarity(embeddings):
    return cosine_similarity(embeddings)

def app():
    st.title("Audit de maillage interne")

    uploaded_file = st.file_uploader("Choisissez un fichier Excel ou CSV", type=["xlsx", "csv"])
    
    if uploaded_file:
        df = load_file(uploaded_file)
        
        st.write("Aperçu des données :")
        st.write(df.head())
        
        url_column = st.selectbox("Sélectionnez la colonne des URL de départ", df.columns)
        destination_column = st.selectbox("Sélectionnez la colonne des URL de destination", df.columns)
        embedding_column = st.selectbox("Sélectionnez la colonne des Embeddings", df.columns)
        anchor_column = st.selectbox("Sélectionnez la colonne des ancres de liens", df.columns)
        
        min_links = st.number_input("Nombre minimum de liens pour une URL de destination", min_value=1, value=5)
        
        if st.button("Valider"):
            with st.spinner("Calcul de la similarité en cours..."):
                embeddings = preprocess_embeddings(df, embedding_column)
                similarities = calculate_cosine_similarity(embeddings)
                df["similarities"] = similarities.tolist()
                st.session_state.df = df
                st.session_state.url_column = url_column
                st.session_state.destination_column = destination_column
                st.session_state.embedding_column = embedding_column
                st.session_state.anchor_column = anchor_column
                st.session_state.min_links = min_links
                st.write("Données chargées avec succès.")

    if 'df' in st.session_state:
        df = st.session_state.df
        url_column = st.session_state.url_column
        destination_column = st.session_state.destination_column
        embedding_column = st.session_state.embedding_column
        anchor_column = st.session_state.anchor_column
        min_links = st.session_state.min_links
        
        # Calcul des métriques de maillage interne
        df['existing_links'] = df.groupby(destination_column)[url_column].transform('count')
        df['links_to_keep'] = df['existing_links'].apply(lambda x: min(x, min_links))
        df['links_to_remove'] = df['existing_links'] - df['links_to_keep']
        df['links_to_add'] = df['links_to_keep'] - df['existing_links']
        df['links_to_replace'] = df[['links_to_remove', 'links_to_add']].max(axis=1)
        
        # Calcul des scores
        df['internal_link_score'] = df['links_to_keep'] / df['existing_links'] * 100
        avg_internal_link_score = df['internal_link_score'].mean()
        replace_or_add_percentage = df['links_to_replace'].sum() / df['existing_links'].sum() * 100
        
        st.subheader("Métriques de maillage interne pour chaque URL de destination :")
        st.write(df[[destination_column, 'existing_links', 'links_to_keep', 'links_to_remove', 'links_to_replace']])

        st.download_button(label="Télécharger les métriques de maillage interne",
                           data=df.to_csv(index=False).encode('utf-8'),
                           file_name='internal_link_metrics.csv',
                           mime='text/csv')
        
        st.subheader("Scores de maillage interne")
        st.write(f"Score moyen de maillage interne (sur une base de 5 URL minimum) : {avg_internal_link_score:.2f}")
        st.write(f"Pourcentage de liens à remplacer et/ou à ajouter (sur une base de 5 URL minimum) : {replace_or_add_percentage:.2f}")
        
        # Graphiques
        st.subheader("Graphiques des scores")
        score_chart = alt.Chart(pd.DataFrame({'score': [avg_internal_link_score]})).mark_arc(innerRadius=50).encode(
            theta=alt.datum('score'),
            color=alt.value('blue')
        )
        st.altair_chart(score_chart, use_container_width=True)
        
        percentage_chart = alt.Chart(pd.DataFrame({'percentage': [replace_or_add_percentage]})).mark_arc(innerRadius=50).encode(
            theta=alt.datum('percentage'),
            color=alt.value('green')
        )
        st.altair_chart(percentage_chart, use_container_width=True)
        
        # Statistiques sur les ancres de lien
        st.subheader("Statistiques sur les ancres de lien")
        anchor_counts = df[anchor_column].value_counts().reset_index()
        anchor_counts.columns = [anchor_column, 'count']
        
        anchor_chart = alt.Chart(anchor_counts).mark_bar().encode(
            x=alt.X('count:Q', title='Nombre de fois utilisée'),
            y=alt.Y(f'{anchor_column}:N', title='Ancre', sort='-x')
        )
        st.altair_chart(anchor_chart, use_container_width=True)

if __name__ == "__main__":
    app()
