import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px

@st.cache_resource
def load_model():
    return SentenceTransformer('distiluse-base-multilingual-cased-v2')

@st.cache_data
def get_embeddings(texts, model):
    return model.encode(texts)

def calculate_similarity(embeddings):
    return cosine_similarity(embeddings)

st.set_page_config(page_title="Analyse de similarité d'URLs", layout="wide")
st.title("Analyse de similarité d'URLs")

model = load_model()

uploaded_file = st.file_uploader("Choisissez votre fichier Excel contenant les URLs", type="xlsx")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    url_column = st.selectbox("Sélectionnez la colonne contenant les URLs", df.columns)
    content_column = st.selectbox("Sélectionnez la colonne contenant le contenu textuel", df.columns)
    
    if st.button("Analyser la similarité"):
        with st.spinner("Calcul des embeddings et de la similarité en cours..."):
            embeddings = get_embeddings(df[content_column].tolist(), model)
            similarity_matrix = calculate_similarity(embeddings)
            
        st.success("Analyse terminée!")
        
        st.subheader("Matrice de similarité")
        fig = px.imshow(similarity_matrix, labels=dict(x="URLs", y="URLs", color="Similarité"),
                        x=df[url_column], y=df[url_column])
        st.plotly_chart(fig)
        
        st.subheader("URLs les plus similaires")
        for i in range(len(df)):
            similar_indices = similarity_matrix[i].argsort()[-6:-1][::-1]
            st.write(f"URLs similaires à {df[url_column][i]}:")
            for idx in similar_indices:
                st.write(f"- {df[url_column][idx]} (Similarité: {similarity_matrix[i][idx]:.2f})")
            st.write("---")

else:
    st.info("Veuillez uploader un fichier Excel pour commencer l'analyse.")
