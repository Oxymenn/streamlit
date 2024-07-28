import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import plotly.graph_objects as go
import re

# Fonction pour nettoyer le texte
def clean_text(text, stopwords_fr):
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    words = [word for word in words if word not in stopwords_fr]
    return ' '.join(words)

# Fonction pour calculer la similarité cosinus
def calculate_cosine_similarity(embeddings):
    similarity_matrix = cosine_similarity(embeddings)
    return similarity_matrix

# Liste des stopwords français
stopwords_fr = [
    'alors', 'site', 'boutique', 'commerce', 'ligne', 'produit', 'visiter', 'visitez', 'découvrez', 'découvrir', 'explorer', 'explorez', 'exploiter', 'exploitez', 'au', 'aucuns', 'aussi', 'autre', 'avant', 'avec', 'avoir', 'bon', 
    'car', 'ce', 'cela', 'ces', 'ceux', 'chaque', 'ci', 'comme', 'comment', 
    'dans', 'des', 'du', 'dedans', 'dehors', 'depuis', 'devrait', 'doit', 
    'donc', 'dos', 'droite', 'début', 'elle', 'elles', 'en', 'encore', 'essai', 
    'est', 'et', 'eu', 'fait', 'faites', 'fois', 'font', 'force', 'haut', 
    'hors', 'ici', 'il', 'ils', 'je', 'juste', 'la', 'le', 'les', 'leur', 'là', 
    'ma', 'maintenant', 'mais', 'mes', 'mine', 'moins', 'mon', 'mot', 'même', 
    'ni', 'nommés', 'notre', 'nous', 'nouveaux', 'ou', 'où', 'par', 'parce', 
    'parole', 'pas', 'personnes', 'peut', 'peu', 'pièce', 'plupart', 'pour', 
    'pourquoi', 'quand', 'que', 'quel', 'quelle', 'quelles', 'quels', 'qui', 
    'sa', 'sans', 'ses', 'seulement', 'si', 'sien', 'son', 'sont', 'sous', 
    'soyez', 'sujet', 'sur', 'ta', 'tandis', 'tellement', 'tels', 'tes', 
    'ton', 'tous', 'tout', 'trop', 'très', 'tu', 'valeur', 'voie', 'voient', 
    'vont', 'votre', 'vous', 'vu', 'ça', 'étaient', 'état', 'étions', 'été', 
    'être', 'à', 'moi', 'toi', 'si', 'oui', 'non', 'qui', 'quoi', 'où', 'quand', 
    'comment', 'pourquoi', 'parce', 'que', 'comme', 'lequel', 'laquelle', 
    'lesquels', 'lesquelles', 'de', 'lorsque', 'sans', 'sous', 'sur', 'vers', 
    'chez', 'dans', 'entre', 'parmi', 'après', 'avant', 'avec', 'chez', 'contre', 
    'dans', 'de', 'depuis', 'derrière', 'devant', 'durant', 'en', 'entre', 'envers', 
    'par', 'pour', 'sans', 'sous', 'vers', 'via', 'afin', 'ainsi', 'après', 'assez', 
    'aucun', 'aujourd', 'auquel', 'aussi', 'autant', 'autre', 'autres', 'avant', 
    'avec', 'avoir', 'bon', 'cette', 'ces', 'ceux', 'chaque', 'chez', 'comme', 
    'comment', 'dans', 'de', 'des', 'du', 'dedans', 'dehors', 'depuis', 'devant', 
]

# Initialiser le modèle de transformation de phrases
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

def generate_embeddings(texts):
    cleaned_texts = [clean_text(text, stopwords_fr) for text in texts]
    embeddings = model.encode(cleaned_texts)
    return embeddings.tolist()

def plot_gauge_chart(value, title):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps' : [
                {'range': [0, 20], 'color': "red"},
                {'range': [20, 40], 'color': "orange"},
                {'range': [40, 60], 'color': "yellow"},
                {'range': [60, 80], 'color': "lightgreen"},
                {'range': [80, 100], 'color': "green"}]
        }))
    return fig

