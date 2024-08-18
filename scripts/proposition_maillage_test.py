import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import openpyxl

# Fonction pour faire une requête Google
def google_search(query, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    response = requests.get(url, headers=headers)
    return response.text

# Fonction pour extraire les suggestions Google
def get_google_suggest(query, language='fr', country='fr'):
    url = f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={query}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'xml')
    suggestions = [suggestion['data'] for suggestion in soup.find_all('suggestion')]
    return suggestions

# Fonction pour extraire les "People Also Ask" (PAA)
def extract_paa(html):
    soup = BeautifulSoup(html, 'html.parser')
    paa_elements = soup.select('div.related-question-pair')
    paa = [element.text.strip() for element in paa_elements]
    return paa

# Fonction pour extraire les recherches associées
def extract_related_searches(html):
    soup = BeautifulSoup(html, 'html.parser')
    related_searches = soup.select('div.brs_col p.nVcaUb a')
    return [search.text for search in related_searches]

# Fonction pour extraire les 10 premiers résultats
def extract_search_results(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    for result in soup.select('div.g')[:10]:
        title = result.select_one('h3')
        if title:
            title = title.text
            link = result.select_one('a')['href']
            snippet = result.select_one('div.VwiC3b')
            if snippet:
                snippet = snippet.text
            else:
                snippet = ""
            results.append({'title': title, 'url': link, 'description': snippet})
    return results

# Fonction principale pour scraper les SERP
def scrape_serp(query, language='fr', country='fr'):
    html = google_search(query, language, country)
    suggestions = get_google_suggest(query, language, country)
    paa = extract_paa(html)
    related_searches = extract_related_searches(html)
    search_results = extract_search_results(html)
    
    return {
        'suggestions': suggestions,
        'paa': paa,
        'related_searches': related_searches,
        'search_results': search_results
    }

def app():
    st.title("Google SERP Scraper")

    # Zone de texte pour les mots-clés
    keywords = st.text_area("Entrez vos mots-clés (un par ligne):")

    if st.button("Exécuter"):
        if keywords:
            keywords_list = keywords.split('\n')
            all_results = []

            progress_bar = st.progress(0)
            for i, keyword in enumerate(keywords_list):
                results = scrape_serp(keyword.strip())
                all_results.append({'keyword': keyword, **results})
                progress_bar.progress((i + 1) / len(keywords_list))
                time.sleep(random.uniform(1, 3))  # Pause aléatoire pour éviter la détection

            # Création du DataFrame
            df = pd.DataFrame(all_results)

            # Affichage des résultats dans Streamlit
            st.write("Résultats:")
            st.dataframe(df)

            # Création du fichier Excel
            excel_file = openpyxl.Workbook()
            writer = pd.ExcelWriter(excel_file, engine='openpyxl')
            df.to_excel(writer, index=False)
            writer.save()

            # Bouton de téléchargement
            st.download_button(
                label="Télécharger les résultats (Excel)",
                data=excel_file,
                file_name="resultats_serp.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Veuillez entrer au moins un mot-clé.")

if __name__ == "__main__":
    app()
