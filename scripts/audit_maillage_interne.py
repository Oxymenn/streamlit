import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import plotly.graph_objects as go
import altair as alt

def load_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1]
    if file_type == 'xlsx':
        df = pd.read_excel(uploaded_file, engine='openpyxl')
    elif file_type == 'csv':
        df = pd.read_csv(uploaded_file)
    return df

def preprocess_embeddings(df, embedding_col):
    if isinstance(df[embedding_col].iloc[0], str):
        df[embedding_col] = df[embedding_col].apply(eval)
    return np.array(df[embedding_col].tolist())

def calculate_cosine_similarity(embeddings):
    return cosine_similarity(embeddings)

def calculate_internal_link_metrics(df, url_column, destination_column, min_links):
    if url_column not in df.columns or destination_column not in df.columns:
        st.error(f"Columns {url_column} or {destination_column} not found in DataFrame")
        return df
    df['existing_links'] = df.groupby(destination_column)[url_column].transform('count')
    df['links_to_keep'] = df['existing_links'].apply(lambda x: min(x, min_links))
    df['links_to_remove'] = df['existing_links'] - df['links_to_keep']
    df['links_to_add'] = df['links_to_keep'] - df['existing_links']
    df['links_to_replace'] = df[['links_to_remove', 'links_to_add']].max(axis=1)
    df['internal_link_score'] = df['links_to_keep'] / df['existing_links'] * 100
    return df

def create_gauge_chart(value, title, min_val=0, max_val=100):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={'axis': {'range': [min_val, max_val]},
               'bar': {'color': "blue"},
               'steps': [
                   {'range': [0, 20], 'color': "red"},
                   {'range': [20, 40], 'color': "orange"},
                   {'range': [40, 60], 'color': "yellow"},
                   {'range': [60, 80], 'color': "lightgreen"},
                   {'range': [80, 100], 'color': "green"}]}))
    fig.update_layout(width=450, height=300, margin=dict(l=20, r=20, t=40, b=40))
    return fig

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
                
                df = calculate_internal_link_metrics(df, url_column, destination_column, min_links)
                
                st.session_state.df = df
                st.session_state.url_column = url_column
                st.session_state.destination_column = destination_column
                st.session_state.embedding_column = embedding_column
                st.session_state.anchor_column = anchor_column
                st.session_state.min_links = min_links
                st.session_state.filtered_df = df.copy()
                st.write("Données chargées avec succès.")

    if 'df' in st.session_state:
        df = st.session_state.df
        url_column = st.session_state.url_column
        destination_column = st.session_state.destination_column
        embedding_column = st.session_state.embedding_column
        anchor_column = st.session_state.anchor_column
        min_links = st.session_state.min_links
        filtered_df = st.session_state.filtered_df
        
        st.subheader("Métriques de maillage interne pour chaque URL de destination :")
        st.write(df[[destination_column, 'existing_links', 'links_to_keep', 'links_to_remove', 'links_to_replace']])
        
        selected_url_type = st.radio("Sélectionnez le type d'URLs à filtrer :", ["Aucun filtre", "URLs de départ", "URLs de destination"])
        
        if selected_url_type == "URLs de départ":
            selected_urls = st.multiselect("Sélectionnez les URLs de départ :", df[url_column].unique().tolist())
        elif selected_url_type == "URLs de destination":
            selected_urls = st.multiselect("Sélectionnez les URLs de destination :", df[destination_column].unique().tolist())
        else:
            selected_urls = []

        if selected_urls:
            if selected_url_type == "URLs de départ":
                filtered_df = df[df[url_column].isin(selected_urls)]
            elif selected_url_type == "URLs de destination":
                filtered_df = df[df[destination_column].isin(selected_urls)]
            st.session_state.filtered_df = filtered_df
        else:
            st.session_state.filtered_df = df.copy()

        st.download_button(label="Télécharger les métriques de maillage interne",
                           data=st.session_state.filtered_df.to_csv(index=False).encode('utf-8'),
                           file_name='internal_link_metrics.csv',
                           mime='text/csv')

        filtered_df = st.session_state.filtered_df
        avg_internal_link_score = filtered_df['internal_link_score'].mean()
        replace_or_add_percentage = filtered_df['links_to_replace'].sum() / filtered_df['existing_links'].sum() * 100
        
        st.subheader("Scores de maillage interne")
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.plotly_chart(create_gauge_chart(avg_internal_link_score, "Score moyen de maillage interne (sur une base de 5 URL minimum)"), use_container_width=True)
        
        with right_col:
            st.plotly_chart(create_gauge_chart(replace_or_add_percentage, "Pourcentage de liens à remplacer et/ou à ajouter (sur une base de 5 URL minimum)"), use_container_width=True)

        st.subheader("Statistiques sur les ancres de lien")
        anchor_counts = filtered_df[anchor_column].value_counts().reset_index()
        anchor_counts.columns = [anchor_column, 'count']
        
        anchor_chart = alt.Chart(anchor_counts).mark_bar().encode(
            x=alt.X('count:Q', title='Nombre de fois utilisée'),
            y=alt.Y(f'{anchor_column}:N', title='Ancre', sort='-x')
        )
        st.altair_chart(anchor_chart, use_container_width=True)

if __name__ == "__main__":
    app()
