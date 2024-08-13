import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def preprocess(text):
    return text.lower()

def perform_clustering(keywords, n_clusters=3):
    # Prétraitement
    processed_keywords = [preprocess(kw) for kw in keywords]
    
    # Vectorisation
    vectorizer = CountVectorizer(analyzer='char', ngram_range=(2,3))
    X = vectorizer.fit_transform(processed_keywords)
    
    # Calcul de la similarité
    similarity_matrix = cosine_similarity(X)
    
    # Clustering
    clustering = AgglomerativeClustering(n_clusters=n_clusters, affinity='precomputed', linkage='average')
    labels = clustering.fit_predict(1 - similarity_matrix)
    
    cluster_data = {
        'Topic Clusters': labels, 
        'Keywords': keywords
    }
    cluster_df = pd.DataFrame(cluster_data)
    
    return cluster_df, n_clusters

def app():
    st.title("Topical Cluster")
    
    st.write("""
    Cet outil regroupe les mots-clés en clusters thématiques.
    Entrez vos mots-clés (un par ligne) dans la zone de texte ci-dessous.
    """)

    keywords_input = st.text_area("Entrez vos mots-clés (un par ligne) :", height=200)
    n_clusters = st.slider("Nombre de clusters souhaités", min_value=2, max_value=10, value=3)

    if st.button("Effectuer le clustering"):
        if keywords_input:
            keywords = [kw.strip() for kw in keywords_input.split('\n') if kw.strip()]

            with st.spinner("Clustering en cours..."):
                cluster_df, n_clusters = perform_clustering(keywords, n_clusters)

            st.success(f"Clustering terminé ! {n_clusters} clusters trouvés.")

            st.subheader("Mots-clés regroupés")
            st.dataframe(cluster_df)

            csv = cluster_df.to_csv(index=False)
            st.download_button(
                label="Télécharger les mots-clés regroupés (CSV)",
                data=csv,
                file_name="mots_cles_regroupes.csv",
                mime="text/csv",
            )

            st.subheader("Distribution des clusters")
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.countplot(x='Topic Clusters', data=cluster_df, ax=ax)
            plt.title("Distribution des mots-clés par cluster")
            plt.xlabel("Cluster")
            plt.ylabel("Nombre de mots-clés")
            st.pyplot(fig)

        else:
            st.warning("Veuillez entrer des mots-clés avant de lancer le clustering.")

if __name__ == "__main__":
    app()
