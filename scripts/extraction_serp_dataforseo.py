import streamlit as st
import requests
import base64
import pandas as pd

# Identifiants DataForSEO directement dans le script
login = "mepiden597@hraifi.com"  # Remplacez par votre login
password = "8590a4d1b01fd481"  # Remplacez par votre mot de passe

# Dictionnaire des pays et leurs location_code correspondants
country_mapping = {
    "États-Unis": 2840,
    "France": 2158,
    "Espagne": 2250,
    "Allemagne": 2005,
    "Royaume-Uni": 2826,
    "Italie": 2380,
    "Canada": 2124,
    "Australie": 2036,
}

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
        return response.json()  # Retourne la réponse JSON complète
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

    # Sélection du pays via les noms
    country = st.selectbox("Choisissez le pays", list(country_mapping.keys()))
    location_code = country_mapping[country]  # Récupère le code du pays sélectionné

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
            st.write("Données brutes de l'API (débogage) :")  # Pour déboguer, affichons les données brutes
            st.json(result)  # Affiche la réponse JSON complète

            # Créer un DataFrame avec les résultats
            serp_data = []

            # On vérifie la structure des tâches avant de traiter les résultats
            if "tasks" in result:
                for task in result["tasks"]:
                    if "result" in task:
                        for res in task["result"]:
                            if "items" in res:  # On vérifie aussi si 'items' existe
                                for item in res["items"]:
                                    serp_data.append({
                                        "Keyword": res.get("keyword"),
                                        "Position": item.get("rank_absolute"),
                                        "URL": item.get("url"),
                                        "Domain": item.get("domain"),
                                        "Title": item.get("title")
                                    })
                            else:
                                st.warning(f"Pas d'items trouvés pour la tâche : {task}")
                    else:
                        st.warning(f"Pas de résultats trouvés pour la tâche : {task}")
            else:
                st.error("Aucune tâche trouvée dans la réponse API.")

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
            else:
                st.error("Aucune donnée SERP trouvée.")
        else:
            st.error("Erreur lors de l'extraction des données.")
