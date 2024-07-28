import streamlit as st
from calcul_similarite_urls import calcul_similarite_urls
from audit_maillage_interne import audit_maillage_interne

def main():
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Choisissez une application",
                                ["Audit de maillage interne", 
                                 "Calcul de similarité des URLs"])

    if app_mode == "Audit de maillage interne":
        audit_maillage_interne()
    elif app_mode == "Calcul de similarité des URLs":
        calcul_similarite_urls()

    st.write("---")
    st.write("© 2024 | By PirateSEO")

if __name__ == "__main__":
    main()
