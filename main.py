import streamlit as st
from scripts import analyse_proposition_maillage, proposition_maillage
from scripts import similarite_cosinus, cannibalisation_serp, test_cannibalisation, images_bulk

st.set_page_config(page_title="Scripts de Pirates", layout="wide")

# CSS personnalisé pour styliser les boutons
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        text-align: left;
        background-color: transparent;
        color: black;
        font-weight: normal;
        border: none;
        padding: 0.25rem 0;
        margin: 0;
        border-radius: 0;
    }
    .stButton > button:hover {
        text-decoration: underline;
    }
    .stButton > button:active, .stButton > button:focus {
        font-weight: bold;
    }
    .sidebar .stButton > button {
        font-size: 0.9rem;
    }
    .sidebar .stButton {
        margin-bottom: 0.25rem;
    }
    .sidebar .header {
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Titre principal
st.sidebar.title("Pirates SEO")

# Fonction pour créer un sous-titre
def sidebar_header(title):
    st.sidebar.markdown(f'<div class="header">{title}</div>', unsafe_allow_html=True)

# Maillage interne
sidebar_header("Maillage interne")
if st.sidebar.button("Proposition Maillage"):
    proposition_maillage.app()
if st.sidebar.button("Analyse + Proposition Maillage"):
    analyse_proposition_maillage.app()

# Autres scripts
sidebar_header("Autres scripts")
if st.sidebar.button("Similarité Cosinus"):
    similarite_cosinus.app()
if st.sidebar.button("Cannibalisation SERP"):
    cannibalisation_serp.app()
if st.sidebar.button("Test Cannibalisation"):
    test_cannibalisation.app()
if st.sidebar.button("Images Bulk"):
    images_bulk.app()

# Copyright
st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 | by PirateSEO")

# Zone principale pour afficher le contenu du script sélectionné
main_container = st.container()
with main_container:
    st.write("Sélectionnez un script dans le menu de gauche pour commencer.")
