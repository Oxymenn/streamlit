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

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erreur lors de la récupération des résultats: {response.status_code} {response.text}")
        return None

# Fonction pour poller l'état d'une tâche jusqu'à ce qu'elle soit terminée
def poll_task(task_id, timeout=300):
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Récupérer les résultats de la tâche
        result = get_serp_results(task_id)

        # Vérifier si la tâche est terminée
        if result and result["tasks"][0]["status_code"] == 20000:
            return result
        else:
            st.info(f"Tâche en cours... (ID : {task_id})")
        
        # Attendre avant de vérifier à nouveau
        time.sleep(10)

    st.error(f"Temps d'attente dépassé pour la tâche {task_id}")
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

                # Polling pour vérifier l'état de la tâche et récupérer les résultats
                serp_result = poll_task(task_id)

                if serp_result:
                    # Traiter les résultats et les afficher
                    serp_data = process_serp_results(serp_result)
                    if serp_data:
                        df = pd.DataFrame(serp_data)
                        st.dataframe(df)

                        # Télécharger les résultats au format CSV
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Télécharger les résultats en CSV",
                            data=csv,
                            file_name="serp_results.csv",
                            mime="text/csv",
                        )
                    else:
                        st.info("Aucun résultat à afficher.")
        else:
            st.warning("Veuillez entrer au moins un mot-clé.")

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

    response = requests.post(url, headers=headers, json=tasks)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erreur lors de la création de la tâche: {response.status_code} {response.text}")
        return None

# Fonction pour ajuster les positions des résultats et créer le dataframe final
def process_serp_results(serp_result):
    serp_data = []
    for res in serp_result.get("tasks", []):
        if "result" in res:
            for item in res["result"]:
                for entry in item["items"]:
                    rank = entry.get("rank_absolute")

                    if entry["type"] == "featured_snippet":
                        rank = 0
                    elif entry["type"] == "organic":
                        rank = max(1, rank)

                    serp_data.append({
                        "Keyword": item.get("keyword"),
                        "Type": entry.get("type"),
                        "Position": rank,
                        "URL": entry.get("url"),
                        "Domain": entry.get("domain"),
                        "Title": entry.get("title")
                    })
    return serp_data

# Si ce fichier est exécuté directement, on appelle la fonction app()
if __name__ == "__main__":
    app()
