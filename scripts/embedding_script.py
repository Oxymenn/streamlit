import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import openai
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

# Télécharger les ressources NLTK nécessaires
nltk.download('stopwords')
nltk.download('wordnet')

# Initialisation du lemmatizer et des stop words
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Configuration de l'API OpenAI
openai.api_key = st.secrets["openai"]["openai_api_key"]

# Fonction pour nettoyer le texte
def clean_text(text):
    text = re.sub(r'<[^>]+>', ' ', text)  # Supprimer les balises HTML
    text = re.sub(r'\W+', ' ', text)  # Supprimer les caractères spéciaux
    text = text.lower()  # Convertir en minuscules
    words = text.split()
    words = [word for word in words if word not in stop_words]  # Supprimer les mots vides
    words = [lemmatizer.lemmatize(word) for word in words]  # Lemmatisation
    return ' '.join(words)

# Fonction pour extraire le contenu d'une URL
def extract_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find(class_='below-woocommerce-category')
        return clean_text(content.get_text()) if content else ''
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération de l'URL {url}: {e}")
        return ''

# Fonction pour générer les embeddings à partir de textes
def get_embeddings(texts):
    response = openai.Embedding.create(
        input=texts,
        model="text-embedding-ada-002"  # Ou utilisez le modèle spécifié dans votre besoin
    )
    return [data['embedding'] for data in response['data']]

# Fonction principale de l'application
def main():
    st.title("Analyse de Similarité Sémantique des URLs")
    
    # Importation du fichier CSV ou Excel
    uploaded_file = st.file_uploader("Importer un fichier CSV ou Excel contenant des URLs", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.write("Aperçu des URLs importées :")
        st.dataframe(df.head())
        
        # Extraire le contenu des URLs
        df['Content'] = df['URL'].apply(extract_content)
        
        st.write("Contenus extraits et nettoyés :")
        st.dataframe(df[['URL', 'Content']].head())
        
        # Générer les embeddings
        df['Embedding'] = get_embeddings(df['Content'].tolist())
        
        # Calculer la similarité cosinus
        similarity_matrix = cosine_similarity(df['Embedding'].tolist())
        
        # Conversion de la matrice en DataFrame
        similarity_df = pd.DataFrame(similarity_matrix, columns=df['URL'], index=df['URL'])
        
        st.write("Matrice de similarité cosinus :")
        st.dataframe(similarity_df)
        
        # Tableau interactif
        st.write("Tableau de Similarité Interactif :")
        similarity_long_df = similarity_df.reset_index().melt(id_vars='index', var_name='URL2', value_name='Cosine Similarity')
        similarity_long_df.columns = ['URL1', 'URL2', 'Cosine Similarity']
        
        # Affichage et filtres
        filtered_df = similarity_long_df[similarity_long_df['Cosine Similarity'] > 0.5]  # Filtrer par exemple
        st.dataframe(filtered_df.sort_values(by='Cosine Similarity', ascending=False))
        
        # Exportation des résultats
        if st.button("Exporter les résultats en CSV"):
            filtered_df.to_csv('similarity_results.csv', index=False)
            st.success("Les résultats ont été exportés en similarity_results.csv")

if __name__ == "__main__":
    main()
