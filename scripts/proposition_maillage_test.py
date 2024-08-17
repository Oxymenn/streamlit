import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import requests
import time
import random
import openpyxl

@st.cache_resource
def setup_driver():
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = FirefoxService(GeckoDriverManager().install())
    return webdriver.Firefox(service=service, options=options)

def get_suggest(keyword, language='fr', country='fr'):
    url = f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={keyword}'
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    return [sugg['data'] for sugg in soup.find_all('suggestion')]

def scrape_serp(driver, keyword, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}"
    driver.get(url)
    
    time.sleep(random.uniform(1, 3))
    
    results = {
        'PAA': [],
        'related_searches': [],
        'suggest': get_suggest(keyword, language, country)
    }
    
    # Scrape PAA
    try:
        paa_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.xpc"))
        )
        for paa in paa_elements:
            results['PAA'].append(paa.text.strip())
    except TimeoutException:
        pass
    
    # Scrape related searches
    try:
        related_searches = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.Q71vJc"))
        )
        for search in related_searches:
            results['related_searches'].append(search.text.strip())
    except TimeoutException:
        pass
    
    return results

def recursive_scrape(driver, keyword, depth, max_depth):
    if depth > max_depth:
        return {}
    
    results = scrape_serp(driver, keyword)
    
    if depth < max_depth:
        for suggest in results['suggest'][:3]:  # Limitation aux 3 premières suggestions
            suggest_results = recursive_scrape(driver, suggest, depth + 1, max_depth)
            for key in suggest_results:
                results[key].extend(suggest_results[key])
    
    return results

def app():
    st.title("Google SERP Scraper")
    
    keywords = st.text_area("Enter keywords (one per line):")
    depth = st.slider("Select depth", 1, 5, 1)  # Limitation à une profondeur de 5
    
    if st.button("Start Scraping"):
        driver = setup_driver()
        
        results = {}
        keywords_list = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
        
        progress_bar = st.progress(0)
        
        for i, keyword in enumerate(keywords_list):
            results[keyword] = recursive_scrape(driver, keyword, 1, depth)
            progress_bar.progress((i + 1) / len(keywords_list))
        
        driver.quit()
        
        # Créer un DataFrame
        df = pd.DataFrame(index=keywords_list, columns=['PAA', 'Related Searches', 'Suggest'])
        
        for keyword in results:
            df.at[keyword, 'PAA'] = ', '.join(results[keyword]['PAA'])
            df.at[keyword, 'Related Searches'] = ', '.join(results[keyword]['related_searches'])
            df.at[keyword, 'Suggest'] = ', '.join(results[keyword]['suggest'])
        
        # Sauvegarder en Excel
        df.to_excel("serp_results.xlsx")
        
        st.success("Scraping completed! Results saved to 'serp_results.xlsx'")
        st.dataframe(df)

if __name__ == "__main__":
    app()
