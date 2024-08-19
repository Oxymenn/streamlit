import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import io
from sentence_transformers import SentenceTransformer, util

# Liste prédéfinie de stopwords en français
STOPWORDS = set(['au','aux','avec','ce','ces','dans','de','des','du','elle','en','et','eux','il','je','la','le','leur','lui','ma','mais','me','même','mes','moi','mon','ne','nos','notre','nous','on','ou','par','pas','pour','qu','que','qui','sa','se','ses','son','sur','ta','te','tes','toi','ton','tu','un','une','vos','votre','vous','c','d','j','l','à','m','n','s','t','y','été','étée','étées','étés','étant','étante','étants','étantes','suis','es','est','sommes','êtes','sont','serai','seras','sera','serons','serez','seront','serais','serait','serions','seriez','seraient','étais','était','étions','étiez','étaient','fus','fut','fûmes','fûtes','furent','sois','soit','soyons','soyez','soient','fusse','fusses','fût','fussions','fussiez','fussent','ayant','ayante','ayantes','ayants','eu','eue','eues','eus','ai','as','avons','avez','ont','aurai','auras','aura','aurons','aurez','auront','aurais','aurait','aurions','auriez','auraient','avais','avait','avions','aviez','avaient','eut','eûmes','eûtes','eurent','aie','aies','ait','ayons','ayez','aient','eusse','eusses','eût','eussions','eussiez','eussent'])

# Fonction pour faire une requête Google
def google_search(query, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    response = requests.get(url, headers=headers)
    return response.text

# Fonction pour extraire les en-têtes
def extract_headers(html, optional_headers=['h1', 'h2', 'h3']):
    soup = BeautifulSoup(html, 'html.parser')
    headers = []
    for i, result in enumerate(soup.select('div.g')[:10], start=1):
        result_headers = []
        for j, header in enumerate(result.find_all(optional_headers), start=1):
            result_headers.append([header.name, header.text.strip(), i, j])
        headers.extend(result_headers)
    return headers

# Classe pour gérer les encodages et les similitudes
class Encodings:
    def __init__(self, lista, model):
        self.lista = list(set([x.lower() for x in lista]))
        self.model = model
        self.embeddings = self.model.encode(self.lista, batch_size=64, show_progress_bar=True, convert_to_tensor=True)
    
    def calculate_similarity(self, key):
        query_emb = self.model.encode(key)
        scores = util.cos_sim(query_emb, self.embeddings)[0].cpu().tolist()
        doc_score_pairs = sorted(list(zip(self.lista, [round(x,2) for x in scores])), key=lambda x: x[1], reverse=True)
        return doc_score_pairs

# Fonction pour nettoyer le texte
def clean_text(text):
    return ' '.join([word for word in text.lower().split() if word not in STOPWORDS])

# Fonction pour obtenir les n-grams
def get_ngrams(text, n):
    words = text.split()
    ngrams_list = [words[i:i+n] for i in range(len(words)-n+1)]
    return [' '.join(gram) for gram in ngrams_list]

# Fonction principale pour scraper les SERP
def scrape_serp(query, language='fr', country='fr', optional_headers=['h1', 'h2', 'h3']):
    html = google_search(query, language, country)
    headers = extract_headers(html, optional_headers)
    
    # Chargement du modèle de similarité sémantique
    model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
    
    # Calcul des similitudes
    header_texts = [header[1] for header in headers]
    encodings = Encodings(header_texts, model)
    similarities = encodings.calculate_similarity(query)
    
    # Ajout des scores aux en-têtes
    for header in headers:
        header.append(next(score for text, score in similarities if text == header[1].lower()))
    
    # Tri des en-têtes par score
    headers.sort(key=lambda x: x[4], reverse=True)
    
    # Analyse des mots fréquents
    all_text = clean_text(' '.join([header[1] for header in headers]))
    unigrams = pd.Series(all_text.split()).value_counts().head(20).to_dict()
    bigrams = pd.Series(get_ngrams(all_text, 2)).value_counts().head(20).to_dict()
    trigrams = pd.Series(get_ngrams(all_text, 3)).value_counts().head(20).to_dict()
    
    return {
        'headers': headers,
        'unigrams': list(unigrams.items()),
        'bigrams': list(bigrams.items()),
        'trigrams': list(trigrams.items())
    }

def app():
    st.title("Google SERP Scraper et Analyseur d'En-têtes")

    # Zone de texte pour les mots-clés
    keywords = st.text_area("Entrez vos mots-clés (un par ligne):")
    
    # Sélection de la langue et du pays
    language = st.selectbox("Langue", ['fr', 'en', 'es', 'de', 'it'])
    country = st.selectbox("Pays", ['fr', 'us', 'uk', 'es', 'de', 'it'])
    
    # Sélection des en-têtes à extraire
    optional_headers = st.multiselect("En-têtes à extraire", ['h1', 'h2', 'h3', 'h4'], default=['h1', 'h2', 'h3'])

    if st.button("Exécuter"):
        if keywords:
            keywords_list = keywords.split('\n')
            all_results = []

            progress_bar = st.progress(0)
            for i, keyword in enumerate(keywords_list):
                results = scrape_serp(keyword.strip(), language, country, optional_headers)
                all_results.append({'keyword': keyword, **results})
                progress_bar.progress((i + 1) / len(keywords_list))
                time.sleep(random.uniform(1, 3))  # Pause aléatoire pour éviter la détection

            # Affichage des résultats
            for result in all_results:
                st.write(f"Résultats pour '{result['keyword']}':")
                
                # Affichage des en-têtes
                headers_df = pd.DataFrame(result['headers'], columns=['Type', 'Texte', 'Position SERP', 'Position En-tête', 'Score'])
                st.write("En-têtes les plus pertinents:")
                st.dataframe(headers_df)
                
                # Affichage des mots fréquents
                st.write("Mots les plus fréquents:")
                words_df = pd.DataFrame(
                    result['unigrams'] + result['bigrams'] + result['trigrams'], 
                    columns=['Mot(s)', 'Fréquence']
                )
                words_df['Nombre de mots'] = words_df['Mot(s)'].apply(lambda x: len(x.split()))
                st.dataframe(words_df)

            # Création du fichier Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                for i, result in enumerate(all_results):
                    headers_df = pd.DataFrame(result['headers'], columns=['Type', 'Texte', 'Position SERP', 'Position En-tête', 'Score'])
                    words_df = pd.DataFrame(
                        result['unigrams'] + result['bigrams'] + result['trigrams'], 
                        columns=['Mot(s)', 'Fréquence']
                    )
                    words_df['Nombre de mots'] = words_df['Mot(s)'].apply(lambda x: len(x.split()))
                    
                    headers_df.to_excel(writer, sheet_name=f'Keyword_{i+1}_Headers', index=False)
                    words_df.to_excel(writer, sheet_name=f'Keyword_{i+1}_Words', index=False)
            
            # Bouton de téléchargement
            st.download_button(
                label="Télécharger les résultats (Excel)",
                data=buffer.getvalue(),
                file_name="resultats_serp_headers.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Veuillez entrer au moins un mot-clé.")

if __name__ == "__main__":
    app()
