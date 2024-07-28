import streamlit as st
from audit_maillage_interne import run_audit_maillage_interne
from embed_and_analyze import analyze_similarity

st.set_page_config(page_title="SEO Tools", layout="wide")

st.sidebar.title("Navigation")

# Utilisation de boutons au lieu d'une liste déroulante
if st.sidebar.button("Audit de maillage interne"):
    run_audit_maillage_interne()
elif st.sidebar.button("Audit Sémantique"):
    analyze_similarity()

# Ajout du copyright en bas de la sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 - by PirateSEO")

# Page d'accueil par défaut
if 'page' not in st.session_state:
    st.title("Bienvenue dans SEO Tools")
    st.write("Choisissez une application dans la barre latérale pour commencer.")
