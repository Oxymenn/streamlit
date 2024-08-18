import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import time

# Liste d'agents utilisateurs
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
]

def get_random_header():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def get_soup(url):
    response = requests.get(url, headers=get_random_header())
    return BeautifulSoup(response.text, 'html.parser')

def scrape_serp(keyword, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}"
    soup = get_soup(url)
    
    results = {
        'PAA': [],
        'related_searches': [],
        'suggest': []
    }
    
    # Scraper les PAA
    paa_elements = soup.select("div.related-question-pair")
    for paa in paa_elements:
        results['PAA'].append(paa.text.strip())
    
    # Scraper les recherches associées
    related_searches_elements = soup.select("a.BVG0Nb")
    for search in related_searches_elements:
        results['related_searches'].append(search.text.strip())
    
    # Scraper les Google Suggest
    suggest_url = f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={keyword}'
    suggest_soup = get_soup(suggest_url)
    results['suggest'] = [sugg['data'] for sugg in suggest_soup.find_all('suggestion')]
    
    return results

def app():
    st.title("Google SERP Scraper")
    
    keywords = st.text_area("Entrez les mots-clés (un par ligne) :")
    if st.button("Lancer le scraping"):
        keywords_list = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
        results = {}
        
        for keyword in keywords_list:
            results[keyword] = scrape_serp(keyword)
        
        # Créer un DataFrame
        df = pd.DataFrame(columns=['Keyword', 'PAA', 'Recherches associées', 'Google Suggest'])
        
        for keyword in results:
            df = df.append({
                'Keyword': keyword,
                'PAA': ', '.join(results[keyword]['PAA']),
                'Recherches associées': ', '.join(results[keyword]['related_searches']),
                'Google Suggest': ', '.join(results[keyword]['suggest'])
            }, ignore_index=True)
        
        # Enregistrer dans un fichier Excel
        df.to_excel("serp_results.xlsx")
        
        st.success("Scraping terminé ! Résultats enregistrés dans 'serp_results.xlsx'")
        st.dataframe(df)

if __name__ == "__main__":
    app()
