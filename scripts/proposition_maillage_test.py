import streamlit as st
import os
import requests  # Importation ajoutée
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import random
import pandas as pd

# Fonction pour installer chromedriver et configurer Chrome
@st.cache_resource
def install_chromedriver():
    os.system('sbase install chromedriver')
    os.system('ln -s /home/appuser/venv/lib/python3.7/site-packages/seleniumbase/drivers/chromedriver /home/appuser/venv/bin/chromedriver')

_ = install_chromedriver()

# Configuration de Selenium pour utiliser Chrome avec l'option headless
def init_driver():
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    return webdriver.Chrome(options=options)

# Liste d'exemples de User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

# Fonction pour récupérer les Google Suggest
def get_google_suggests(keyword, language, country):
    url = f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={keyword}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return [sugg['data'] for sugg in soup.find_all('suggestion')]

# Fonction pour scraper les résultats de recherche
def scrape_serp(driver, keyword, language, country):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}&oq={keyword}"
    driver.get(url)
    time.sleep(random.randint(1, 3))  # Attente pour éviter de déclencher les captchas

    paa = []
    related_searches = []

    try:
        # Scraping des People Also Ask (PAA)
        paa_elements = driver.find_elements(By.CSS_SELECTOR, "[class='xpc']")
        for elem in paa_elements:
            paa.append(elem.text.strip())

        # Scraping des recherches associées
        related_searches_elements = driver.find_elements(By.CSS_SELECTOR, ".Q71vJc")
        for elem in related_searches_elements:
            related_searches.append(elem.text.strip())
    except Exception as e:
        st.write(f"Erreur lors du scraping: {e}")

    suggests = get_google_suggests(keyword, language, country)

    return paa, related_searches, suggests

# Fonction pour gérer la boucle de scraping à plusieurs niveaux
def scrape_loop(driver, keyword, language, country, scrapeLevels):
    all_suggests = []
    all_paa = []
    all_related_searches = []
    queue = [(keyword, 0)]
    seen_keywords = set()

    while queue:
        current_keyword, current_level = queue.pop(0)
        if current_keyword.lower() in seen_keywords:
            continue

        paa, related_searches, suggests = scrape_serp(driver, current_keyword, language, country)
        
        if current_level > 0:  # Ne pas ajouter le mot-clé de départ
            all_suggests.append(current_keyword)
            all_paa.extend(paa)
            all_related_searches.extend(related_searches)

        seen_keywords.add(current_keyword.lower())

        if current_level < scrapeLevels:
            for suggest in suggests:
                if suggest.lower() not in seen_keywords:
                    queue.append((suggest, current_level + 1))

    return all_suggests, all_paa, all_related_searches

# Fonction principale pour Streamlit
def app():
    st.title("Google SERP Scraper Avancé")

    language = st.selectbox("Sélectionnez la langue pour le scraping", options=["fr", "en", "es", "de", "it", "pt"])
    country = st.selectbox("Sélectionnez le pays pour le scraping", options=["fr", "us", "es", "de", "it", "pt"])
    scrapeLevels = st.slider("Niveaux de scraping (scrapeLevels)", 1, 5, 3)

    st.write("Collez vos mots-clés (un par ligne) dans la zone de texte ci-dessous :")
    keywords_input = st.text_area("Mots-clés", height=200)
    keywords = [k.strip() for k in keywords_input.splitlines() if k.strip()]

    st.write(f"Nombre de mots-clés copiés : {len(keywords)}")

    if st.button("Scraper les données"):
        driver = init_driver()

        data = []
        for keyword in keywords:
            all_suggests, all_paa, all_related_searches = scrape_loop(driver, keyword, language, country, scrapeLevels)
            data.append({
                "keyword": keyword,
                "suggests": "\n".join(all_suggests),
                "paa": "\n".join(all_paa),
                "related_searches": "\n".join(all_related_searches)
            })
        
        driver.quit()

        if data:
            df = pd.DataFrame(data)
            file_name = "serp_data.xlsx"
            df.to_excel(file_name, index=False, engine='openpyxl')

            st.download_button(
                label="Télécharger le fichier Excel",
                data=open(file_name, "rb"),
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.success("Scraping terminé et fichier Excel généré avec succès.")
        else:
            st.warning("Aucune donnée n'a été récupérée. Veuillez vérifier les paramètres et réessayer.")

# Exécution de l'application
if __name__ == "__main__":
    app()
