import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
from io import BytesIO

# Liste d'exemples de User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

# Liste d'exemples de proxies
PROXIES = [
    "http://111.222.333.444:8080",
    "http://555.666.777.888:3128",
    "http://999.888.777.666:8080",
    # Ajoutez ici vos propres proxies
]

# Fonction pour récupérer les Google Suggest
def get_google_suggests(keyword, language='fr', country='fr'):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    proxy = {"http": random.choice(PROXIES), "https": random.choice(PROXIES)}
    
    r = requests.get(f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={keyword}', headers=headers, proxies=proxy)
    soup = BeautifulSoup(r.content, 'html.parser')
    return [sugg['data'] for sugg in soup.find_all('suggestion')]

# Fonction pour récupérer les résultats des recherches associées
def get_related_searches(keyword, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}&oq={keyword}"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    proxy = {"http": random.choice(PROXIES), "https": random.choice(PROXIES)}
    
    response = requests.get(url, headers=headers, proxies=proxy)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    related_searches = []
    for suggestion in soup.select('.Q71vJc'):
        related_searches.append(suggestion.get_text())
    
    paa = []
    for question in soup.select('.xpc'):
        paa.append(question.get_text())
    
    return related_searches, paa

# Définition de la fonction principale `app`
def app():
    st.title("Google SERP Scraper")

    st.write("Collez vos mots-clés (un par ligne) dans la zone de texte ci-dessous :")

    keywords_input = st.text_area("Mots-clés", height=200)
    keywords = keywords_input.splitlines()

    if st.button("Scraper les données"):
        start_time = time.time()  # Démarrer le chronomètre
        total_keywords = len(keywords)
        progress_bar = st.progress(0)
        status_text = st.empty()
        timer_text = st.empty()

        data = []
        for i, keyword in enumerate(keywords):
            if keyword.strip():  # Ignorer les lignes vides
                suggests = get_google_suggests(keyword)
                related_searches, paa = get_related_searches(keyword)
                data.append({
                    "keyword": keyword,
                    "suggests": suggests,
                    "related_searches": related_searches,
                    "paa": paa
                })
            
            # Mise à jour de la barre de progression
            progress = (i + 1) / total_keywords
            progress_bar.progress(progress)

            # Calcul du temps écoulé et estimation du temps restant
            elapsed_time = time.time() - start_time
            estimated_total_time = elapsed_time / progress
            remaining_time = estimated_total_time - elapsed_time

            # Conversion du temps en heures, minutes, secondes
            elapsed_time_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
            remaining_time_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))

            # Mise à jour du texte d'état et du timer
            status_text.text(f"Scraping {i+1} sur {total_keywords} mots-clés")
            timer_text.text(f"Temps écoulé: {elapsed_time_str} | Temps restant estimé: {remaining_time_str}")

        # Générer le DataFrame
        df = pd.DataFrame(data)
        df['suggests'] = df['suggests'].apply(lambda x: "\n".join(x))
        df['related_searches'] = df['related_searches'].apply(lambda x: "\n".join(x))
        df['paa'] = df['paa'].apply(lambda x: "\n".join(x))

        # Écrire le DataFrame directement dans un fichier Excel
        file_name = "serp_data.xlsx"
        df.to_excel(file_name, index=False, engine='openpyxl')

        # Télécharger le fichier Excel
        with open(file_name, "rb") as file:
            st.download_button(
                label="Télécharger le fichier Excel",
                data=file,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.success("Scraping terminé et fichier Excel généré avec succès.")

# Appel de la fonction `app` dans le bloc principal
if __name__ == "__main__":
    app()
