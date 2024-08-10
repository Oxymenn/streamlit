import streamlit as st
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost

def app():
    st.title("Publier un article sur WordPress")

    # Récupération des secrets avec gestion d'erreur
    try:
        wp_url = st.secrets["wordpress"]["url"]
        wp_username = st.secrets["wordpress"]["username"]
        wp_password = st.secrets["wordpress"]["password"]
    except KeyError:
        st.error("Erreur : Les secrets WordPress ne sont pas configurés correctement.")
        return

    def publish_post(title, content):
        client = Client(wp_url, wp_username, wp_password)
        post = WordPressPost()
        post.title = title
        post.content = content
        post.post_status = 'publish'
        client.call(NewPost(post))

    title = st.text_input("Titre de l'article")
    content = st.text_area("Contenu de l'article")

    if st.button("Publier"):
        try:
            publish_post(title, content)
            st.success("Article publié avec succès!")
        except Exception as e:
            st.error(f"Erreur lors de la publication : {str(e)}")

# Si vous voulez pouvoir exécuter ce script individuellement aussi
if __name__ == "__main__":
    app()
