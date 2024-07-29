import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import plotly.graph_objects as go

def calculate_internal_link_metrics(df, url_start_column, url_end_column, min_links):
    # Calcul des métriques de maillage interne
    df['existing_links'] = df.groupby(url_end_column)[url_start_column].transform('count')
    df['links_to_keep'] = np.where(df['existing_links'] >= min_links, df['existing_links'], min_links)
    df['links_to_remove'] = np.where(df['existing_links'] > min_links, df['existing_links'] - min_links, 0)
    df['links_to_replace'] = np.where(df['existing_links'] < min_links, min_links - df['existing_links'], 0)
    return df

def display_gauge_chart(title, value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 12}},  # Réduction de la taille de la police
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': "darkblue"},
               'steps': [{'range': [0, 20], 'color': 'red'},
                         {'range': [20, 40], 'color': 'orange'},
                         {'range': [40, 60], 'color': 'yellow'},
                         {'range': [60, 80], 'color': 'lightgreen'},
                         {'range': [80, 100], 'color': 'green'}]}))
    return fig

def app():
    st.title("Audit de maillage interne")

    uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.write("Noms des colonnes disponibles :", df.columns.tolist())  # Affichage des noms des colonnes

        sheets = pd.ExcelFile(uploaded_file).sheet_names
        main_sheet = st.selectbox("Choisissez la feuille contenant les données principales", sheets)
        secondary_sheet = st.selectbox("Choisissez la feuille contenant les données secondaires", sheets)

        df_main = pd.read_excel(uploaded_file, sheet_name=main_sheet)
        df_secondary = pd.read_excel(uploaded_file, sheet_name=secondary_sheet)

        st.write("Données chargées avec succès.")

        # Sélection des colonnes pour les URLs de départ, destination, embeddings, et ancres de liens
        col1, col2 = st.columns(2)
        with col1:
            url_start_column = st.selectbox("Sélectionnez la colonne des URL de départ", df_main.columns)
        with col2:
            url_end_column = st.selectbox("Sélectionnez la colonne des URL de destination", df_main.columns)
        
        col3, col4 = st.columns(2)
        with col3:
            embedding_column = st.selectbox("Sélectionnez la colonne des Embeddings", df_main.columns)
        with col4:
            anchor_column = st.selectbox("Sélectionnez la colonne des ancres de liens", df_main.columns)
        
        min_links = st.number_input("Nombre minimum de liens pour une URL de destination (nécessaire pour le calcul des métriques de maillage interne)", min_value=1, value=5)
        
        if st.button("Valider"):
            with st.spinner("Calcul des métriques de maillage interne..."):
                df = calculate_internal_link_metrics(df_main, url_start_column, url_end_column, min_links)

                st.subheader("Métriques de maillage interne pour chaque URL de destination :")
                st.write(df[[url_end_column, 'existing_links', 'links_to_keep', 'links_to_remove', 'links_to_replace']])
                
                st.subheader("Filtrer par URL")
                col7, col8 = st.columns(2)
                with col7:
                    url_start_filter = st.selectbox("Sélectionnez des URLs de départ :", options=["Choose an option"] + list(df[url_start_column].unique()))
                with col8:
                    url_end_filter = st.selectbox("Sélectionnez des URLs de destination :", options=["Choose an option"] + list(df[url_end_column].unique()))

                if url_start_filter != "Choose an option":
                    df_filtered = df[df[url_start_column] == url_start_filter]
                elif url_end_filter != "Choose an option":
                    df_filtered = df[df[url_end_column] == url_end_filter]
                else:
                    df_filtered = df

                col5, col6 = st.columns(2)
                with col5:
                    st.plotly_chart(display_gauge_chart("Score moyen de maillage interne (sur une base de 5 URL minimum)", 43), use_container_width=True)
                with col6:
                    st.plotly_chart(display_gauge_chart("Pourcentage de liens à remplacer et/ou à ajouter (sur une base de 5 URL minimum)", 33.5), use_container_width=True)

                st.download_button(label="Télécharger les métriques de maillage interne", data=df.to_csv(index=False).encode('utf-8'), file_name='metrics_maillage_interne.csv', mime='text/csv')

                st.subheader(f"Détails des liens à remplacer et des meilleures URLs à inclure :")
                st.write(df_filtered[[url_end_column, 'links_to_replace']])

                # Affichage du nombre de fois où chaque ancre de lien est utilisée
                anchor_counts = df_filtered[anchor_column].value_counts().reset_index()
                anchor_counts.columns = ['Ancre', 'Nombre de fois utilisée']
                st.subheader("Nombre de fois où chaque ancre de lien est utilisée")
                st.bar_chart(anchor_counts.set_index('Ancre'))

                st.download_button(label="Télécharger les liens à remplacer", data=df_filtered.to_csv(index=False).encode('utf-8'), file_name='liens_a_remplacer.csv', mime='text/csv')

if __name__ == "__main__":
    app()
