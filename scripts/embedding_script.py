import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

# Charger le modèle de Sentence Transformers
model = SentenceTransformer('distiluse-base-multilingual-cased-v1')

def generate_embeddings(texts):
    embeddings = model.encode(texts, convert_to_tensor=True)
    return embeddings.tolist()

def app():
    st.title("Génération des Embeddings pour un site E-commerce")

    uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.write("Aperçu des données :")
        st.write(df.head())
        
        url_column = st.selectbox("Sélectionnez la colonne des URL", df.columns)
        embedding_column = st.selectbox("Sélectionnez la colonne pour les Embeddings", df.columns)

        if st.button("Générer les Embeddings"):
            with st.spinner("Génération des embeddings en cours..."):
                texts = df[url_column].tolist()
                embeddings = generate_embeddings(texts)
                
                df[embedding_column] = embeddings
                st.write("Embeddings générés avec succès !")
                st.write(df.head())

            st.download_button(label="Télécharger le fichier avec Embeddings",
                               data=df.to_csv(index=False).encode('utf-8'),
                               file_name='embeddings_output.csv',
                               mime='text/csv')

if __name__ == "__main__":
    app()
