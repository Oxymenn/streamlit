import streamlit as st
from scripts import analyse_proposition_maillage
from scripts import proposition_maillage
from scripts import tri_keywords
from scripts import cannibalisation_serp_payant
from scripts import cannibalisation_serp_gratuit
from scripts import images_bulk
from scripts import post_article_wp
from scripts import audit_on_page
from scripts import google_serp_scraper
from scripts import testmaillage
from scripts import extraction_serp_dataforseo

# Configuration des pages
PAGES = {
    "Analyse + Proposition Maillage": analyse_proposition_maillage,
    "Proposition Maillage": proposition_maillage,
    "Extraction SERP - DataForSEO": extraction_serp_dataforseo,
    "Tri + Nettoyage de mots-clés": tri_keywords,
    "Analyse Cannibalisation SERP (2€30 pour 1000 mots)": cannibalisation_serp_payant,
    "Analyse Cannibalisation SERP (gratuit)": cannibalisation_serp_gratuit,
    "Images Bulk": images_bulk,
    "Post Article WP": post_article_wp,
    "Audit SEO On-page": audit_on_page,
    "Google SERP Scraper": google_serp_scraper,
    "Maillage TEST": testmaillage
}

# Titre principal
st.sidebar.title("PirateSEO")

# Sous-titre et choix des scripts
st.sidebar.subheader("Les scripts")
selection = st.sidebar.radio("", list(PAGES.keys()), index=0)

# Affichage du script sélectionné avec vérification de la fonction 'app'
page = PAGES[selection]
if hasattr(page, 'app'):
    page.app()
else:
    st.error(f"Le module sélectionné ({selection}) ne contient pas de fonction 'app'.")
