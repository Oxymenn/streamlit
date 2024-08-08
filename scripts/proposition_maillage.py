import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import io

# Liste de stopwords en français (inchangée)
stopwords_fr = {
    "alors", "boutique", "site", "collection", "gamme", "découvrez", "sélection", "explorez", "nettoyer", "nettoyez", "entretien", "entretenir", "au", "aucuns", "aussi", "autre", "avant", "avec", "avoir", "bon", 
    "car", "ce", "cela", "ces", "ceux", "chaque", "ci", "comme", "comment", 
    "dans", "des", "du", "dedans", "dehors", "depuis", "devrait", "doit", 
    "donc", "dos", "droite", "début", "elle", "elles", "en", "encore", "essai", 
    "est", "et", "eu", "fait", "faites", "fois", "font", "force", "haut", 
    "hors", "ici", "il", "ils", "je", "juste", "la", "le", "les", "leur", 
    "là", "ma", "maintenant", "mais", "mes", "mien", "moins", "mon", "mot", 
    "même", "ni", "nommés", "notre", "nous", "nouveaux", "ou", "où", "par", 
    "parce", "parole", "pas", "personnes", "peut", "peu", "pièce", "plupart", 
    "pour", "pourquoi", "quand", "que", "quel", "quelle", "quelles", "quels", 
    "qui", "sa", "sans", "ses", "seulement", "si", "sien", "son", "sont", 
    "sous", "soyez", "sujet", "sur", "ta", "tandis", "tellement", "tels", 
    "tes", "ton", "tous", "tout", "trop", "très", "tu", "valeur", "voie", 
    "voient", "vont", "votre", "vous", "vu", "ça", "étaient", "état", "étions", 
    "été", "être"
}

# Configuration de la clé API OpenAI
OPENAI_API_KEY = st.secrets.get("api_key", "default_key")

# Fonction pour extraire et nettoyer le contenu HTML (modifiée)
def extract_and_clean_content(url, include_classes, exclude_classes, additional_stopwords):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Filtrer le contenu en fonction des classes à inclure et exclure
        if include_classes:
            elements = soup.find_all(class_=include_classes)
        else:
            elements = [soup]

        if exclude_classes:
            for cls in exclude_classes:
                for element in elements:
                    for excluded in element.find_all(class_=cls):
                        excluded.decompose()

        content = ' '.join([element.get_text(separator=" ", strip=True) for element in elements])

        # Nettoyage du texte
        content = re.sub(r'\s+', ' ', content)
        content = content.lower()
        content = re.sub(r'[^\w\s]', '', content)

        # Retirer les mots vides, y compris les stopwords additionnels
        words = content.split()
        all_stopwords = stopwords_fr.union(set(additional_stopwords))
        content = ' '.join([word for word in words if word not in all_stopwords])

        return content
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de l'accès à {url}: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du contenu de {url}: {e}")
        return None

# Fonction pour obtenir les embeddings d'un texte (inchangée)
def get_embeddings(text):
    try:
        response = requests.post(
            'https://api.openai.com/v1/embeddings',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'text-embedding-3-small',
                'input': text,
                'encoding_format': 'float'
            }
        )
        response.raise_for_status()
        data = response.json()
        return data['data'][0]['embedding']
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as e:
        st.error(f"Erreur lors de la création des embeddings: {e}")
    return None

# Fonction pour calculer la similarité cosinus (inchangée)
def calculate_similarity(embeddings):
    try:
        similarity_matrix = cosine_similarity(embeddings)
        return similarity_matrix
    except Exception as e:
        st.error(f"Erreur lors du calcul de la similarité cosinus: {e}")
        return None

