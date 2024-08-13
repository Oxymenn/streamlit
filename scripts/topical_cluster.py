import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import spacy
import matplotlib.pyplot as plt
import seaborn as sns

# Charger le modèle spaCy (assurez-vous d'avoir téléchargé le modèle avec : python -m spacy download fr_core_news_md)
nlp = spacy.load("fr_core_news_md")

def get_embedding(text):
    doc = nlp(text)
    return doc.vector

def perform_clustering(keywords, n_clusters=3):
    # Créer les embeddings
    embeddings = np.array([get_embedding(kw) for kw in keywords])
    
    # Effectuer le clustering hiérarchique
    clustering = AgglomerativeClustering(n_clusters=n_clusters)
    labels = clustering.fit_predict(embeddings)
    
    cluster_data = {
        'Topic Clusters': labels, 
        'Keywords': keywords
    }
    cluster_df = pd.DataFrame(cluster_data)
    
    return cluster_df, n_clusters

def app():
    st.title("Topical Cluster amélioré")
    
    st.write("""
    Cet outil regroupe les mots-clés en clusters thématiques en utilisant des embeddings de mots et un clustering hiérarchique.
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
