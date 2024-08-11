import streamlit as st
from scripts import analyse_proposition_maillage
from scripts import proposition_maillage
from scripts import similarite_cosinus
from scripts import cannibalisation_serp
from scripts import cannibalisation_gratuit
from scripts import images_bulk
from scripts import post_article_wp

# Configuration des pages
PAGES = {
    "Analyse + Proposition Maillage": analyse_proposition_maillage,
    "Proposition Maillage": proposition_maillage,
    "Similarité Cosinus": similarite_cosinus,
        "Analyse Cannibalisation SERP (2€30 pour 1000 mots)": cannibalisation_serp_payant,
    "Analyse Cannibalisation SERP (gratuit)": cannibalisation_serp_gratuit,
    "Images Bulk": images_bulk,
    "Post Article WP": post_article_wp
}

# Titre principal
st.sidebar.title("PirateSEO")

# Sous-titre et choix des scripts
st.sidebar.subheader("Les scripts")
selection = st.sidebar.radio("", list(PAGES.keys()), index=0)

# Affichage du script sélectionné
page = PAGES[selection]
page.app()

# Copyright
st.sidebar.markdown("© 2024 | by PirateSEO")
