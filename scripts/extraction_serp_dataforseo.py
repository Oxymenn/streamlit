import streamlit as st
import requests
import base64
import pandas as pd
import time
import io  # Import necessary for handling Excel export in memory

# Identifiants DataForSEO
login = "julesbrault.pro@gmail.com"  # Remplace par ton login DataForSEO
password = "fa670025004519a1"  # Remplace par ton mot de passe DataForSEO

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
        return response.json()  # Return the task creation result silently
    else:
        st.error(f"Erreur lors de la création de la tâche: {response.status_code} {response.text}")
        return None

# Fonction pour récupérer les résultats d'une tâche par ID
def get_serp_results(task_id):
    # Encodage des identifiants API en Base64
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

    # URL de l'API DataForSEO pour récupérer les résultats (toujours en regular)
    url = f"https://api.dataforseo.com/v3/serp/google/organic/task_get/regular/{task_id}"

    headers = {
        "Authorization": f"Basic {credentials}"
    }

    # Envoi de la requête GET
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erreur lors de la récupération des résultats: {response.status_code} {response.text}")
        return None

# Fonction principale de l'application Streamlit
def app():
    st.title("Extraction SERP - DataForSEO")

    # Interface utilisateur
    st.write("Configurez les paramètres d'extraction SERP :")

    # Zone de texte pour les mots-clés (un mot clé par ligne)
    keywords_input = st.text_area("Entrez les mots-clés (un par ligne)")

    # Agencement sur une même ligne pour la langue, le pays, et le type d'appareil
    col1, col2, col3 = st.columns(3)

    # Sélection de la langue
    with col1:
        language_code = st.selectbox("Langue", ["en", "fr", "es", "de", "it"])

    # Sélection du pays
    with col2:
        countries = {
            "États-Unis": 2840,
            "France": 2250,
            "Allemagne": 2158,
            "Espagne": 2392
        }
        country_name = st.selectbox("Pays", list(countries.keys()))
        location_code = countries[country_name]

    # Sélection du type d'appareil
    with col3:
        device = st.selectbox("Appareil", ["desktop", "mobile"])

    # Agencement sur une même ligne pour la méthode d'exécution et la priorité
    col4, col5 = st.columns(2)

    # Méthode d'exécution
    with col4:
        search_type = st.selectbox("Méthode d'exécution", ["organic", "live"])

    # Priorité de la tâche
    with col5:
        priority = st.selectbox("Priorité", [1, 2])

    # Nombre de résultats à extraire (par tranches de 10)
    depth = st.slider("Nombre de résultats", 10, 100, 10)

    # Validation des mots-clés
    if st.button("Lancer l'extraction"):
        # Séparer les mots-clés par ligne
        keywords = keywords_input.splitlines()

        # Vérifier si des mots-clés ont été fournis
        if keywords:
            total_keywords = len(keywords)
            serp_data = []
            start_time = time.time()

            # Barre de progression
            progress_bar = st.progress(0)
            timer_placeholder = st.empty()
            processed_keywords = 0

            # Extraction des résultats
            result = extract_serp_data(keywords, language_code, location_code, device, priority, search_type, depth)

            if result:
                # Itération sur les tâches pour récupérer les résultats
                for task in result.get("tasks", []):
                    task_id = task.get("id")
                    task_status_code = task.get("status_code", None)

                    if task_status_code == 20100:  # Tâche créée avec succès
                        # Polling pour vérifier l'état de la tâche
                        while True:
                            serp_result = get_serp_results(task_id)

                            # Vérifier si la tâche est terminée
                            if serp_result and serp_result["tasks"][0]["status_code"] == 20000:
                                # Si les résultats sont prêts, on arrête la boucle
                                break
                            else:
                                # Mettre à jour le timer et attendre avant de vérifier à nouveau
                                elapsed_time = time.time() - start_time
                                timer_placeholder.write(f"Temps écoulé : {int(elapsed_time // 3600):02d}:{int((elapsed_time % 3600) // 60):02d}:{int(elapsed_time % 60):02d}")
                                time.sleep(5)

                        # Ajouter les résultats à serp_data
                        for res in serp_result.get("tasks", []):
                            if "result" in res:
                                for item in res["result"]:
                                    # Ajuster les positions pour que le premier résultat organique soit 1
                                    for entry in item["items"]:
                                        rank = entry.get("rank_absolute", None)
                                        if rank and entry.get("type") == "organic":
                                            adjusted_rank = 1 if rank == 0 else rank - 1
                                            serp_data.append({
                                                "Keyword": item.get("keyword"),
                                                "Position": adjusted_rank,
                                                "URL": entry.get("url"),
                                                "Domain": entry.get("domain"),
                                                "Title": entry.get("title")
                                            })

                        # Mettre à jour la barre de progression et le nombre de mots-clés traités
                        processed_keywords += 1
                        progress_bar.progress(processed_keywords / total_keywords)
                        st.write(f"Mots-clés traités : {processed_keywords}/{total_keywords}")

                    else:
                        st.warning(f"Tâche échouée avec le statut : {task_status_code}")

                if serp_data:
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

                    # Télécharger les résultats au format Excel
                    excel_buffer = io.BytesIO()  # Créer un buffer en mémoire pour les données Excel
                    df.to_excel(excel_buffer, index=False)  # Écrire le fichier Excel dans le buffer
                    excel_buffer.seek(0)  # Remettre le curseur au début du buffer

                    st.download_button(
                        label="Télécharger les résultats en Excel",
                        data=excel_buffer,
                        file_name="serp_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                else:
                    st.info("Aucun résultat à afficher.")
        else:
            st.warning("Veuillez entrer au moins un mot-clé.")

# Si ce fichier est exécuté directement, on appelle la fonction app()
if __name__ == "__main__":
    app()
