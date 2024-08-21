import streamlit as st
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import pandas as pd
import random
import io
import time
import logging
from sentence_transformers import SentenceTransformer, util
from itertools import cycle

# Configuration de la journalisation
logging.basicConfig(level=logging.INFO)

# Liste prédéfinie de stopwords en français
STOPWORDS = set([
    'au','aux', 'avec', 'ce', 'ces', 'dans', 'de', 'des', 'du', 
    'elle', 'en', 'et', 'eux', 'il', 'je', 'la', 'le', 'leur', 
    'lui', 'ma', 'mais', 'me', 'même', 'mes', 'moi', 'mon', 
    'ne', 'nos', 'notre', 'nous', 'on', 'ou', 'par', 'pas', 
    'pour', 'qu', 'que', 'qui', 'sa', 'se', 'ses', 'son', 
    'sur', 'ta', 'te', 'tes', 'toi', 'ton', 'tu', 'un', 
    'une', 'vos', 'votre', 'vous', 'c', 'd', 'j', 'l', 'à',
    'm', 'n', 's', 't', 'y', 'été', 'étée', 'étées', 
    'étés', 'étant', 'étante', 'étants', 'étantes', 'suis', 
    'es', 'est', 'sommes', 'êtes', 'sont', 'serai', 
    'seras', 'sera', 'serons', 'serez', 'seront', 'serais', 
    'serait', 'serions', 'seriez', 'seraient', 'étais', 
    'était', 'étions', 'étiez', 'étaient', 'fus', 'fut', 
    'fûmes', 'fûtes', 'furent', 'sois', 'soit', 'soyons', 
    'soyez', 'soient', 'fusse', 'fusses', 'fût', 'fussions', 
    'fussiez', 'fussent', 'ayant', 'ayante', 'ayantes', 
    'ayants', 'eu', 'eue', 'eues', 'eus', 'ai', 'as', 
    'avons', 'avez', 'ont', 'aurai', 'auras', 'aura', 
    'aurons', 'aurez', 'auront', 'aurais', 'aurait', 
    'aurions', 'auriez', 'auraient', 'avais', 'avait', 
    'avions', 'aviez', 'avaient', 'eut', 'eûmes', 'eûtes', 
    'eurent', 'aie', 'aies', 'ait', 'ayons', 'ayez', 
    'aient', 'eusse', 'eusses', 'eût', 'eussions', 
    'eussiez', 'eussent'
])

# Liste des User-Agents pour les requêtes
USER_AGENTS = cycle([
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0"
])

# Fonction asynchrone pour faire une requête Google
async def google_search(session, query, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={query}"
    headers = {"User-Agent": next(USER_AGENTS)}  # Vary User-Agent
    async with session.get(url, headers=headers) as response:
        return await response.text()

# Fonction pour extraire les données des résultats de recherche
def extract_data(html, optional_headers=['h1', 'h2', 'h3']):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    for i, result in enumerate(soup.select('div.g')[:10], start=1):
        title = result.find('h3')
        meta_desc = result.find('span', {'class': 'aCOpRe'})
        titles = title.text if title else 'N/A'
        descriptions = meta_desc.text if meta_desc else 'N/A'
        
        headers = {tag: [] for tag in optional_headers}
        
        for header in result.find_all(optional_headers):
            headers[header.name].append(header.text.strip())
        
        results.append({
            'title': titles,
            'meta_desc': descriptions,
            'headers': headers
        })
    return results

# Classe pour gérer les encodages et les similitudes
class Encodings:
    def __init__(self, lista, model):
        self.lista = list(set([x.lower() for x in lista]))
        self.model = model
        self.embeddings = self.model.encode(self.lista, batch_size=64, show_progress_bar=True, convert_to_tensor=True)
    
    def calculate_similarity(self, key):
        query_emb = self.model.encode(key, convert_to_tensor=True)
        scores = util.cos_sim(query_emb, self.embeddings)[0].cpu().tolist()
        doc_score_pairs = sorted(list(zip(self.lista, [round(x, 2) for x in scores])), key=lambda x: x[1], reverse=True)
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
async def scrape_serp(session, query, language='fr', country='fr', optional_headers=['h1', 'h2', 'h3'], model=None):
    html = await google_search(session, query, language, country)
    results = extract_data(html, optional_headers)
    
    # Calcul des similitudes pour les en-têtes <h2> et <h3>
    for result in results:
        header_texts = [header for key in result['headers'].keys() for header in result['headers'][key]]
        encodings = Encodings(header_texts, model)
        similarities = encodings.calculate_similarity(query)
        
        for key in result['headers'].keys():
            result['headers'][key] = sorted(result['headers'][key], key=lambda x: next(score for text, score in similarities if text == x.lower()), reverse=True)
    
    return results

async def main(keywords_list, language, country, optional_headers):
    model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
    async with ClientSession() as session:
        tasks = []
        for keyword in keywords_list:
            tasks.append(scrape_serp(session, keyword.strip(), language, country, optional_headers, model))
        
        all_results = await asyncio.gather(*tasks)
        return all_results
    
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
            keywords_list = keywords.strip().split('\n')
            st.info("Scraping en cours, veuillez patienter...")
            start_time = time.time()

            # Lancer la boucle d'événements pour exécuter les requêtes asynchrones
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            all_results = loop.run_until_complete(main(keywords_list, language, country, optional_headers))
            
            # Création du fichier Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                for i, keyword in enumerate(keywords_list):
                    results = all_results[i]
                    
                    # Collecter les titres et méta-descriptions
                    titles = '[]'.join([res['title'] for res in results])
                    meta_descs = '[]'.join([res['meta_desc'] for res in results])
                    
                    data = {
                        'Keyword': [keyword],
                        'Titles': [titles],
                        'Meta Descriptions': [meta_descs]
                    }
                    
                    # Ajouter les en-têtes
                    for header in optional_headers:
                        data[f'{header.upper()} Headers'] = ['[]'.join([item for res in results for item in res['headers'].get(header, [])])]
                    
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=f'Keyword_{i+1}', index=False)
            
            # Bouton de téléchargement
            st.download_button(
                label="Télécharger les résultats (Excel)",
                data=buffer.getvalue(),
                file_name="resultats_serp_headers.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            end_time = time.time()
            logging.info(f"Temps total pour l'exécution : {end_time - start_time} secondes")
        else:
            st.warning("Veuillez entrer au moins un mot-clé.")

if __name__ == "__main__":
    app()
