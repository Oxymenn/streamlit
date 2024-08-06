import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import base64

def process_image(url):
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content))
        
        # Créer un nouveau fond gris clair
        background = Image.new('RGB', img.size, (220, 220, 220))
        
        # Coller l'image originale sur le fond gris
        background.paste(img, (0, 0), img if img.mode == 'RGBA' else None)
        
        # Convertir l'image en base64
        buffered = BytesIO()
        background.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        st.error(f"Erreur lors du traitement de l'image {url}: {str(e)}")
        return url

def app():
    st.title("Traitement d'images en masse")
    
    st.write("Ce script permet d'importer un fichier CSV, de sélectionner une colonne contenant des URLs d'images, "
             "puis de traiter ces images en déplaçant l'URL 2 à la position 1 et en changeant le fond de l'image 1 "
             "(anciennement 2) en gris clair.")

    # Upload du fichier CSV
    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")
    
    if uploaded_file is not None:
        try:
            # Lire le fichier CSV
            df = pd.read_csv(uploaded_file)
            
            # Sélectionner la colonne des images
            image_column = st.selectbox("Sélectionnez la colonne des images", df.columns)
            
            if st.button("Exécuter"):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Traiter chaque cellule de la colonne sélectionnée
                for index, cell in enumerate(df[image_column]):
                    status_text.text(f"Traitement de la ligne {index+1}/{len(df)}")
                    urls = cell.split(',')
                    if len(urls) >= 2:
                        # Déplacer l'URL 2 à la position 1
                        urls[0], urls[1] = urls[1].strip(), urls[0].strip()
                        
                        # Traiter l'image 1 (anciennement 2)
                        processed_img_url = process_image(urls[0])
                        
                        # Mettre à jour l'URL avec l'image traitée
                        urls[0] = processed_img_url
                        
                        # Mettre à jour la cellule avec les nouvelles URLs
                        df.at[index, image_column] = ','.join(urls)

                    progress_bar.progress((index + 1) / len(df))

                status_text.text("Traitement terminé !")

                # Afficher le DataFrame mis à jour
                st.dataframe(df)
                
                # Offrir un téléchargement du fichier CSV mis à jour
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Télécharger le CSV mis à jour",
                    data=csv,
                    file_name="updated_images.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"Une erreur s'est produite lors du traitement : {str(e)}")

if __name__ == "__main__":
    app()
