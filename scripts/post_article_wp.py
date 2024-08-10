import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse

def app():
    st.title("Publier un article sur WordPress")

    try:
        wp_url = st.secrets["wordpress"]["url"].rstrip('/xmlrpc.php')
        wp_username = st.secrets["wordpress"]["username"]
        wp_password = st.secrets["wordpress"]["password"]
        
        # Vérification et correction de l'URL
        parsed_url = urlparse(wp_url)
        if not parsed_url.scheme:
            wp_url = "https://" + wp_url
        if not wp_url.endswith('.fr'):
            wp_url += '.fr'
        
        st.write(f"URL utilisée : {wp_url}")  # Pour le débogage
    except KeyError:
        st.error("Erreur : Les secrets WordPress ne sont pas configurés correctement.")
        return

    def publish_post_rest(title, content):
        api_url = f"{wp_url}/wp-json/wp/v2/posts"
        auth = HTTPBasicAuth(wp_username, wp_password)
        headers = {'Content-Type': 'application/json'}
        data = {
            'title': title,
            'content': content,
            'status': 'publish'
        }
        response = requests.post(api_url, json=data, headers=headers, auth=auth)
        if response.status_code == 201:
            return response.json()['id']
        else:
            raise Exception(f"Erreur HTTP {response.status_code}: {response.text}")

    title = st.text_input("Titre de l'article")
    content = st.text_area("Contenu de l'article")

    if st.button("Publier"):
        try:
            post_id = publish_post_rest(title, content)
            st.success(f"Article publié avec succès via l'API REST! ID: {post_id}")
        except Exception as e:
            st.error(f"Erreur lors de la publication : {str(e)}")

if __name__ == "__main__":
    app()
