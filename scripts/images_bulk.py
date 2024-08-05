import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import requests
from io import BytesIO

# Fonction pour supprimer l'arrière-plan et ajouter un fond rouge
def remove_background_and_add_red(image):
    # Convertir l'image en tableau numpy
    np_image = np.array(image)
    
    # Convertir en espace de couleur HSV
    hsv = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
    
    # Définir le seuil pour la couleur blanche
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 20, 255])
    mask = cv2.inRange(hsv, lower_white, upper_white)
    
    # Créer une image avec un fond rouge
    red_background = np.full(np_image.shape, [255, 0, 0], dtype=np.uint8)
    
    # Combiner l'image originale avec le fond rouge
    result = np.where(mask[:, :, np.newaxis] == 255, red_background, np_image)
    
    return Image.fromarray(result)

# Titre de l'application
st.title("Traitement d'images avec arrière-plan rouge")

# Télécharger le fichier CSV
uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

if uploaded_file is not None:
    # Lire le fichier CSV
    df = pd.read_csv(uploaded_file)
    
    # Sélectionner la colonne des URLs
    column = st.selectbox("Sélectionnez la colonne des URLs d'images", df.columns)
    
    # Traitement des images
    for index, url in enumerate(df[column]):
        try:
            # Télécharger l'image
            response = requests.get(url)
            image = Image.open(BytesIO(response.content))
            
            # Supprimer l'arrière-plan et ajouter un fond rouge
            processed_image = remove_background_and_add_red(image)
            
            # Afficher l'image traitée
            st.image(processed_image, caption=f"Image {index + 1} traitée", use_column_width=True)
        
        except Exception as e:
            st.write(f"Erreur lors du traitement de l'image {index + 1}: {e}")
