import streamlit as st
from scripts import embedding_script
from scripts import semantic_audit_script
from scripts import cannibalisation_serp

# Configuration des pages
PAGES = {
    "Maillage interne": {
        "Embedding Script": embedding_script,
        "Audit Sémantique": semantic_audit_script,
    },
    "Analyse SERP": {
        "Cannibalisation SERP": cannibalisation_serp,
    }
}

# Titre principal
st.sidebar.title("Scripts de Pirates")

# Initialisation de la sélection
selected_script = None

# Sous-titre et choix des scripts de maillage interne
st.sidebar.subheader("Maillage interne")
maillage_script = st.sidebar.radio("", list(PAGES["Maillage interne"].keys()), key="maillage", index=0)

# Sous-titre et choix des scripts d'analyse SERP
st.sidebar.subheader("Analyse SERP")
serp_script = st.sidebar.radio("", list(PAGES["Analyse SERP"].keys()), key="serp", index=0)

# Déterminer quel script est sélectionné
if maillage_script:
    selected_script = PAGES["Maillage interne"][maillage_script]
if serp_script:
    selected_script = PAGES["Analyse SERP"][serp_script]

# Exécuter le script sélectionné
if selected_script:
    selected_script.app()

# Copyright
st.sidebar.markdown("© 2024 | by PirateSEO")
