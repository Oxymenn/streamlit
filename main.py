import streamlit as st
from scripts import analyse_proposition_maillage, proposition_maillage
from scripts import similarite_cosinus, cannibalisation_serp, test_cannibalisation, images_bulk

st.set_page_config(page_title="Scripts de Pirates", layout="wide")

# Titre principal
st.sidebar.title("Pirates SEO")

# Fonction pour créer un sous-titre avec espacement minimal
def sidebar_header(title):
    st.sidebar.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)

# Dictionnaire des scripts
scripts = {
    "Maillage interne": {
        "Proposition Maillage": proposition_maillage,
        "Analyse + Proposition Maillage": analyse_proposition_maillage
    },
    "Autres scripts": {
        "Similarité Cosinus": similarite_cosinus,
        "Cannibalisation SERP": cannibalisation_serp,
        "Test Cannibalisation": test_cannibalisation,
        "Images Bulk": images_bulk
    }
}

# Sélection et exécution du script
selected_script = None

for category, category_scripts in scripts.items():
    sidebar_header(category)
    script_name = st.sidebar.radio("", list(category_scripts.keys()), key=category, label_visibility="collapsed")
    if script_name:
        selected_script = category_scripts[script_name]

# Copyright
st.sidebar.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
st.sidebar.markdown("© 2024 | by PirateSEO")

# Zone principale pour afficher le contenu du script sélectionné
main_container = st.container()
with main_container:
    if selected_script:
        selected_script.app()
    else:
        st.write("Sélectionnez un script dans le menu de gauche pour commencer.")



# CSS personnalisé pour un espacement minimal
st.markdown("""
<style>
    .sidebar .sidebar-content {
        padding-top: 0rem;
    }
    .sidebar .stRadio > div[role="radiogroup"] {
        margin-top: 0;
        margin-bottom: 0;
    }
    .sidebar .stRadio > label {
        margin: 0;
        line-height: 1;
    }
    .sidebar .stRadio > div > label {
        padding: 0.1rem 0;
    }
    h4 {
        margin-top: 0.5rem;
        margin-bottom: 0.1rem;
    }
</style>
""", unsafe_allow_html=True)
