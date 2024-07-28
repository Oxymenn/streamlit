import streamlit as st
from scripts import embedding_script
from scripts import semantic_audit_script
from scripts import cannibalisation_serp

PAGES = {
    "Scripts de Pirates": {
        "Embedding Script": embedding_script,
        "Audit Sémantique": semantic_audit_script
    },
    "Sémantique": {
        "Cannibalisation SERP": cannibalisation_serp
    }
}

st.sidebar.title("Navigation")
selection_category = st.sidebar.radio("Catégories", list(PAGES.keys()))
selection_page = st.sidebar.radio("Scripts", list(PAGES[selection_category].keys()))

page = PAGES[selection_category][selection_page]
page.app()
