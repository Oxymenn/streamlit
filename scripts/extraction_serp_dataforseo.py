import requests
import base64
import time
import streamlit as st

# Identifiants API
login = "votre_login_dataforseo"
password = "votre_password_dataforseo"

# Fonction pour créer une tâche SERP
def create_serp_task(keyword, language_code, location_code, device, priority, search_type, depth):
    # Encodage des identifiants API
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

    # URL de l'API
    url = f"https://api.dataforseo.com/v3/serp/google/{search_type}/task_post"

    # Corps de la requête
    post_data = [
        {
            "keyword": keyword,
            "language_code": language_code,
            "location_code": location_code,
            "device": device,
            "priority": priority,
            "depth": depth
        }
    ]

    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=post_data)

    # Si la tâche est bien créée
    if response.status_code == 200:
        task_id = response.json()['tasks'][0]['id']
        st.write(f"Tâche créée avec succès. ID: {task_id}")
        return task_id
    else:
        st.error(f"Erreur lors de la création de la tâche: {response.status_code} {response.text}")
        return None

# Fonction pour récupérer les résultats d'une tâche
def get_serp_results(task_id):
    # Encodage des identifiants API
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

    # URL pour obtenir les résultats
    url = f"https://api.dataforseo.com/v3/serp/google/organic/task_get/regular/{task_id}"

    headers = {
        "Authorization": f"Basic {credentials}",
    }

    # Attendre que la tâche soit terminée
    for _ in range(10):  # Réessaie pendant 10 cycles toutes les 10 secondes
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and response.json().get('tasks'):
            return response.json()['tasks'][0]['result']
        time.sleep(10)

    st.error("La tâche n'est pas terminée après plusieurs tentatives.")
    return None

# Interface Streamlit pour l'extraction SERP
def app():
    st.title("Extraction SERP - DataForSEO")

    # Paramètres de l'utilisateur
    keyword = st.text_input("Entrez le mot-clé")
    language_code = st.selectbox("Choisissez la langue", ["en", "fr", "es", "de", "it"])
    location_code = st.selectbox("Choisissez le pays", {
        "États-Unis": 2840, "France": 2158, "Espagne": 2250, "Allemagne": 2005, "Royaume-Uni": 2826})
    device = st.radio("Choisissez l'appareil", ["desktop", "mobile"])
    search_type = st.radio("Type de recherche", ["organic", "live"])
    priority = st.selectbox("Priorité d'exécution", [1, 2])
    depth = st.slider("Nombre de résultats", 10, 100, 10)

    # Lorsque l'utilisateur lance l'extraction
    if st.button("Lancer l'extraction"):
        task_id = create_serp_task(keyword, language_code, location_code, device, priority, search_type, depth)

        if task_id:
            st.write("Récupération des résultats...")
            results = get_serp_results(task_id)

            if results:
                st.write("Résultats obtenus:")
                for result in results:
                    st.write(f"Position: {result['rank_absolute']}, URL: {result['url']}")

# Lancer l'application
if __name__ == "__main__":
    app()
