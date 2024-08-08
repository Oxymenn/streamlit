import streamlit as st
from scripts import analyse_proposition_maillage, proposition_maillage
from scripts import similarite_cosinus, cannibalisation_serp, test_cannibalisation, images_bulk

st.set_page_config(page_title="Scripts de Pirates", layout="wide")

# CSS personnalisé pour styliser les éléments de menu
st.markdown("""
<style>
    .menu-item {
        color: black;
        cursor: pointer;
        transition: font-weight 0.3s;
        padding: 0.25rem 0;
        font-size: 0.9rem;
    }
    .menu-item:hover {
        text-decoration: underline;
    }
    .menu-subtitle {
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    .menu-container {
        padding-left: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Fonction pour créer un élément de menu
def menu_item(label, on_click):
    st.markdown(f"""
    <div class="menu-item" onclick='{on_click}'>{label}</div>
    """, unsafe_allow_html=True)

# Titre principal
st.sidebar.title("Scripts de Pirates")

# Menu
st.sidebar.markdown('<div class="menu-subtitle">Maillage interne</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="menu-container">', unsafe_allow_html=True)
menu_item("Analyse + Proposition Maillage", "Streamlit.setComponentValue('script', 'analyse_proposition_maillage')")
menu_item("Proposition Maillage", "Streamlit.setComponentValue('script', 'proposition_maillage')")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="menu-subtitle">Autres scripts</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="menu-container">', unsafe_allow_html=True)
menu_item("Similarité Cosinus", "Streamlit.setComponentValue('script', 'similarite_cosinus')")
menu_item("Cannibalisation SERP", "Streamlit.setComponentValue('script', 'cannibalisation_serp')")
menu_item("Test Cannibalisation", "Streamlit.setComponentValue('script', 'test_cannibalisation')")
menu_item("Images Bulk", "Streamlit.setComponentValue('script', 'images_bulk')")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Copyright
st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 | by PirateSEO")

# Zone principale pour afficher le contenu du script sélectionné
script = st.sidebar.empty()
script.text_input("", key="script", label_visibility="collapsed")

main_container = st.container()
with main_container:
    selected_script = st.session_state.get('script', None)
    if selected_script == 'analyse_proposition_maillage':
        analyse_proposition_maillage.app()
    elif selected_script == 'proposition_maillage':
        proposition_maillage.app()
    elif selected_script == 'similarite_cosinus':
        similarite_cosinus.app()
    elif selected_script == 'cannibalisation_serp':
        cannibalisation_serp.app()
    elif selected_script == 'test_cannibalisation':
        test_cannibalisation.app()
    elif selected_script == 'images_bulk':
        images_bulk.app()
    else:
        st.write("Sélectionnez un script dans le menu de gauche pour commencer.")
