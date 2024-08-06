import streamlit as st
import pandas as pd

def swap_first_two_urls(url_string):
    urls = url_string.split(',')
    if len(urls) >= 2:
        urls[0], urls[1] = urls[1], urls[0]
    return ','.join(urls)

st.title('Inverseur d\'URLs d\'images')

uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    st.write("Aperçu du fichier importé:")
    st.dataframe(df.head())
    
    columns = df.columns.tolist()
    selected_column = st.selectbox("Sélectionnez la colonne contenant les URLs des images", columns)
    
    if st.button('Lancer le script'):
        if selected_column in df.columns:
            df['URLs inversées'] = df[selected_column].apply(swap_first_two_urls)
            
            st.write("Résultat:")
            st.dataframe(df)
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Télécharger le fichier CSV modifié",
                data=csv,
                file_name="urls_inversees.csv",
                mime="text/csv",
            )
        else:
            st.error("La colonne sélectionnée n'existe pas dans le fichier CSV.")
