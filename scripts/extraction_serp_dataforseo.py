import requests
import base64

# Tes identifiants
login = "mepiden597@hraifi.com"
password = "8590a4d1b01fd481"

# Encodage des identifiants API
credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

# URL d'un simple GET
url = "https://api.dataforseo.com/v3/serp/errors"

headers = {
    "Authorization": f"Basic {credentials}",
}

response = requests.get(url, headers=headers)

# Vérification de la réponse
if response.status_code == 200:
    print("Succès! Tes identifiants sont corrects.")
else:
    print(f"Erreur lors de la connexion: {response.status_code} - {response.text}")
