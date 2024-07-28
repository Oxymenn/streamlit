import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import re
import os

# Liste des stopwords français
stopwords_fr = [
    'alors', 'au', 'aucuns', 'aussi', 'autre', 'avant', 'avec', 'avoir', 'bon', 
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
    'par', 'pour', 'sans', 'sous', 'vers', 'via'
]

def clean_text(text):
    # Convertir en minuscules
    text = text.lower()
    # Supprimer les caractères spéciaux et diviser en mots
    words = re.findall(r'\b\w+\b', text)
    # Filtrer les stopwords
    words = [word for word in words if word not in stopwords_fr]
    return ' '.join(words)

# Charger le modèle Sentence-BERT
model = SentenceTransformer('sentence-transformers/LaBSE')  # modèle multilingue adapté aux tâches sémantiques

def generate_embeddings(texts):
    cleaned_texts = [clean_text(text) for text in texts]
    embeddings = model.encode(cleaned_texts)
    return embeddings.tolist()

def app():
    st.title("Génération des Embeddings pour un site E-commerce")

    uploaded_file = st.file_uploader("Choisissez un fichier Excel ou CSV", type=["xlsx", "csv"])
    
    if uploaded_file:
        file_type = uploaded_file.name.split('.')[-1]
        
        if file_type == 'xlsx':
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif file_type == 'csv':
            df = pd.read_csv(uploaded_file)
        
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
