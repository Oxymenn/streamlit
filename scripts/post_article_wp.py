import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse, urlunparse
import concurrent.futures
from openai import OpenAI

# Configuration OpenAI
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Configuration pour plusieurs sites
sites = [
    {"name": "Site 1", "key": "wordpress1"},
    {"name": "Site 2", "key": "wordpress2"},
    # Ajoutez autant de sites que nécessaire
]

def get_site_config(site_key):
    try:
        raw_url = st.secrets[site_key]["url"]
        username = st.secrets[site_key]["username"]
        password = st.secrets[site_key]["password"]
        
        parsed_url = urlparse(raw_url)
        scheme = parsed_url.scheme if parsed_url.scheme else 'https'
        netloc = parsed_url.netloc if parsed_url.netloc else parsed_url.path
        url = urlunparse((scheme, netloc, '', '', '', ''))
        
        return {"url": url, "username": username, "password": password}
    except KeyError:
        st.error(f"Erreur : Les secrets pour {site_key} ne sont pas configurés correctement.")
        return None

def publish_post_rest(site_config, title, content):
    api_url = f"{site_config['url']}/wp-json/wp/v2/posts"
    auth = HTTPBasicAuth(site_config['username'], site_config['password'])
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
        raise Exception(f"Erreur lors de la publication sur {site_config['url']}: {str(e)}")

def generate_article(prompt, keyword):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "Vous êtes un rédacteur web expert en SEO."},
                {"role": "user", "content": f"{prompt} Le mot-clé principal est : {keyword}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Erreur lors de la génération de l'article : {str(e)}")

def main():
    st.title("Générer et publier un article sur plusieurs sites WordPress")

    if 'article_content' not in st.session_state:
        st.session_state.article_content = None

    prompt = st.text_area("Entrez votre prompt pour générer l'article")
    keyword = st.text_input("Entrez le mot-clé principal de l'article")

    if st.button("Générer l'article"):
        if not prompt or not keyword:
            st.error("Veuillez entrer un prompt et un mot-clé.")
        else:
            try:
                with st.spinner("Génération de l'article en cours..."):
                    st.session_state.article_content = generate_article(prompt, keyword)
                st.success("Article généré avec succès!")
                st.write("Aperçu de l'article :")
                st.write(st.session_state.article_content[:500] + "...")  # Affiche les 500 premiers caractères
            except Exception as e:
                st.error(str(e))

    if st.session_state.article_content and st.button("Publier l'article généré sur tous les sites"):
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_site = {executor.submit(publish_post_rest, get_site_config(site["key"]), f"Article sur {keyword}", st.session_state.article_content): site["name"] for site in sites if get_site_config(site["key"])}
            for future in concurrent.futures.as_completed(future_to_site):
                site_name = future_to_site[future]
                try:
                    post_id = future.result()
                    results.append(f"Article publié avec succès sur {site_name}! ID: {post_id}")
                except Exception as exc:
                    results.append(f"Erreur lors de la publication sur {site_name}: {str(exc)}")
        
        for result in results:
            if "succès" in result:
                st.success(result)
            else:
                st.error(result)

if __name__ == "__main__":
    main()
