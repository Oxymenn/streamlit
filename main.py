import streamlit as st
from scripts import analyse_proposition_maillage
from scripts import proposition_maillage
from scripts import similarite_cosinus
from scripts import cannibalisation_serp
from scripts import test_cannibalisation
from scripts import images_bulk

# Configuration des pages
PAGES = {
    "Analyse + Proposition Maillage": analyse_proposition_maillage,
    "Proposition Maillage": proposition_maillage,
    "Similarité Cosinus": similarite_cosinus,
    "Cannibalisation SERP": cannibalisation_serp,
    "Test Cannibalisation": test_cannibalisation,
    "Images Bulk": images_bulk
}

# Titre principal
st.sidebar.title("PirateSEO")

# Affichage du script sélectionné
page = PAGES[selection]
page.app()

# Copyright
st.sidebar.markdown("© 2024 | by PirateSEO")
