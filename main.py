import streamlit as st
from scripts import embedding_script
from scripts import semantic_audit_script

PAGES = {
    "Embedding Script": embedding_script,
    "Audit Sémantique": semantic_audit_script
}

st.sidebar.title("Scripts de Pirates")
selection = st.sidebar.radio("Maillage interne", list(PAGES.keys()))

page = PAGES[selection]
page.app()
