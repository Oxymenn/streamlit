import streamlit as st
import requests
import base64
import pandas as pd
import time

# Identifiants DataForSEO
login = "julesbrault.pro@gmail.com"  # Remplace par ton login DataForSEO
password = "fa670025004519a1"  # Remplace par ton mot de passe DataForSEO

# Fonction pour tester la connexion API
def test_api_connection():
    try:
        credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
        url = "https://api.dataforseo.com/v3/serp/google/organic/task_get"
        headers = {
            "Authorization": f"Basic {credentials}",
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            st.success("Connexion à l'API réussie")
        else:
            st.error(f"Erreur de connexion à l'API: {response.status_code} {response.text}")
    
    except Exception as e:
        st.error(f"Erreur lors de la tentative de connexion à l'API : {e}")

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

    # Affichage pour le débogage
    st.write("Données envoyées à l'API :")
    st.write(tasks)
    
    # Envoi de la requête
    try:
        response = requests.post(url, headers=headers, json=tasks)
        st.write(f"Code réponse API: {response.status_code}")
        st.write(f"Réponse brute : {response.text}")

        if response.status_code == 200:
            st.info("Tâche créée avec succès")
            return response.json()  # On ne l'affiche plus, mais on retourne la réponse
        else:
            st.error(f"Erreur lors de la création de la tâche: {response.status_code} {response.text}")
            return None
    except Exception as e:
        st.error(f"Erreur lors de la requête API : {e}")
        return None

# Fonction principale de l'application Streamlit
def app():
    st.title("Extraction SERP - DataForSEO")

    # Tester la connexion à l'API
    if st.button("Tester la connexion à l'API"):
        test_api_connection()

    # Interface utilisateur pour l'extraction SERP
    st.write("Configurez les paramètres d'extraction SERP :")
    
    keywords_input = st.text_area("Entrez les mots-clés (un par ligne)")
    col1, col2, col3 = st.columns(3)

    with col1:
        language_code = st.selectbox("Langue", ["en", "fr", "es", "de", "it"], label_visibility="collapsed")

    with col2:
        countries = {
            "États-Unis": 2840,
            "France": 2250,
            "Allemagne": 2158,
            "Espagne": 2392
        }
        country_name = st.selectbox("Pays", list(countries.keys()), label_visibility="collapsed")
        location_code = countries[country_name]

    with col3:
        device = st.selectbox("Appareil", ["desktop", "mobile"], label_visibility="collapsed")

    col4, col5 = st.columns(2)
    with col4:
        search_type = st.selectbox("Méthode d'exécution", ["organic", "live"], label_visibility="collapsed")
    with col5:
        priority = st.selectbox("Priorité", [1, 2], label_visibility="collapsed")

    depth = st.slider("Nombre de résultats", 10, 100, 10)

    if st.button("Lancer l'extraction"):
        keywords = keywords_input.splitlines()
        if keywords:
            result = extract_serp_data(keywords, language_code, location_code, device, priority, search_type, depth)

            if result:
                st.write("Tâches retournées :")
                st.write(result)
            else:
                st.error("Erreur lors de l'extraction SERP.")
        else:
            st.warning("Veuillez entrer au moins un mot-clé.")

# Si ce fichier est exécuté directement, on appelle la fonction app()
if __name__ == "__main__":
    app()
