import streamlit as st
import requests
import base64
import pandas as pd
import time

# Identifiants DataForSEO
login = "julesbrault.pro@gmail.com"  # Remplace par ton login DataForSEO
password = "fa670025004519a1"  # Remplace par ton mot de passe DataForSEO

# Fonction pour récupérer les résultats d'une tâche par ID
def get_serp_results(task_id, result_type="regular"):
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
    url = f"https://api.dataforseo.com/v3/serp/google/organic/task_get/{result_type}/{task_id}"

    headers = {
        "Authorization": f"Basic {credentials}"
    }

    st.write(f"Récupération des résultats pour la tâche {task_id}...")
    response = requests.get(url, headers=headers)

    st.write(f"Code réponse lors de la récupération des résultats : {response.status_code}")
    st.write(f"Réponse brute lors de la récupération : {response.text}")

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erreur lors de la récupération des résultats: {response.status_code} {response.text}")
        return None

# Fonction pour créer une requête d'extraction SERP avec DataForSEO
def extract_serp_data(keywords, language_code, location_code, device, priority, search_type, depth):
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
    url = f"https://api.dataforseo.com/v3/serp/google/{search_type}/task_post"

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

    st.write("Données envoyées à l'API pour la création de tâche :")
    st.write(tasks)

    # Envoi de la requête
    response = requests.post(url, headers=headers, json=tasks)
    st.write(f"Code réponse lors de la création de la tâche : {response.status_code}")
    st.write(f"Réponse brute lors de la création : {response.text}")

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erreur lors de la création de la tâche: {response.status_code} {response.text}")
        return None

# Fonction pour vérifier manuellement le statut de la tâche
def check_task_status(task_id):
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
    url = f"https://api.dataforseo.com/v3/serp/google/organic/task_get/regular/{task_id}"

    headers = {
        "Authorization": f"Basic {credentials}"
    }

    st.write(f"Vérification du statut pour la tâche {task_id}...")
    response = requests.get(url, headers=headers)
    st.write(f"Code réponse statut : {response.status_code}")
    st.write(f"Réponse brute statut : {response.text}")

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erreur lors de la vérification du statut: {response.status_code} {response.text}")
        return None

# Fonction principale de l'application Streamlit
def app():
    st.title("Extraction SERP - DataForSEO")

    # Interface utilisateur
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
            # Créer une tâche d'extraction via l'API
            result = extract_serp_data(keywords, language_code, location_code, device, priority, search_type, depth)

            if result:
                # Récupérer l'ID de la tâche
                task_id = result["tasks"][0]["id"]
                st.info(f"Tâche créée avec succès, ID : {task_id}")

                # Vérifier manuellement l'état de la tâche
                if st.button(f"Vérifier l'état de la tâche {task_id}"):
                    check_task_status(task_id)

        else:
            st.warning("Veuillez entrer au moins un mot-clé.")

# Si ce fichier est exécuté directement, on appelle la fonction app()
if __name__ == "__main__":
    app()
