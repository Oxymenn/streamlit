import streamlit as st
from audit_maillage_interne import run_audit_maillage_interne
from embed_and_analyze import analyze_similarity

st.set_page_config(page_title="SEO Tools by PirateSEO", layout="wide")

st.sidebar.title("Navigation")

# Création de la sidebar avec les options
app_mode = st.sidebar.radio(
    "Choisissez une application",
    ["Audit de maillage interne", "Embedding URL"]
)

# Affichage du contenu en fonction de la sélection
if app_mode == "Audit de maillage interne":
    run_audit_maillage_interne()
elif app_mode == "Embedding URL":
    analyze_similarity()

# Ajout du copyright en bas de la sidebar
st.sidebar.markdown("---")
st.sidebar.text("© 2024 - PirateSEO")

# Page d'accueil si aucune option n'est sélectionnée
if app_mode not in ["Audit de maillage interne", "Embedding URL"]:
    st.title("Bienvenue dans SEO Tools")
    st.write("Choisissez une application dans la barre latérale pour commencer.")
