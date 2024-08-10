import streamlit as st
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
import requests
from requests.auth import HTTPBasicAuth

def app():
    st.title("Publier un article sur WordPress")

    try:
        wp_url = st.secrets["wordpress"]["url"].rstrip('/xmlrpc.php')
        wp_username = st.secrets["wordpress"]["username"]
        wp_password = st.secrets["wordpress"]["password"]
    except KeyError:
        st.error("Erreur : Les secrets WordPress ne sont pas configurés correctement.")
        return

    def publish_post_xmlrpc(title, content):
        client = Client(f"{wp_url}/xmlrpc.php", wp_username, wp_password)
        post = WordPressPost()
        post.title = title
        post.content = content
        post.post_status = 'publish'
        post_id = client.call(NewPost(post))
        return post_id

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
            post_id = publish_post_xmlrpc(title, content)
            st.success(f"Article publié avec succès via XML-RPC! ID: {post_id}")
        except Exception as e:
            st.warning(f"Erreur avec XML-RPC: {str(e)}. Tentative avec l'API REST...")
            try:
                post_id = publish_post_rest(title, content)
                st.success(f"Article publié avec succès via l'API REST! ID: {post_id}")
            except Exception as e:
                st.error(f"Erreur lors de la publication : {str(e)}")

if __name__ == "__main__":
    app()
