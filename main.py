import streamlit as st
from scripts import embedding_script
from scripts import semantic_audit_script
from scripts import cannibalisation_serp

PAGES = {
    "Maillage interne": {
        "Embedding Script": embedding_script,
        "Audit Sémantique": semantic_audit_script,
    },
    "Sémantique": {
        "Cannibalisation SERP": cannibalisation_serp,
    }
}

st.sidebar.title("Scripts de Pirates")

# Choix de la catégorie
category = st.sidebar.radio("Catégories", list(PAGES.keys()))

# Choix du script dans la catégorie sélectionnée
selection = st.sidebar.radio("Scripts", list(PAGES[category].keys()))

page = PAGES[category][selection]
page.app()
