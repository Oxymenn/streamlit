import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse, urlunparse

def app():
    st.title("Publier un article sur WordPress")

    try:
        # Récupération de l'URL brute depuis les secrets
        raw_url = st.secrets["wordpress"]["url"]
        wp_username = st.secrets["wordpress"]["username"]
        wp_password = st.secrets["wordpress"]["password"]
        
        # Parsing et reconstruction de l'URL
        parsed_url = urlparse(raw_url)
        scheme = parsed_url.scheme if parsed_url.scheme else 'https'
        netloc = parsed_url.netloc if parsed_url.netloc else parsed_url.path
        wp_url = urlunparse((scheme, netloc, '', '', '', ''))
        
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
        try:
            response = requests.post(api_url, json=data, headers=headers, auth=auth)
            response.raise_for_status()
            return response.json()['id']
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur lors de la publication : {str(e)}")

    title = st.text_input("Titre de l'article")
    content = st.text_area("Contenu de l'article")

    if st.button("Publier"):
        try:
            post_id = publish_post_rest(title, content)
            st.success(f"Article publié avec succès via l'API REST! ID: {post_id}")
        except Exception as e:
            st.error(str(e))

if __name__ == "__main__":
    app()
