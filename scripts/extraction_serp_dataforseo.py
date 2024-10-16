import streamlit as st
import requests
import base64
import pandas as pd
import time

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
        st.write("Réponse de l'API reçue avec succès :")
        st.json(response.json())  # Afficher la réponse JSON dans Streamlit pour débogage
        return response.json()
    else:
        st.error(f"Erreur lors de la création de la tâche: {response.status_code} {response.text}")
        return None

# Fonction pour récupérer les résultats d'une tâche par ID
def get_serp_results(task_id, result_type="regular"):
    # Encodage des identifiants API en Base64
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

    # URL de l'API DataForSEO pour récupérer les résultats
    url = f"https://api.dataforseo.com/v3/serp/google/organic/task_get/{result_type}/{task_id}"

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

    # Sélection de la langue
    language_code = st.selectbox("Choisissez la langue", ["en", "fr", "es", "de", "it"])

    # Sélection du pays avec des noms lisibles pour l'utilisateur
    countries = {
        "États-Unis": 2840,
        "France": 2250,
        "Allemagne": 2158,
        "Espagne": 2392
    }
    country_name = st.selectbox("Choisissez le pays", list(countries.keys()))
    location_code = countries[country_name]

    # Sélection du type d'appareil
    device = st.radio("Choisissez l'appareil", ["desktop", "mobile"])

    # Choix entre mode Live et Standard
    search_type = st.radio("Méthode d'exécution", ["organic", "live"])

    # Priorité de la tâche
    priority = st.selectbox("Priorité d'exécution", [1, 2])

    # Nombre de résultats à extraire (par tranches de 10)
    depth = st.slider("Nombre de résultats", 10, 100, 10)

    # Choix du type de résultat
    result_type = st.selectbox("Type de résultat", ["regular", "advanced"])

    # Validation des mots-clés
    if st.button("Lancer l'extraction"):
        # Séparer les mots-clés par ligne
        keywords = keywords_input.splitlines()

        # Vérifier si des mots-clés ont été fournis
        if keywords:
            # Extraction des résultats
            result = extract_serp_data(keywords, language_code, location_code, device, priority, search_type, depth)

            if result:
                serp_data = []

                # Itération sur les tâches pour récupérer les résultats
                for task in result.get("tasks", []):
                    task_id = task.get("id")
                    task_status_code = task.get("status_code", None)

                    if task_status_code == 20100:  # Tâche créée avec succès
                        st.write(f"Tâche créée avec succès. ID de la tâche : {task_id}")

                        # Attendre que la tâche soit terminée (polling)
                        while True:
                            serp_result = get_serp_results(task_id, result_type)

                            # Vérifier si la tâche est terminée
                            if serp_result and serp_result["tasks"][0]["status_code"] == 20000:
                                # Si les résultats sont prêts, on arrête la boucle
                                break
                            else:
                                st.info("Tâche en cours d'exécution, veuillez patienter...")
                                time.sleep(5)  # Attente avant de vérifier à nouveau

                        # Ajouter les résultats à serp_data
                        for res in serp_result.get("tasks", []):
                            if "result" in res:
                                for item in res["result"]:
                                    for entry in item["items"]:
                                        serp_data.append({
                                            "Keyword": item.get("keyword"),
                                            "Position": entry.get("rank_absolute"),
                                            "URL": entry.get("url"),
                                            "Domain": entry.get("domain"),
                                            "Title": entry.get("title")
                                        })
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
                    excel_file = df.to_excel(index=False).encode('utf-8')
                    st.download_button(
                        label="Télécharger les résultats en Excel",
                        data=excel_file,
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
