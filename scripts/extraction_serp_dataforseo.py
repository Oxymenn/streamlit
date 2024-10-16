import streamlit as st
import requests
import base64
import pandas as pd
import os

# Utilisation des secrets pour récupérer le login et password
login = st.secrets["login"]
password = st.secrets["password"]

# Fonction pour créer une requête d'extraction SERP avec DataForSEO
def extract_serp_data(keywords, language_code, location_code, device, priority, search_type, depth):
    # Encodage des identifiants API en Base64
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

    # URL de l'API DataForSEO
    url = f"https://api.dataforseo.com/v3/serp/google/{search_type}/task_post"

    # Préparation des données de la requête
    tasks = [
        {
            "language_code": language_code,
            "location_code": location_code,
            "keyword": keyword,
            "device": device,
            "priority": priority,
            "depth": depth
        }
        for keyword in keywords
    ]

    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }

    # Envoi de la requête
    response = requests.post(url, headers=headers, json=tasks)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erreur lors de l'extraction des données SERP : {response.status_code}")
        return None

# Fonction principale de l'application
def app():
    st.title("Extraction SERP - DataForSEO")

    # Interface utilisateur
    st.write("Configurez les paramètres d'extraction SERP :")

    # Zone de texte pour les mots-clés (un mot clé par ligne)
    keywords_input = st.text_area("Entrez les mots-clés (un par ligne)")

    # Sélection de la langue
    language_code = st.selectbox("Choisissez la langue", ["en", "fr", "es", "de", "it"])

    # Sélection du pays
    location_code = st.selectbox("Choisissez le pays", [2840, 2158, 2250, 2392])  # Exemple : US, France, Espagne, Allemagne

    # Sélection du type d'appareil
    device = st.radio("Choisissez l'appareil", ["desktop", "mobile"])

    # Choix entre mode Live et Standard
    search_type = st.radio("Méthode d'exécution", ["organic", "live"])

    # Priorité de la tâche
    priority = st.selectbox("Priorité d'exécution", [1, 2])

    # Nombre de résultats à extraire (par tranches de 10)
    depth = st.slider("Nombre de résultats", 10, 100, 10)

    # Validation des mots-clés
    if st.button("Lancer l'extraction"):
        # Séparer les mots-clés par ligne
        keywords = keywords_input.splitlines()

        # Extraction des résultats
        result = extract_serp_data(keywords, language_code, location_code, device, priority, search_type, depth)

        if result:
            # Créer un DataFrame avec les résultats
            serp_data = []
            for task in result.get("tasks", []):
                for res in task.get("result", []):
                    for item in res.get("items", []):
                        serp_data.append({
                            "Keyword": res.get("keyword"),
                            "Position": item.get("rank_absolute"),
                            "URL": item.get("url"),
                            "Domain": item.get("domain"),
                            "Title": item.get("title")
                        })

            # Créer un DataFrame pandas
            df = pd.DataFrame(serp_data)

            # Afficher les résultats sous forme de tableau dans l'interface
            st.dataframe(df)

            # Télécharger les résultats au format CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger les résultats en CSV",
                data=csv,
                file_name="serp_results.csv",
                mime="text/csv",
            )

