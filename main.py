import streamlit as st
from scripts import analyse_proposition_maillage, proposition_maillage
from scripts import similarite_cosinus, cannibalisation_serp, test_cannibalisation, images_bulk

st.set_page_config(page_title="Scripts de Pirates", layout="wide")

# Titre principal
st.sidebar.title("Pirates SEO")

# Fonction pour créer un sous-titre
def sidebar_header(title):
    st.sidebar.markdown(f"**{title}**")

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
