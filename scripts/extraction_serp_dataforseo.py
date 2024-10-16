import streamlit as st
import requests
import base64
import json
import pandas as pd
import time

# Récupérer le login et le mot de passe depuis les secrets
dataforseo_login = st.secrets["dataforseo_login"]
dataforseo_password = st.secrets["dataforseo_password"]

# Encoder en base64
auth = base64.b64encode(f'{dataforseo_login}:{dataforseo_password}'.encode('utf-8')).decode('utf-8')

# Fonction pour appeler l'API DataForSEO
def create_task(api_url, auth, payload):
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    response = requests.post(api_url, headers=headers, json=payload)
    return response.json()

# Fonction pour récupérer les résultats via l'API
def get_results(api_url, auth):
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    response = requests.get(api_url, headers=headers)
    return response.json()

# Fonction principale pour gérer la création des tâches et la récupération des résultats
def process_keywords(keywords, language_code, location_code, device, priority, mode, depth):
    api_url_task = 'https://api.dataforseo.com/v3/serp/google/organic/task_post'
    tasks = []
    
    # Créer les tâches pour chaque mot-clé
    for keyword in keywords:
        task_payload = {
            "language_code": language_code,
            "location_code": location_code,
            "keyword": keyword.strip(),
            "device": device,
            "priority": priority,
            "depth": depth
        }
        task_response = create_task(api_url_task, auth, [task_payload])
        task_id = task_response['tasks'][0]['id']
        tasks.append(task_id)

    # Attendre les résultats pour chaque tâche
    results = []
    for task_id in tasks:
        api_url_result = f"https://api.dataforseo.com/v3/serp/google/organic/task_get/regular/{task_id}"
        task_result = None
        while not task_result:
            task_result = get_results(api_url_result, auth)
            if task_result['status_code'] == 20000:
                results.append(task_result['tasks'][0]['result'])
            else:
                time.sleep(5)  # Attendre avant de vérifier à nouveau

    # Extraction des informations et création du DataFrame
    extracted_data = []
    for result in results:
        for item in result:
            for serp_item in item['items']:
                extracted_data.append({
                    "Keyword": item['keyword'],
                    "Position": serp_item['rank_absolute'],
                    "URL": serp_item['url'],
                    "Domain": serp_item['domain'],
                    "Title": serp_item['title']
                })

    # Créer un dataframe et le convertir en fichier CSV
    df = pd.DataFrame(extracted_data)
    df.to_csv('serp_results.csv', index=False)
    return df

# Interface utilisateur avec Streamlit
st.title('SERP Extractor - Google Organic Results')

# Sélection des paramètres
language = st.selectbox('Choisir la langue', ['en', 'fr', 'es', 'de', 'it'])
country = st.selectbox('Choisir le pays', ['France', 'United States', 'Germany', 'Spain', 'Italy'])
device = st.radio('Type d\'appareil', ['desktop', 'mobile'])
priority = st.radio('Priorité d\'exécution', ['Normal', 'Haute'])
mode = st.radio('Mode d\'exécution', ['Standard', 'Live'])
depth = st.slider('Nombre de résultats par mot-clé', 10, 100, 100, step=10)

# Zone de texte pour les mots-clés
keywords_input = st.text_area('Mots-clés (1 par ligne)')

# Si l'utilisateur clique sur le bouton "Exécuter"
if st.button('Exécuter'):
    if keywords_input:
        keywords = keywords_input.splitlines()
        
        # Traduire le pays en code de localisation pour DataforSEO
        location_code = {'France': 2250, 'United States': 2840, 'Germany': 1299, 'Spain': 2297, 'Italy': 2163}[country]
        
        # Traduire la priorité
        priority_code = 1 if priority == 'Normal' else 2
        
        # Exécuter le processus et afficher le dataframe
        df = process_keywords(keywords, language, location_code, device, priority_code, mode, depth)
        
        st.write('Résultats obtenus :')
        st.dataframe(df)

        # Lien pour télécharger le CSV
        st.download_button("Télécharger les résultats en CSV", data=df.to_csv(), file_name="serp_results.csv", mime='text/csv')

