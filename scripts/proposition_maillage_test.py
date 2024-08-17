import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import concurrent.futures

# Liste d'agents utilisateurs
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
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

def get_suggest(keyword, language='fr', country='fr'):
    url = f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={keyword}'
    soup = get_soup(url)
    return [sugg['data'] for sugg in soup.find_all('suggestion')]

def scrape_serp(keyword, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}"
    soup = get_soup(url)
    
    results = {
        'PAA': [],
        'related_searches': [],
        'suggest': get_suggest(keyword, language, country)
    }
    
    # Scraping des PAA
    paa_elements = soup.select("div.related-question-pair")
    for paa in paa_elements:
        results['PAA'].append(paa.text.strip())
    
    # Scraping des recherches associées
    related_searches_elements = soup.select("a.k8XOCe")
    for search in related_searches_elements:
        results['related_searches'].append(search.text.strip())
    
    return results

def recursive_scrape(keyword, depth, max_depth):
    if depth > max_depth:
        return {}
    
    results = scrape_serp(keyword)
    
    if depth < max_depth:
        for suggest in results['suggest'][:3]:  # Limitation aux 3 premières suggestions
            suggest_results = recursive_scrape(suggest, depth + 1, max_depth)
            for key in suggest_results:
                results[key].extend(suggest_results[key])
    
    return results

def scrape_keyword(keyword, max_depth):
    return recursive_scrape(keyword, 1, max_depth)

def app():
    st.title("Google SERP Scraper")
    
    keywords = st.text_area("Entrez les mots-clés (un par ligne) :")
    depth = st.slider("Sélectionnez la profondeur", 1, 5, 1)
    
    if st.button("Lancer le scraping"):
        keywords_list = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
        
        progress_bar = st.progress(0)
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_keyword = {executor.submit(scrape_keyword, keyword, depth): keyword for keyword in keywords_list}
            for i, future in enumerate(concurrent.futures.as_completed(future_to_keyword)):
                keyword = future_to_keyword[future]
                try:
                    results[keyword] = future.result()
                except Exception as exc:
                    st.error(f'{keyword} a généré une exception: {exc}')
                progress_bar.progress((i + 1) / len(keywords_list))
        
        # Créer un DataFrame
        df = pd.DataFrame(index=keywords_list, columns=['PAA', 'Recherches associées', 'Suggest'])
        
        for keyword in results:
            df.at[keyword, 'PAA'] = ', '.join(results[keyword]['PAA'])
            df.at[keyword, 'Recherches associées'] = ', '.join(results[keyword]['related_searches'])
            df.at[keyword, 'Suggest'] = ', '.join(results[keyword]['suggest'])
        
        # Enregistrer dans un fichier Excel
        df.to_excel("serp_results.xlsx")
        
        st.success("Scraping terminé ! Résultats enregistrés dans 'serp_results.xlsx'")
        st.dataframe(df)

if __name__ == "__main__":
    app()
