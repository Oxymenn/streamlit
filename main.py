from scripts import analyse_proposition_maillage, proposition_maillage
from scripts import similarite_cosinus, cannibalisation_serp, test_cannibalisation, images_bulk

st.set_page_config(page_title="Ratpi SEO", layout="wide")
st.set_page_config(page_title="Scripts de Pirate", layout="wide")

# CSS personnalisé pour styliser les boutons
st.markdown("""
@@ -36,14 +36,14 @@
""", unsafe_allow_html=True)

# Titre principal
st.sidebar.title("Scripts de Pirates")
st.sidebar.title("Pirate SEO")

# Maillage interne
st.sidebar.subtitle("Maillage interne")
if st.sidebar.button("Analyse + Proposition Maillage"):
    analyse_proposition_maillage.app()
if st.sidebar.button("Proposition Maillage"):
    proposition_maillage.app()
if st.sidebar.button("Analyse + Proposition Maillage"):
    analyse_proposition_maillage.app()

# Autres scripts
st.sidebar.header("Autres scripts")
@@ -62,5 +62,3 @@

# Zone principale pour afficher le contenu du script sélectionné
main_container = st.container()
with main_container:
    st.write("Sélectionnez un script dans le menu de gauche pour commencer.")
