import streamlit as st
from scripts import embedding_script
from scripts import semantic_audit_script
from scripts import cannibalisation_serp

# Configuration des pages
PAGES_MAILLAGE = {
    "Embedding Script": embedding_script,
    "Audit Sémantique": semantic_audit_script,
}

PAGES_SERP = {
    "Cannibalisation SERP": cannibalisation_serp,
}

# Titre principal
st.sidebar.title("Scripts de Pirates")

# Sous-titre et choix des scripts de maillage interne
st.sidebar.subheader("Maillage interne")
selection_maillage = st.sidebar.radio("Choisissez un script", list(PAGES_MAILLAGE.keys()))

# Sous-titre et choix des scripts d'analyse SERP
st.sidebar.subheader("Analyse SERP")
selection_serp = st.sidebar.radio("Choisissez un script", list(PAGES_SERP.keys()), key="serp")

# Affichage du script sélectionné
if selection_maillage:
    page = PAGES_MAILLAGE[selection_maillage]
    page.app()
elif selection_serp:
    page = PAGES_SERP[selection_serp]
    page.app()

# Copyright
st.sidebar.markdown("© 2024 | by PirateSEO")
