import streamlit as st
from scripts import embedding_script
from scripts import semantic_audit_script
from scripts import cannibalisation_serp

PAGES = {
    "Embedding Script": embedding_script,
    "Audit Sémantique": semantic_audit_script,
    "Cannibalisation SERP": cannibalisation_serp
}

st.sidebar.title("Scripts de Pirates")
selection = st.sidebar.radio("Maillage interne", list(PAGES.keys()))

page = PAGES[selection]
page.app()
