import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Fonction pour charger le fichier Excel
def load_excel(file):
    return pd.read_excel(file, sheet_name=None)

# Fonction pour générer le rapport
def generate_report(df, start_url_column, destination_url_column, min_links=5):
    # Exemple de logique pour générer le rapport
    report = df.groupby(destination_url_column).agg(
        Nombre_de_liens_existants=(start_url_column, 'count'),
        Nombre_de_liens_à_conserver=(start_url_column, lambda x: len(x)),
        Nombre_de_liens_à_retirer=(start_url_column, lambda x: 0),
        Nombre_de_liens_à_remplacer=(start_url_column, lambda x: max(0, min_links - len(x)))
    ).reset_index()
    return report

# Interface utilisateur
def app():
    st.title("Audit Sémantique")

    # Téléchargement du fichier Excel
    uploaded_file = st.file_uploader("Choisissez un fichier Excel", type="xlsx")

    if uploaded_file is not None:
        # Chargement du fichier Excel
        sheets = load_excel(uploaded_file)

        # Sélection des feuilles
        sheet_names = list(sheets.keys())
        main_sheet = st.selectbox("Choisissez la feuille contenant les données principales", sheet_names)
        secondary_sheet = st.selectbox("Choisissez la feuille contenant les données secondaires", sheet_names)

        # Sélection des colonnes
        main_df = sheets[main_sheet]
        secondary_df = sheets[secondary_sheet]

        all_columns = list(main_df.columns) + list(secondary_df.columns)
        start_url_column = st.selectbox("Colonne des URL de départ", all_columns)
        destination_url_column = st.selectbox("Colonne des URL de destination", all_columns)
        embeddings_column = st.selectbox("Colonne des embeddings", all_columns)
        anchor_links_column = st.selectbox("Colonne des ancre de liens", all_columns)

        # Nombre minimum de liens pour une URL de destination
        min_links = st.number_input("Nombre minimum de liens pour une URL de destination", min_value=1, value=5)

        # Génération du rapport
        report = generate_report(main_df, start_url_column, destination_url_column, min_links)

        # Affichage du rapport
        st.write("### Rapport 1")
        st.write(report)

        # Filtrage pour les graphiques
        start_urls = st.multiselect("Sélectionnez des URLs de départ", main_df[start_url_column].unique())
        destination_urls = st.multiselect("Sélectionnez des URLs de destination", main_df[destination_url_column].unique())

        # Génération des graphiques
        st.write("### Rapport 2")

        # Graphique 1: Score moyen de maillage interne
        st.write("Score moyen de maillage interne (sur une base de 5 liens internes minimum)")
        fig1 = px.bar(
            report,
            x=destination_url_column,
            y='Nombre_de_liens_à_conserver',
            labels={'Nombre_de_liens_à_conserver': 'Score moyen de maillage interne'},
            title='Score moyen de maillage interne',
            color_discrete_sequence=['blue']
        )
        fig1.update_yaxes(range=[0, 100])
        st.plotly_chart(fig1)

        # Graphique 2: Pourcentage de liens à remplacer et/ou à ajouter
        st.write("Pourcentage de liens à remplacer et/ou à ajouter (sur une base de 5 liens internes minimum)")
        report['Pourcentage_de_liens_à_remplacer'] = (report['Nombre_de_liens_à_remplacer'] / report['Nombre_de_liens_existants']) * 100
        fig2 = px.bar(
            report,
            x=destination_url_column,
            y='Pourcentage_de_liens_à_remplacer',
            labels={'Pourcentage_de_liens_à_remplacer': 'Pourcentage de liens à remplacer et/ou à ajouter'},
            title='Pourcentage de liens à remplacer et/ou à ajouter',
            color_discrete_sequence=['red']
        )
        fig2.update_yaxes(range=[0, 100])
        st.plotly_chart(fig2)
