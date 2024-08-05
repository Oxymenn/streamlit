import streamlit as st
from scripts import proposition_maillage
from scripts import similarite_cosinus
from scripts import audit_maillage_interne
from scripts import cannibalisation_serp
from scripts import test_cannibalisation
from scripts import images_bulk

# Configuration des pages
PAGES = {
    "Pages Similaires Sémantiquement - Proposition de Maillage Interne": proposition_maillage,
    "Similarité Cosinus": similarite_cosinus,
    "Audit Maillage Interne": audit_maillage_interne,
    "Cannibalisation SERP": cannibalisation_serp,
    "Test Cannibalisation": test_cannibalisation,
    "Images Bulk": images_bulk
}

# Titre principal
st.sidebar.title("Scripts de Pirates")

# Sous-titre et choix des scripts
st.sidebar.subheader("Les scripts")
selection = st.sidebar.radio("", list(PAGES.keys()), index=0)

# Affichage du script sélectionné
page = PAGES[selection]
page.app()

# Copyright
st.sidebar.markdown("© 2024 | by PirateSEO")
