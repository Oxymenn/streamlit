import streamlit as st
import pandas as pd
import io

def limit_images(image_urls, max_images=5):
    urls = image_urls.split(', ')
    if len(urls) > max_images:
        return ', '.join(urls[:max_images])
    return image_urls

def process_csv(df, image_column):
    df['processed_images'] = df[image_column].apply(limit_images)
    return df

def app():
    st.title('Limitation d\'images pour CSV de produits')

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Aperçu des données originales :")
        st.write(df.head())

        columns = df.columns.tolist()
        image_column = st.selectbox("Sélectionnez la colonne contenant les URLs des images", columns)

        if st.button('Traiter le CSV'):
            processed_df = process_csv(df, image_column)
            st.write("Aperçu des données traitées :")
            st.write(processed_df.head())

            # Création d'un buffer en mémoire pour stocker le CSV
            csv_buffer = io.BytesIO()
            processed_df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            # Bouton de téléchargement
            st.download_button(
                label="Télécharger le CSV traité",
                data=csv_buffer,
                file_name="produits_images_limitees.csv",
                mime="text/csv"
            )

    st.write("Note : Ce script limitera le nombre d'images à 5 pour chaque produit ayant plus de 5 images.")

if __name__ == "__main__":
    app()
