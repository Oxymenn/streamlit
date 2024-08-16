import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import requests

# Configuration de Selenium pour fonctionner sans interface graphique
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1366,768')
    options.add_argument("user-agent=Mozilla/5.0")
    return webdriver.Chrome(options=options)

# Fonction pour récupérer les Google Suggest
def get_google_suggests(keyword, language='fr', country='fr'):
    r = requests.get(f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={keyword}')
    soup = BeautifulSoup(r.content, 'html.parser')
    return [sugg['data'] for sugg in soup.find_all('suggestion')]

# Fonction pour scraper les SERP pour un mot-clé donné
def scrape_keyword_data(driver, keyword, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}&oq={keyword}"
    driver.get(url)
    time.sleep(2)  # Temps de chargement de la page

    paa = []
    related_searches = []

    # Scraping des People Also Ask (PAA)
    paa_elements = driver.find_elements(By.CSS_SELECTOR, "[class='xpc']")
    for elem in paa_elements:
        paa.append(elem.text.strip())

    # Scraping des recherches associées
    related_searches_elements = driver.find_elements(By.CSS_SELECTOR, ".Q71vJc")
    for elem in related_searches_elements:
        related_searches.append(elem.text.strip())

    # Scraping des Google Suggest
    suggests = get_google_suggests(keyword, language, country)

    return {
        "keyword": keyword,
        "paa": paa,
        "related_searches": related_searches,
        "suggests": suggests
    }

# Streamlit UI
st.title("Google SERP Scraper")

st.write("Collez vos mots-clés (un par ligne) dans la zone de texte ci-dessous :")

keywords_input = st.text_area("Mots-clés", height=200)
keywords = keywords_input.splitlines()

if st.button("Scraper les données"):
    driver = init_driver()

    data = []
    for keyword in keywords:
        if keyword.strip():  # Ignorer les lignes vides
            st.write(f"Scraping pour le mot-clé : {keyword}")
            result = scrape_keyword_data(driver, keyword)
            data.append(result)
            st.write(f"Données récupérées pour {keyword}")

    driver.quit()

    # Générer le DataFrame et l'exporter en Excel
    df = pd.DataFrame(data)
    df['paa'] = df['paa'].apply(lambda x: "\n".join(x))
    df['related_searches'] = df['related_searches'].apply(lambda x: "\n".join(x))
    df['suggests'] = df['suggests'].apply(lambda x: "\n".join(x))

    st.write(df)

    # Générer le fichier Excel
    excel_file = df.to_excel(index=False, engine='xlsxwriter')
    st.download_button(label="Télécharger le fichier Excel", data=excel_file, file_name="serp_data.xlsx")

    st.success("Scraping terminé et fichier Excel généré avec succès.")

if __name__ == "__main__":
    app()
