import streamlit as st
import pandas as pd
import requests
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import base64

def remove_background(image):
    # Convertir l'image en RGB si elle est en RGBA
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    # Convertir l'image PIL en array numpy
    np_image = np.array(image)
    
    # Convertir l'image en grayscale
    gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
    
    # Appliquer un seuillage pour créer un masque
    _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    
    # Appliquer une dilatation pour améliorer le masque
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Créer une image avec canal alpha
    result = cv2.cvtColor(np_image, cv2.COLOR_RGB2RGBA)
    result[:, :, 3] = mask
    
    return Image.fromarray(result)

def process_image(url):
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content))
        
        # Supprimer l'arrière-plan
        img_no_bg = remove_background(img)
        
        # Créer un nouveau fond gris clair
        background = Image.new('RGBA', img_no_bg.size, (220, 220, 220, 255))
        
        # Coller l'image sans fond sur le fond gris
        background.paste(img_no_bg, (0, 0), img_no_bg)
        
        # Convertir l'image en base64
        buffered = BytesIO()
        background.save(buffered, format="PNG", quality=100)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        st.error(f"Erreur lors du traitement de l'image {url}: {str(e)}")
        return None

def app():
    st.title("Traitement d'images en masse")
    
    st.write("Ce script permet d'importer un fichier CSV, de sélectionner une colonne contenant des URLs d'images, "
             "puis de tenter de supprimer l'arrière-plan de la deuxième image de chaque cellule, d'ajouter un arrière-plan gris clair "
             "et de l'échanger avec la première.")

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
                    status_text.text(f"Traitement de la cellule {index+1}/{len(df)}")
                    
                    urls = cell.split(',')
                    if len(urls) >= 2:
                        url1 = urls[0].strip()
                        url2 = urls[1].strip()
                        
                        # Afficher l'image originale url2
                        col1.image(url2, caption=f"Original URL2 - Cellule {index+1}", use_column_width=True)
                        
                        # Traiter l'image url2
                        processed_img = process_image(url2)
                        
                        if processed_img:
                            # Afficher l'image traitée
                            col2.image(processed_img, caption=f"URL2 Traitée - Cellule {index+1}", use_column_width=True)
                            
                            # Échanger url1 et url2 traitée
                            urls[0] = processed_img
                            urls[1] = url1
                            
                            # Mettre à jour la cellule avec les nouvelles URLs
                            df.at[index, image_column] = ','.join(urls)
                        else:
                            col2.error(f"Erreur de traitement pour la cellule {index+1}, URL2")

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
