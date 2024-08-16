import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO

# Fonction pour récupérer les Google Suggest
def get_google_suggests(keyword, language='fr', country='fr'):
    r = requests.get(f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={language}&gl={country}&q={keyword}')
    soup = BeautifulSoup(r.content, 'html.parser')
    return [sugg['data'] for sugg in soup.find_all('suggestion')]

# Fonction pour récupérer les résultats des recherches associées
def get_related_searches(keyword, language='fr', country='fr'):
    url = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}&oq={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
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
        data = []
        for keyword in keywords:
            if keyword.strip():  # Ignorer les lignes vides
                st.write(f"Scraping pour le mot-clé : {keyword}")
                suggests = get_google_suggests(keyword)
                related_searches, paa = get_related_searches(keyword)
                data.append({
                    "keyword": keyword,
                    "suggests": suggests,
                    "related_searches": related_searches,
                    "paa": paa
                })
                st.write(f"Données récupérées pour {keyword}")

        # Générer le DataFrame
        df = pd.DataFrame(data)
        df['suggests'] = df['suggests'].apply(lambda x: "\n".join(x))
        df['related_searches'] = df['related_searches'].apply(lambda x: "\n".join(x))
        df['paa'] = df['paa'].apply(lambda x: "\n".join(x))

        # Écrire le DataFrame dans un fichier Excel en mémoire avec openpyxl
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            writer.save()
        
        # Positionner le buffer au début du fichier
        output.seek(0)

        # Télécharger le fichier Excel
        st.download_button(
            label="Télécharger le fichier Excel",
            data=output,
            file_name="serp_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.success("Scraping terminé et fichier Excel généré avec succès.")

# Appel de la fonction `app` dans le bloc principal
if __name__ == "__main__":
    app()
