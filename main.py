import streamlit as st
from scripts import analyse_proposition_maillage, proposition_maillage
from scripts import similarite_cosinus, cannibalisation_serp, test_cannibalisation, images_bulk

st.set_page_config(page_title="Scripts de Pirates", layout="wide")

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

# Initialiser l'état pour le script sélectionné
if 'selected_script' not in st.session_state:
    st.session_state.selected_script = None

# Fonction pour mettre à jour le script sélectionné
def update_selected_script(script_name, script_func):
    st.session_state.selected_script = (script_name, script_func)

# Affichage et sélection des scripts
for category, category_scripts in scripts.items():
    sidebar_header(category)
    for script_name, script_func in category_scripts.items():
        is_selected = st.session_state.selected_script and st.session_state.selected_script[0] == script_name
        if st.sidebar.radio(script_name, [True, False], key=script_name, index=0 if is_selected else 1, label_visibility="collapsed"):
            update_selected_script(script_name, script_func)

# Copyright
st.sidebar.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
st.sidebar.markdown("© 2024 | by PirateSEO")

# Zone principale pour afficher le contenu du script sélectionné
main_container = st.container()
with main_container:
    if st.session_state.selected_script:
        st.session_state.selected_script[1].app()
    else:
        st.write("Sélectionnez un script dans le menu de gauche pour commencer.")
