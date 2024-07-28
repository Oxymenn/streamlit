import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import openai

# Fonction pour charger les embeddings d'OpenAI
def get_embeddings(text, model="text-embedding-ada-002"):
    response = openai.Embedding.create(
        input=text,
        model=model
    )
    return response['data'][0]['embedding']

# Fonction pour calculer la similarité cosinus
def calculate_cosine_similarity(embeddings):
    similarity_matrix = cosine_similarity(embeddings)
    return similarity_matrix

# Application Streamlit
def main():
    st.title("Audit de Proximité Sémantique des URL")

    # Étape 1 : Upload du fichier Excel
    uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)

        # Étape 2 : Sélection de la colonne des URL
        url_column = st.selectbox("Sélectionnez la colonne des URL", df.columns)

        # Vérifier si l'utilisateur a sélectionné une colonne
        if url_column:
            urls = df[url_column].tolist()

            # Étape 3 : Générer les embeddings pour chaque URL
            embeddings = []
            with st.spinner("Génération des embeddings..."):
                for url in urls:
                    # Ici, nous utilisons l'URL comme texte, mais vous pouvez extraire le contenu réel de chaque URL si nécessaire
                    embedding = get_embeddings(url)
                    embeddings.append(embedding)

            # Convertir les embeddings en tableau numpy
            embeddings = np.array(embeddings)

            # Étape 4 : Calculer la similarité cosinus
            with st.spinner("Calcul de la similarité cosinus..."):
                similarity_matrix = calculate_cosine_similarity(embeddings)

            # Afficher la matrice de similarité sous forme de DataFrame
            similarity_df = pd.DataFrame(similarity_matrix, index=urls, columns=urls)
            st.write("Matrice de Similarité Cosinus")
            st.dataframe(similarity_df)

            # Option pour télécharger les résultats
            def convert_df(df):
                return df.to_csv().encode('utf-8')

            csv = convert_df(similarity_df)
            st.download_button(
                label="Télécharger la matrice de similarité en CSV",
                data=csv,
                file_name='similarity_matrix.csv',
                mime='text/csv',
            )

if __name__ == "__main__":
    main()
