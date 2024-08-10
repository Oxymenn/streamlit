import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

def app():
    st.title("Publier un article sur WordPress")

    try:
        wp_url = st.secrets["wordpress"]["url"]
        wp_username = st.secrets["wordpress"]["username"]
        wp_password = st.secrets["wordpress"]["password"]
    except KeyError:
        st.error("Erreur : Les secrets WordPress ne sont pas configurés correctement.")
        return

    def publish_post(title, content):
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
            return True
        else:
            raise Exception(f"Erreur HTTP {response.status_code}: {response.text}")

    title = st.text_input("Titre de l'article")
    content = st.text_area("Contenu de l'article")

    if st.button("Publier"):
        try:
            if publish_post(title, content):
                st.success("Article publié avec succès!")
        except Exception as e:
            st.error(f"Erreur lors de la publication : {str(e)}")

if __name__ == "__main__":
    app()
