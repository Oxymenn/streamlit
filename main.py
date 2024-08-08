import streamlit as st
from scripts import analyse_proposition_maillage
from scripts import proposition_maillage
from scripts import similarite_cosinus
from scripts import cannibalisation_serp
from scripts import test_cannibalisation
from scripts import images_bulk

# Configuration des pages
PAGES = {
    "Maillage interne": {
        "Analyse + Proposition Maillage": analyse_proposition_maillage,
        "Proposition Maillage": proposition_maillage
    },
    "Autres scripts": {
        "Similarité Cosinus": similarite_cosinus,
        "Cannibalisation SERP": cannibalisation_serp,
        "Test Cannibalisation": test_cannibalisation,
        "Images Bulk": images_bulk
    }
}

# Titre principal
st.sidebar.title("Scripts de Pirates")

# Sélection de la catégorie
category = st.sidebar.radio("Catégories", list(PAGES.keys()))

# Sélection du script dans la catégorie choisie
if category == "Maillage interne":
    st.sidebar.subheader("Maillage interne")
    script = st.sidebar.radio("", list(PAGES[category].keys()))
else:
    st.sidebar.subheader("Autres scripts")
    script = st.sidebar.radio("", list(PAGES[category].keys()))

# Affichage du script sélectionné
page = PAGES[category][script]
page.app()

# Copyright
st.sidebar.markdown("© 2024 | by PirateSEO")
