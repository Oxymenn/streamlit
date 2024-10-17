import streamlit as st
import requests
import base64
import pandas as pd
import time

# Identifiants DataForSEO
login = "julesbrault.pro@gmail.com"  # Remplacez par votre login DataForSEO
password = "fa670025004519a1"  # Remplacez par votre mot de passe DataForSEO

# Fonction pour créer une requête d'extraction SERP avec DataForSEO
def extract_serp_data(keywords, language_code, location_code, device, priority, queue_mode, depth):
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

    if queue_mode == "live":
        url = f"https://api.dataforseo.com/v3/serp/google/live/task_post"
    else:
        url = f"https://api.dataforseo.com/v3/serp/google/{queue_mode}/task_post"

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
    try:
        response = requests.post(url, headers=headers, json=tasks)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la création de la tâche : {e}")
        return None

# Fonction pour récupérer les résultats d'une tâche par ID
def get_serp_results(task_id):
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
    url = f"https://api.dataforseo.com/v3/serp/google/organic/task_get/regular/{task_id}"
    
    headers = {"Authorization": f"Basic {credentials}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération des résultats : {e}")
        return None

# Fonction pour afficher le timer et la progression
def display_timer_and_progress(start_time, completed_tasks, total_tasks):
    elapsed_time = int(time.time() - start_time)
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    st.write(f"Temps écoulé : {hours:02}:{minutes:02}:{seconds:02}")
    st.write(f"Mots-clés traités : {completed_tasks}/{total_tasks}")
    st.progress(completed_tasks / total_tasks)

# Fonction principale de l'application Streamlit
def app():
    st.title("Extraction SERP - DataForSEO")

    # Interface utilisateur améliorée
    st.write("Configurez les paramètres d'extraction SERP :")

    keywords_input = st.text_area("Entrez les mots-clés (un par ligne)")

    col1, col2, col3 = st.columns(3)
    with col1:
        language_code = st.selectbox("Langue", ["en", "fr", "es", "de", "it"], label_visibility="collapsed")
    with col2:
        countries = {"États-Unis": 2840, "France": 2250, "Allemagne": 2158, "Espagne": 2392}
        country_name = st.selectbox("Pays", list(countries.keys()), label_visibility="collapsed")
        location_code = countries[country_name]
    with col3:
        device = st.selectbox("Appareil", ["desktop", "mobile"], label_visibility="collapsed")

    col4, col5 = st.columns(2)
    with col4:
        search_type = st.selectbox("Méthode d'exécution", ["organic", "live"], label_visibility="collapsed")
    with col5:
        priority = st.selectbox("Priorité", [1, 2], label_visibility="collapsed")

    # Ajout du choix entre Standard Queue, Priority Queue ou Live Mode
    queue_mode = st.selectbox("Mode de file d'attente", ["standard", "priority", "live"], label_visibility="collapsed")
    
    depth = st.slider("Nombre de résultats", 10, 100, 10)

    if st.button("Lancer l'extraction"):
        keywords = keywords_input.splitlines()
        if keywords:
            result = extract_serp_data(keywords, language_code, location_code, device, priority, queue_mode, depth)

            if result:
                serp_data = []
                total_keywords = len(keywords)
                start_time = time.time()
                completed_tasks = 0

                # Traitement des tâches et résultats
                for task in result.get("tasks", []):
                    task_id = task.get("id")

                    # Polling pour vérifier l'état des tâches
                    while True:
                        serp_result = get_serp_results(task_id)
                        if serp_result and serp_result["tasks"][0]["status_code"] == 20000:
                            break
                        time.sleep(5)

                    completed_tasks += 1
                    display_timer_and_progress(start_time, completed_tasks, total_keywords)

                    # Ajouter les résultats à serp_data en excluant les annonces payantes
                    for res in serp_result.get("tasks", []):
                        if "result" in res:
                            for item in res["result"]:
                                position = 1
                                for entry in item["items"]:
                                    if entry["type"] == "organic" or entry["type"] == "featured_snippet":
                                        rank = entry.get("rank_absolute")
                                        if entry["type"] == "featured_snippet":
                                            rank = 0  # Si featured snippet, position 0
                                        else:
                                            rank = position
                                            position += 1  # Incrémenter la position pour chaque résultat organique

                                        serp_data.append({
                                            "Keyword": item.get("keyword"),
                                            "Position": rank,
                                            "URL": entry.get("url"),
                                            "Domain": entry.get("domain"),
                                            "Title": entry.get("title")
                                        })

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

if __name__ == "__main__":
    app()
