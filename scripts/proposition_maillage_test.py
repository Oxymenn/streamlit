import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random

# Liste d'exemples de User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

# Initialisation des variables globales
scrapeado = []

# Fonction pour récupérer les Google Suggest
def get_google_suggests(keyword, language, country):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    url = f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={keyword}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    return [sugg['data'] for sugg in soup.find_all('suggestion')]

# Fonction pour scraper les résultats de recherche
def scrape_serp(keyword, language, country):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}&oq={keyword}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    paa = []
    related_searches = []

    # Scraping des People Also Ask (PAA)
    paa_elements = soup.select('.xpc')
    for elem in paa_elements:
        text = elem.get_text(strip=True)
        paa.append(text)

    # Scraping des recherches associées
    related_searches_elements = soup.select('.Q71vJc')
    for elem in related_searches_elements:
        text = elem.get_text(strip=True)
        related_searches.append(text)
    
    # Scraping des Google Suggest
    suggests = get_google_suggests(keyword, language, country)

    return paa, related_searches, suggests

# Fonction pour gérer la boucle de scraping à plusieurs niveaux
def scrape_loop(keyword, language, country, scrapeLevels):
    all_suggests = []
    queue = [(keyword, 0)]
    seen_paa = {}
    seen_related_searches = {}

    while queue:
        current_keyword, current_level = queue.pop(0)
        if current_keyword.lower() in scrapeado:
            continue

        paa, related_searches, suggests = scrape_serp(current_keyword, language, country)
        
        # Ajouter les suggest au niveau actuel
        if current_level > 0:  # Ne pas ajouter le mot-clé de départ
            all_suggests.append(current_keyword)

        # Empêcher le scraping en double
        scrapeado.append(current_keyword.lower())

        if current_level < scrapeLevels:
            for suggest in suggests:
                # Vérifier si les PAA et les recherches associées sont différents pour éviter la redondance
                if (suggest not in seen_paa or paa != seen_paa.get(suggest)) and \
                   (suggest not in seen_related_searches or related_searches != seen_related_searches.get(suggest)):
                    seen_paa[suggest] = paa
                    seen_related_searches[suggest] = related_searches
                    queue.append((suggest, current_level + 1))

    return all_suggests

# Définition de la fonction principale `app`
def app():
    st.title("Google SERP Scraper Avancé")

    # Sélecteurs pour la langue, le pays, et autres paramètres
    language = st.selectbox("Sélectionnez la langue pour le scraping", options=["fr", "en", "es", "de", "it", "pt"])
    country = st.selectbox("Sélectionnez le pays pour le scraping", options=["fr", "us", "es", "de", "it", "pt"])
    scrapeLevels = st.slider("Niveaux de scraping (scrapeLevels)", 1, 5, 3)

    st.write("Collez vos mots-clés (un par ligne) dans la zone de texte ci-dessous :")

    keywords_input = st.text_area("Mots-clés", height=200)
    keywords = keywords_input.splitlines()
    
    # Affichage du nombre de mots-clés
    num_keywords = len([k for k in keywords if k.strip()])  # Ne compte que les lignes non vides
    st.write(f"Nombre de mots-clés copiés : {num_keywords}")

    if st.button("Scraper les données"):
        start_time = time.time()  # Démarrer le chronomètre
        total_keywords = num_keywords
        progress_bar = st.progress(0)
        status_text = st.empty()
        timer_text = st.empty()

        data = []
        for i, keyword in enumerate(keywords):
            if keyword.strip():  # Ignorer les lignes vides
                all_suggests = scrape_loop(keyword, language, country, scrapeLevels)
                data.append({
                    "keyword": keyword,
                    "suggests": "\n".join(all_suggests)
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

