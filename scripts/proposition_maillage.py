import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from io import BytesIO

# Liste de stopwords en français (inchangée)
default_stopwords_fr = {
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

def extract_and_clean_content(url, exclude_classes, include_classes, stopwords):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for class_name in exclude_classes:
            for element in soup.find_all(class_=class_name):
                element.decompose()
        
        if include_classes:
            content = ' '.join([element.get_text(separator=" ", strip=True) for class_name in include_classes for element in soup.find_all(class_=class_name)])
        else:
            content = soup.body.get_text(separator=" ", strip=True)
        
        content = re.sub(r'\s+', ' ', content.lower())
        content = re.sub(r'[^\w\s]', '', content)
        return ' '.join([word for word in content.split() if word not in stopwords])
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de l'accès à {url}: {e}")
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du contenu de {url}: {e}")
    return None

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
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()['data'][0]['embedding']
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as e:
        st.error(f"Erreur lors de la création des embeddings: {e}")
    return None

def calculate_similarity(embeddings):
    try:
        # Filtrer les embeddings non nuls
        valid_embeddings = [e for e in embeddings if e is not None]
        if len(valid_embeddings) != len(embeddings):
            st.warning(f"Attention : {len(embeddings) - len(valid_embeddings)} embeddings manquants ont été ignorés.")
        return cosine_similarity(valid_embeddings)
    except Exception as e:
        st.error(f"Erreur lors du calcul de la similarité cosinus: {e}")
        return None

def create_similarity_df(urls, similarity_matrix, selected_url, max_results):
    if selected_url not in urls:
        st.error(f"L'URL sélectionnée '{selected_url}' n'est pas dans la liste des URLs.")
        return pd.DataFrame()  # Retourner un DataFrame vide en cas d'erreur
    
    selected_index = urls.tolist().index(selected_url)
    selected_similarities = similarity_matrix[selected_index]
    
    if len(urls) != len(selected_similarities):
        st.error(f"Incohérence dans les tailles : {len(urls)} URLs vs {len(selected_similarities)} similarités.")
        return pd.DataFrame()  # Retourner un DataFrame vide en cas d'erreur
    
    similarity_df = pd.DataFrame({
        'URL': urls,
        'Similarité': selected_similarities
    })
    similarity_df = similarity_df[similarity_df['URL'] != selected_url]
    return similarity_df.sort_values(by='Similarité', ascending=False).head(max_results)

def create_links_table(urls, similarity_matrix, max_results):
    links_table = {'URL de départ': []}
    for n in range(1, max_results + 1):
        links_table[f'URL similaire {n}'] = []
    links_table['Concatener'] = []

    valid_urls = urls[:len(similarity_matrix)]  # Utilisez seulement les URLs avec des similarités valides

    for i, url in enumerate(valid_urls):
        similarities = similarity_matrix[i]
        temp_df = pd.DataFrame({'URL': valid_urls, 'Similarité': similarities})
        temp_df = temp_df[temp_df['URL'] != url]
        top_similar_urls = temp_df.sort_values(by='Similarité', ascending=False).head(max_results)['URL'].tolist()

        links_table['URL de départ'].append(url)
        for n in range(1, max_results + 1):
            links_table[f'URL similaire {n}'].append(top_similar_urls[n - 1] if len(top_similar_urls) >= n else None)

        concatenated = '; '.join([f"Lien {n} : {top_similar_urls[n - 1]}" if len(top_similar_urls) >= n else f"Lien {n} : " for n in range(1, max_results + 1)])
        links_table['Concatener'].append(concatenated)

    return pd.DataFrame(links_table)

def analyze_existing_links(df_maillage, url_depart_column, url_destination_column, similarity_matrix, urls):
    analysis_results = []
    urls_set = set(urls)  # Pour une recherche plus rapide
    
    for _, row in df_maillage.iterrows():
        url_depart = row[url_depart_column]
        url_destination = row[url_destination_column]
        
        if url_depart in urls_set and url_destination in urls_set:
            depart_index = urls.tolist().index(url_depart)
            destination_index = urls.tolist().index(url_destination)
            similarity_score = similarity_matrix[depart_index][destination_index]
            
            if similarity_score >= 0.75:
                decision = "À garder"
            else:
                decision = "À supprimer"
            
            analysis_results.append({
                "URL de départ": url_depart,
                "URL de destination": url_destination,
                "Score de similarité": similarity_score,
                "Décision": decision
            })
        else:
            analysis_results.append({
                "URL de départ": url_depart,
                "URL de destination": url_destination,
                "Score de similarité": "N/A (URL non trouvée)",
                "Décision": "À vérifier manuellement"
            })
    
    return pd.DataFrame(analysis_results)

def app():
    st.title("Pages Similaires Sémantiquement - Woocommerce (Shoptimizer)")
    uploaded_file = st.file_uploader("Importer un fichier Excel contenant des URLs", type=["xlsx"])

    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names

        urls_sheet = st.selectbox("Sélectionnez la feuille contenant les URLs à embedder", sheet_names)
        maillage_sheet = st.selectbox("Sélectionnez la feuille contenant le maillage interne existant", sheet_names)

        df_urls = pd.read_excel(uploaded_file, sheet_name=urls_sheet)
        df_maillage = pd.read_excel(uploaded_file, sheet_name=maillage_sheet)

        url_column = st.selectbox("Sélectionnez la colonne contenant les URLs à embedder", df_urls.columns)
        url_depart_column = st.selectbox("Sélectionnez la colonne des URLs de départ", df_maillage.columns)
        url_destination_column = st.selectbox("Sélectionnez la colonne des URLs de destination", df_maillage.columns)

        exclude_classes = st.text_input("Classes HTML à exclure (séparées par des virgules)", "")
        exclude_classes = [cls.strip() for cls in exclude_classes.split(',')] if exclude_classes else []

        include_classes = st.text_input("Classes HTML à inclure exclusivement (séparées par des virgules)", "")
        include_classes = [cls.strip() for cls in include_classes.split(',')] if include_classes else []

        additional_stopwords = st.text_input("Stopwords supplémentaires à exclure (séparés par des virgules)", "")
        additional_stopwords = [word.strip().lower() for word in additional_stopwords.split(',')] if additional_stopwords else []

        stopwords = default_stopwords_fr.union(set(additional_stopwords))

        execute_button = st.button("Exécuter")

        if execute_button:
            try:
                urls = df_urls[url_column].dropna().unique()
                file_name = uploaded_file.name.rsplit('.', 1)[0]

                st.session_state['contents'] = [extract_and_clean_content(url, exclude_classes, include_classes, stopwords) for url in urls]
                st.session_state['embeddings'] = [get_embeddings(content) for content in st.session_state['contents'] if content]
                
                if len(st.session_state['embeddings']) != len(urls):
                    st.warning(f"Attention : {len(urls) - len(st.session_state['embeddings'])} URLs n'ont pas pu être traitées.")
                
                st.session_state['similarity_matrix'] = calculate_similarity(st.session_state['embeddings'])
                
                if st.session_state['similarity_matrix'] is not None:
                    valid_urls = urls[:len(st.session_state['similarity_matrix'])]
                    st.session_state['urls'] = valid_urls
                    st.session_state['file_name'] = file_name

                    # Création du DataFrame pour les URLs similaires
                    max_results = 5  # Vous pouvez ajuster ce nombre si nécessaire
                    links_df = create_links_table(st.session_state['urls'], st.session_state['similarity_matrix'], max_results)

                    # Analyse du maillage existant
                    analysis_df = analyze_existing_links(df_maillage, url_depart_column, url_destination_column, st.session_state['similarity_matrix'], valid_urls)
                    
                    # Création du fichier Excel avec les deux feuilles
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        links_df.to_excel(writer, index=False, sheet_name='URLs Similaires')
                        analysis_df.to_excel(writer, index=False, sheet_name='Analyse Maillage Existant')
                    
                    st.download_button(
                        label="Télécharger le fichier Excel avec les résultats",
                        data=output.getvalue(),
                        file_name=f'resultats_maillage-{file_name}.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )

                    # Affichage des DataFrames dans l'interface
                    st.subheader("URLs Similaires")
                    st.dataframe(links_df)

                    st.subheader("Analyse du Maillage Existant")
                    st.dataframe(analysis_df)

                else:
                    st.error("Impossible de calculer la matrice de similarité. Veuillez vérifier vos données.")

            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")
                st.error("Détails de l'erreur :", exc_info=True)

if __name__ == "__main__":
    app()
