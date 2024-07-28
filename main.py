import streamlit as st
from scripts import embedding_script

PAGES = {
    "Embedding Script": embedding_script
}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

page = PAGES[selection]
page.app()
