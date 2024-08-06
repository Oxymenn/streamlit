import streamlit as st
import pandas as pd
import requests
import numpy as np
from PIL import Image
from io import BytesIO
import base64
from sklearn.cluster import KMeans
import cv2

def remove_background(image):
    # Convertir l'image en array numpy
    np_image = np.array(image)
    
    # Convertir en LAB color space
    lab = cv2.cvtColor(np_image, cv2.COLOR_RGB2LAB)
    
    # Appliquer un flou gaussien pour réduire le bruit
    lab_blur = cv2.GaussianBlur(lab, (5, 5), 0)
    
    # Appliquer K-means clustering
    pixels = lab_blur.reshape((-1, 3))
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    # Créer un masque basé sur les clusters
    mask = kmeans.labels_.reshape(np_image.shape[:2])
    
    # Déterminer quel cluster représente l'arrière-plan
    background_label = 1 if np.mean(np_image[mask == 1]) > np.mean(np_image[mask == 0]) else 0
    
    # Créer le masque final
    mask = np.uint8(mask != background_label) * 255
    
    # Appliquer des opérations morphologiques pour améliorer le masque
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Appliquer un flou gaussien au masque pour adoucir les bords
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    
    # Créer une image RGBA
    rgba = cv2.cvtColor(np_image, cv2.COLOR_RGB2RGBA)
    rgba[:, :, 3] = mask
    
    return Image.fromarray(rgba)

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
             "puis de supprimer l'arrière-plan de la deuxième image de chaque cellule, d'ajouter un arrière-plan gris clair "
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
