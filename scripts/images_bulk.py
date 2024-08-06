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
        return None

def app():
    st.title("Traitement d'images en masse")
    
    st.write("Ce script permet d'importer un fichier CSV, de sélectionner une colonne contenant des URLs d'images, "
             "puis d'ajouter un arrière-plan gris clair à chaque image.")

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

                # Créer des colonnes pour l'affichage
                col1, col2 = st.columns(2)

                # Traiter chaque cellule de la colonne sélectionnée
                for index, cell in enumerate(df[image_column]):
                    status_text.text(f"Traitement de l'image {index+1}/{len(df)}")
                    
                    urls = cell.split(',')
                    for i, url in enumerate(urls):
                        url = url.strip()
                        
                        # Afficher l'image originale
                        col1.image(url, caption=f"Original - Image {index+1}, URL {i+1}", use_column_width=True)
                        
                        # Traiter l'image
                        processed_img = process_image(url)
                        
                        if processed_img:
                            # Afficher l'image traitée
                            col2.image(processed_img, caption=f"Traitée - Image {index+1}, URL {i+1}", use_column_width=True)
                        else:
                            col2.error(f"Erreur de traitement pour l'image {index+1}, URL {i+1}")

                    progress_bar.progress((index + 1) / len(df))

                status_text.text("Traitement terminé !")

        except Exception as e:
            st.error(f"Une erreur s'est produite lors du traitement : {str(e)}")

if __name__ == "__main__":
    app()
