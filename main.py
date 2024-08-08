import streamlit as st
from scripts import analyse_proposition_maillage, proposition_maillage
from scripts import similarite_cosinus, cannibalisation_serp, test_cannibalisation, images_bulk

st.set_page_config(page_title="Scripts de Pirates", layout="wide")

# Titre principal
st.sidebar.title("Pirates SEO")

# Fonction pour créer un sous-titre
def sidebar_header(title):
    st.sidebar.markdown(f"**{title}**")

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

# Sélection du script
selected_script = None

for category, category_scripts in scripts.items():
    sidebar_header(category)
    selected_script_name = st.sidebar.radio("", list(category_scripts.keys()), key=category)
    if st.sidebar.button("Exécuter", key=f"execute_{category}"):
        selected_script = category_scripts[selected_script_name]

# Copyright
st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 | by PirateSEO")

# Zone principale pour afficher le contenu du script sélectionné
main_container = st.container()
with main_container:
    if selected_script:
        selected_script.app()
    else:
        st.write("Sélectionnez un script dans le menu de gauche et cliquez sur 'Exécuter' pour commencer.")
