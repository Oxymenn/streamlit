import streamlit as st
import requests
import base64
import pandas as pd

# Identifiants DataForSEO directement inclus
login = "mepiden597@hraifi.com"  # Remplace par ton login DataForSEO
password = "8590a4d1b01fd481"  # Remplace par ton mot de passe DataForSEO

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

                # Itération sur les tâches
                for task in result.get("tasks", []):
                    status_code = task.get("status_code", None)
                    if status_code == 20000:
                        # La tâche s'est exécutée avec succès, traitement des résultats
                        for res in task.get("result", []):
                            for item in res.get("items", []):
                                serp_data.append({
                                    "Keyword": res.get("keyword"),
                                    "Position": item.get("rank_absolute"),
                                    "URL": item.get("url"),
                                    "Domain": item.get("domain"),
                                    "Title": item.get("title")
                                })
                    else:
                        # Message d'erreur si la tâche a échoué
                        st.warning(f"Tâche échouée avec le statut : {status_code}")

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
                    st.info("Aucun résultat à afficher.")
        else:
            st.warning("Veuillez entrer au moins un mot-clé.")

# Si ce fichier est exécuté directement, on appelle la fonction app()
if __name__ == "__main__":
    app()
