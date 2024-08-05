import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# Liste de stopwords en français et autres fonctions restent inchangées

def extract_and_clean_content(url, include_classes, exclude_classes):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Utiliser les classes à inclure si elles sont spécifiées
        if include_classes:
            elements = []
            for class_name in include_classes:
                elements.extend(soup.find_all(class_=class_name))
        else:
            elements = soup.find_all(class_='below-woocommerce-category')
        
        # Exclure les éléments avec les classes spécifiées
        if exclude_classes:
            elements = [el for el in elements if not any(cls in el.get('class', []) for cls in exclude_classes)]
        
        if elements:
            content = ' '.join([element.get_text(separator=" ", strip=True) for element in elements])
        else:
            st.error(f"Éléments non trouvés dans l'URL: {url}")
            return None

        # Nettoyage du texte (reste inchangé)
        # ...

        return content
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de l'accès à {url}: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du contenu de {url}: {e}")
        return None

# Les autres fonctions restent inchangées

def app():
    st.title("Pages Similaires Sémantiquement - Woocommerce (Shoptimizer)")
    
    # Gestion des classes à inclure
    if 'include_classes' not in st.session_state:
        st.session_state.include_classes = []
    
    include_class = st.text_input("Classe HTML à inclure")
    if st.button("Ajouter classe à inclure"):
        if include_class and include_class not in st.session_state.include_classes:
            st.session_state.include_classes.append(include_class)
    
    st.write("Classes à inclure:", st.session_state.include_classes)
    
    # Gestion des classes à exclure
    if 'exclude_classes' not in st.session_state:
        st.session_state.exclude_classes = []
    
    exclude_class = st.text_input("Classe HTML à exclure")
    if st.button("Ajouter classe à exclure"):
        if exclude_class and exclude_class not in st.session_state.exclude_classes:
            st.session_state.exclude_classes.append(exclude_class)
    
    st.write("Classes à exclure:", st.session_state.exclude_classes)
    
    uploaded_file = st.file_uploader("Importer un fichier CSV ou Excel contenant des URLs", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            file_name = uploaded_file.name.rsplit('.', 1)[0]
            column_option = st.selectbox("Sélectionnez la colonne contenant les URLs", df.columns)
            urls = df[column_option].dropna().unique()

            # Bouton pour exécuter le script
            if st.button("Exécuter l'analyse"):
                with st.spinner("Analyse en cours..."):
                    st.session_state['contents'] = [extract_and_clean_content(url, st.session_state.include_classes, st.session_state.exclude_classes) for url in urls]
                    st.session_state['embeddings'] = [get_embeddings(content) for content in st.session_state['contents'] if content]
                    st.session_state['similarity_matrix'] = calculate_similarity(st.session_state['embeddings'])
                
                st.success("Analyse terminée!")

                # Affichage des résultats (comme précédemment)
                if 'similarity_matrix' in st.session_state and st.session_state['similarity_matrix'] is not None:
                    # Code pour afficher les résultats (inchangé)
                    # ...

        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier ou de l'analyse: {e}")

# Assurez-vous que la fonction `app` est appelée ici
if __name__ == "__main__":
    app()