# Fonction principale de l'application
def app():
    st.title("Proposition de Maillage Interne Personnalisé")

    # Champ pour coller les URLs à analyser
    urls_to_analyze = st.text_area("Collez ici les URLs à analyser (une URL par ligne)")
    
    # Importer le fichier Excel
    uploaded_file = st.file_uploader("Importer le fichier Excel contenant les URLs, ancres et indices de priorité", type=["xlsx"])

    if uploaded_file is not None and urls_to_analyze:
        try:
            # Lire le fichier Excel importé
            df_excel = pd.read_excel(uploaded_file)

            # Sous-titre pour la sélection des données GSC
            st.subheader("Sélectionnez les données GSC")

            # Sélection des colonnes
            col_url = st.selectbox("Sélectionnez la colonne contenant les URLs", df_excel.columns)
            col_ancre = st.selectbox("Sélectionnez la colonne contenant les ancres", df_excel.columns)
            col_priorite = st.selectbox("Sélectionnez la colonne contenant l'indice de priorité (nombre d'impressions)", df_excel.columns)

            # Vérification de l'existence des colonnes sélectionnées
            if not all(col in df_excel.columns for col in [col_url, col_ancre, col_priorite]):
                st.error("Erreur: Une ou plusieurs colonnes sélectionnées n'existent pas dans le fichier Excel.")
                return

            # Curseur pour le nombre d'URLs de destination
            urls_list = [url.strip() for url in urls_to_analyze.split('\n') if url.strip()]
            max_urls = len(urls_list)
            num_dest_urls = st.slider("Nombre d'URLs de destination à inclure", min_value=1, max_value=max_urls, value=min(5, max_urls))

            # Sous-titre pour les filtres
            st.subheader("Filtrer le contenu HTML et termes")

            # Filtres supplémentaires
            include_classes = st.text_area("Classes HTML à analyser exclusivement (une classe par ligne, optionnel)")
            exclude_classes = st.text_area("Classes HTML à exclure de l'analyse (une classe par ligne, optionnel)")
            additional_stopwords = st.text_area("Termes/stopwords supplémentaires à exclure de l'analyse (un terme par ligne, optionnel)")

            if st.button("Exécuter l'analyse"):
                # Traiter les filtres
                include_classes = [cls.strip() for cls in include_classes.split('\n') if cls.strip()]
                exclude_classes = [cls.strip() for cls in exclude_classes.split('\n') if cls.strip()]
                additional_stopwords = [word.strip() for word in additional_stopwords.split('\n') if word.strip()]

                # Extraire et nettoyer le contenu des URLs
                contents = [extract_and_clean_content(url, include_classes, exclude_classes, additional_stopwords) for url in urls_list]
                contents = [content for content in contents if content]

                if not contents:
                    st.error("Aucun contenu n'a pu être extrait des URLs fournies.")
                    return

                # Obtenir les embeddings
                embeddings = [get_embeddings(content) for content in contents]
                embeddings = [emb for emb in embeddings if emb]

                if not embeddings:
                    st.error("Impossible de générer des embeddings pour les contenus extraits.")
                    return

                # Calculer la matrice de similarité
                similarity_matrix = calculate_similarity(embeddings)

                if similarity_matrix is not None:
                    # Créer le DataFrame de résultats
                    results = []
                    for i, url_start in enumerate(urls_list):
                        similarities = similarity_matrix[i]
                        similar_urls = sorted(zip(urls_list, similarities), key=lambda x: x[1], reverse=True)[1:num_dest_urls+1]

                        for url_dest, sim in similar_urls:
                            if sim >= 0.75:  # Seulement si la similarité est >= 0.75
                                ancres = df_excel[df_excel[col_url] == url_dest].sort_values(col_priorite, ascending=False)[col_ancre].tolist()
                                ancre = ancres[0] if ancres else df_excel.sort_values(col_priorite, ascending=False)[col_ancre].iloc[0]
                                results.append({'URL de départ': url_start, 'URL de destination': url_dest, 'Ancre': ancre})

                    # Créer le DataFrame final
                    df_results = pd.DataFrame(results)

                    if df_results.empty:
                        st.warning("Aucun résultat n'a été trouvé avec les critères spécifiés.")
                    else:
                        # Afficher les résultats
                        st.dataframe(df_results)

                        # Option de téléchargement
                        csv = df_results.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Télécharger les résultats (CSV)",
                            data=csv,
                            file_name='maillage_interne_personnalise.csv',
                            mime='text/csv'
                        )
                else:
                    st.error("Erreur lors du calcul de la similarité.")
        except Exception as e:
            st.error(f"Erreur lors du traitement : {str(e)}")

# Exécution de l'application
if __name__ == "__main__":
    app()
