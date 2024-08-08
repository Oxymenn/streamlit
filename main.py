import streamlit as st
from scripts import analyse_proposition_maillage, proposition_maillage
from scripts import similarite_cosinus, cannibalisation_serp, test_cannibalisation, images_bulk

# Configuration des pages
PAGES = {
    "Maillage interne": {
        "Proposition Maillage": proposition_maillage,
        "Analyse + Proposition Maillage": analyse_proposition_maillage
    },
    "Autres scripts": {
        "Similarité Cosinus": similarite_cosinus,
        "Cannibalisation SERP": cannibalisation_serp,
        "Test Cannibalisation": test_cannibalisation,
        "Images Bulk": images_bulk
    }
}

st.set_page_config(page_title="Scripts de Pirates", layout="wide")

# Titre principal
st.sidebar.title("Pirates SEO")

# Sélection de la catégorie
category = st.sidebar.selectbox("Catégorie", list(PAGES.keys()))

# Sélection du script dans la catégorie choisie
script_name = st.sidebar.selectbox("Script", list(PAGES[category].keys()))

# Affichage du script sélectionné
script = PAGES[category][script_name]
script.app()

# Copyright
st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 | by PirateSEO")
