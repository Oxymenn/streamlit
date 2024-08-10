import streamlit as st
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost

# Récupération des secrets
wp_url = st.secrets["wordpress"]["url"]
wp_username = st.secrets["wordpress"]["username"]
wp_password = st.secrets["wordpress"]["password"]

def publish_post(title, content):
    client = Client(wp_url, wp_username, wp_password)
    post = WordPressPost()
    post.title = title
    post.content = content
    post.post_status = 'publish'
    client.call(NewPost(post))

# Interface Streamlit
st.title("Publier un article sur WordPress")

title = st.text_input("Titre de l'article")
content = st.text_area("Contenu de l'article")

if st.button("Publier"):
    try:
        publish_post(title, content)
        st.success("Article publié avec succès!")
    except Exception as e:
        st.error(f"Erreur lors de la publication : {str(e)}")