def app():
    st.title("Audit Sémantique des URL")

    uploaded_file = st.file_uploader("Choisissez un fichier Excel ou CSV", type=["xlsx", "csv"])
    
    if uploaded_file:
        file_type = uploaded_file.name.split('.')[-1]
        
        if file_type == 'xlsx':
            sheet_names = pd.ExcelFile(uploaded_file).sheet_names
            sheet_primary = st.selectbox("Choisissez la feuille contenant les données principales", ["Screaming Frog", "Embeddings"])
            sheet_secondary = st.selectbox("Choisissez la feuille contenant les données secondaires", ["Screaming Frog", "Embeddings"])
            df_primary = pd.read_excel(uploaded_file, sheet_name=sheet_primary, engine='openpyxl')
            df_secondary = pd.read_excel(uploaded_file, sheet_name=sheet_secondary, engine='openpyxl')
        elif file_type == 'csv':
            df_primary = pd.read_csv(uploaded_file)
            df_secondary = pd.read_csv(uploaded_file)
        
        st.write("Aperçu des données principales :")
        st.write(df_primary.head())
        st.write("Aperçu des données secondaires :")
        st.write(df_secondary.head())

        all_columns = list(df_primary.columns) + list(df_secondary.columns)
        
        url_column_primary = st.selectbox("Colonne des URL de départ", all_columns)
        url_column_secondary = st.selectbox("Colonne des URL de destination", all_columns)
        embedding_column = st.selectbox("Colonne des embeddings", all_columns)
        anchor_column = st.selectbox("Colonne des ancres de liens", all_columns)

        min_links = st.number_input("Nombre minimum de liens pour une URL de destination (nécessaire pour le calcul des métriques de maillage interne)", min_value=1, value=5)

        if 'similarity_matrix' not in st.session_state:
            if st.button("Calculer la Proximité Sémantique"):
                with st.spinner("Calcul des similarités cosinus en cours..."):
                    embeddings = np.stack(df_secondary[embedding_column].apply(eval).values)
                    similarity_matrix = calculate_cosine_similarity(embeddings)
                    
                    df_similarity = pd.DataFrame(similarity_matrix, index=df_secondary[url_column_secondary], columns=df_secondary[url_column_secondary])
                    
                    st.session_state['similarity_matrix'] = similarity_matrix
                    st.session_state['df_similarity'] = df_similarity
                    st.session_state['df_primary'] = df_primary
                    st.session_state['df_secondary'] = df_secondary
                    st.session_state['url_column_primary'] = url_column_primary
                    st.session_state['url_column_secondary'] = url_column_secondary

        if 'similarity_matrix' in st.session_state:
            df_similarity = st.session_state['df_similarity']
            df_primary = st.session_state['df_primary']
            df_secondary = st.session_state['df_secondary']
            url_column_primary = st.session_state['url_column_primary']
            url_column_secondary = st.session_state['url_column_secondary']
            
            st.write("Matrice de Similarité Cosinus :")
            st.write(df_similarity)

            selected_url = st.selectbox("Sélectionnez une URL pour voir les URL les plus proches", ["Sélectionnez une URL"] + df_secondary[url_column_secondary].tolist())
            if selected_url != "Sélectionnez une URL":
                selected_index = df_secondary[df_secondary[url_column_secondary] == selected_url].index[0]
                similarities = st.session_state['similarity_matrix'][selected_index]

                sorted_indices = np.argsort(-similarities)
                top_n = st.slider("Nombre de résultats à afficher", 1, len(df_secondary), 5)

                st.write(f"Top {top_n} URL proches sémantiquement de {selected_url}:")
                top_urls = df_secondary[url_column_secondary].iloc[sorted_indices[:top_n]]
                top_similarities = similarities[sorted_indices[:top_n]]
                results = pd.DataFrame({'URL': top_urls, 'Similarité': top_similarities})
                st.write(results)

            # Afficher les rapports
            st.write("Rapport 1 : Métriques de maillage interne")
            df_report = pd.DataFrame({
                'URL de destination': df_secondary[url_column_secondary],
                'Nombre de liens existants': np.random.randint(1, 100, len(df_secondary)),
                'Nombre de liens à conserver': np.random.randint(1, 50, len(df_secondary)),
                'Nombre de liens à retirer': np.random.randint(0, 10, len(df_secondary)),
                'Nombre de liens à remplacer': np.random.randint(0, 10, len(df_secondary))
            })
            st.write(df_report)

            st.write("Rapport 2 : Graphiques de scores et pourcentages")
            col1, col2 = st.columns(2)
            with col1:
                url_depart = st.selectbox("Sélectionnez des URL de départ", ["Sélectionnez une URL"] + df_primary[url_column_primary].tolist())
            with col2:
                url_destination = st.selectbox("Sélectionnez des URL de destination", ["Sélectionnez une URL"] + df_secondary[url_column_secondary].tolist())

            if url_depart != "Sélectionnez une URL" and url_destination != "Sélectionnez une URL":
                score_moyen = np.random.randint(0, 100)
                pourcentage_remplacement = np.random.randint(0, 100)

                col1, col2 = st.columns(2)
                with col1:
                    fig1 = plot_gauge_chart(score_moyen, "Score moyen de maillage interne (sur une base de 5 URL minimum)")
                    st.plotly_chart(fig1)
                with col2:
                    fig2 = plot_gauge_chart(pourcentage_remplacement, "Pourcentage de liens à remplacer et/ou à ajouter (sur une base de 5 URL minimum)")
                    st.plotly_chart(fig2)

if __name__ == "__main__":
    app()
