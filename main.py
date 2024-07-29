import streamlit as st
from scripts import embedding_script
from scripts import similarite_cosinus
from scripts import audit_maillage_interne
from scripts import semantic_audit_script
from scripts import cannibalisation_serp

# Configuration des pages
PAGES = {
    "Embedding Script": embedding_script,
    "Similarité Cosinus": similarite_cosinus,
    "Audit Maillage Interne": audit_maillage_interne,
    "Audit Sémantique": semantic_audit_script,
    "Cannibalisation SERP": cannibalisation_serp
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
