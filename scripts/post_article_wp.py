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

def generate_article(prompt, keyword, site_name):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "Vous êtes un rédacteur web expert en SEO."},
                {"role": "user", "content": f"Écrivez un article unique pour le site {site_name}. {prompt} Le mot-clé principal est : {keyword}."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Erreur lors de la génération de l'article : {str(e)}")

def app():
    st.title("Générer et publier des articles sur différents mots-clés")

    prompt = st.text_area("Entrez votre prompt général pour générer les articles")
    keywords = st.text_area("Entrez les mots-clés (un par ligne)")

    if st.button("Générer et publier les articles"):
        if not prompt or not keywords:
            st.error("Veuillez entrer un prompt et au moins un mot-clé.")
        else:
            keyword_list = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
            results = []

            for i, (keyword, site) in enumerate(zip(keyword_list, sites)):
                site_config = get_site_config(site["key"])
                if site_config:
                    try:
                        with st.spinner(f"Génération et publication de l'article pour le mot-clé '{keyword}' sur {site['name']}..."):
                            article_content = generate_article(prompt, keyword, site['name'])
                            title = f"Article sur {keyword}"  # Titre basé sur le mot-clé
                            post_id = publish_post_rest(site_config, title, article_content)
                            results.append(f"Article sur '{keyword}' publié avec succès sur {site['name']}! ID: {post_id}")
                            st.success(f"Article sur '{keyword}' pour {site['name']} généré et publié avec succès!")
                            st.write(f"Titre : {title}")
                            st.write("Aperçu de l'article :")
                            st.write(article_content[:500] + "...")  # Affiche les 500 premiers caractères
                    except Exception as e:
                        results.append(f"Erreur pour le mot-clé '{keyword}' sur {site['name']}: {str(e)}")
                        st.error(f"Erreur lors de la génération ou de la publication pour '{keyword}' sur {site['name']}: {str(e)}")
                
                if i + 1 >= len(sites):
                    break  # Arrêter si nous avons utilisé tous les sites disponibles

            st.subheader("Résumé des publications")
            for result in results:
                if "succès" in result:
                    st.success(result)
                else:
                    st.error(result)

            if len(keyword_list) > len(sites):
                st.warning(f"Attention : {len(keyword_list) - len(sites)} mot(s)-clé(s) n'ont pas été utilisés car il n'y a pas assez de sites configurés.")

    # Ajoutez ici toute autre fonctionnalité existante de post_article_wp.py si nécessaire

if __name__ == "__main__":
    app()
