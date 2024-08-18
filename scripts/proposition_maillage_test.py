import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random

# Configure WebDriver
@st.cache_resource
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    options.add_argument("--window-size=1366,768")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_google_suggests(keyword, language='fr', country='fr'):
    url = f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={keyword}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return [sugg['data'] for sugg in soup.find_all('suggestion')]

def scrape_serp(driver, keyword, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}"
    driver.get(url)
    
    results = {
        'search_results': [],
        'PAA': [],
        'related_searches': [],
        'suggest': get_google_suggests(keyword, language, country)
    }
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div#search')))
        time.sleep(random.uniform(1, 3))
        
        # Scrape search results
        search_results = driver.find_elements(By.CSS_SELECTOR, 'div.g')
        for result in search_results[:10]:
            try:
                title = result.find_element(By.CSS_SELECTOR, 'h3').text
                link = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                snippet = result.find_element(By.CSS_SELECTOR, 'div.IsZvec').text
                results['search_results'].append({'title': title, 'link': link, 'snippet': snippet})
            except Exception:
                continue

        # Scrape PAA
        try:
            paa_elements = driver.find_elements(By.CSS_SELECTOR, "div.related-question-pair")
            for paa in paa_elements:
                question = paa.find_element(By.CSS_SELECTOR, 'div').text
                results['PAA'].append(question)
        except Exception:
            pass

        # Scrape related searches
        try:
            related_searches_elements = driver.find_elements(By.CSS_SELECTOR, 'p.nVcaUb')
            for search in related_searches_elements:
                results['related_searches'].append(search.text.strip())
        except Exception:
            pass
    
    except TimeoutException:
        st.error("Timeout while loading Google SERP")
    
    return results

def app():
    st.title("Google SERP Scraper")
    
    keywords = st.text_area("Enter keywords (one per line):")
    depth = st.slider("Select scraping depth", 1, 5, 1)
    
    if st.button("Start Scraping"):
        driver = setup_driver()
        keywords_list = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
        
        progress_bar = st.progress(0)
        results = {}
        
        for i, keyword in enumerate(keywords_list):
            st.info(f"Scraping keyword: {keyword}")
            results[keyword] = scrape_serp(driver, keyword)
            progress_bar.progress((i + 1) / len(keywords_list))
        
        driver.quit()
        
        # Prepare DataFrame
        data = {
            'Keyword': [],
            'Title': [],
            'Link': [],
            'Snippet': [],
            'PAA': [],
            'Related Searches': [],
            'Suggest': []
        }
        
        for keyword, result in results.items():
            for res in result['search_results']:
                data['Keyword'].append(keyword)
                data['Title'].append(res['title'])
                data['Link'].append(res['link'])
                data['Snippet'].append(res['snippet'])
                data['PAA'].append(', '.join(result['PAA']))
                data['Related Searches'].append(', '.join(result['related_searches']))
                data['Suggest'].append(', '.join(result['suggest']))
        
        df = pd.DataFrame(data)
        
        # Save to Excel
        df.to_excel("serp_results.xlsx", index=False)
        
        st.success("Scraping completed! Results saved to 'serp_results.xlsx'")
        st.dataframe(df)

if __name__ == "__main__":
    app()
