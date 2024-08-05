# scripts/images_bulk.py

import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import requests
from io import BytesIO

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

def app():
    # Titre de l'application
    st.title("Traitement d'images avec arrière-plan rouge")

    # Télécharger le fichier CSV
    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

    if uploaded_file is not None:
        # Lire le fichier CSV
        df = pd.read_csv(uploaded_file)
        
        # Permettre à l'utilisateur de sélectionner la colonne d'URLs
        column = st.selectbox("Sélectionnez la colonne des URLs d'images", df.columns)

        # Ajouter un bouton pour exécuter le traitement
        if st.button("Traiter les images"):
            # Vérifier que la colonne sélectionnée est valide
            if column:
                urls = df[column].dropna().tolist()  # Extraire les URLs, en supprimant les valeurs manquantes

                # Traiter chaque URL
                for url_index, url in enumerate(urls):
                    if isinstance(url, str) and url.startswith(('http', 'https')):
                        try:
                            # Télécharger l'image
                            response = requests.get(url)
                            image = Image.open(BytesIO(response.content))
                            
                            # Supprimer l'arrière-plan et ajouter un fond rouge
                            processed_image = remove_background_and_add_red(image)
                            
                            # Afficher l'image traitée
                            st.image(processed_image, caption=f"Image {url_index + 1}", use_column_width=True)
                        
                        except Exception as e:
                            st.error(f"Erreur lors du traitement de l'image URL {url_index + 1}: {e}")
                    else:
                        st.error(f"L'URL à l'index {url_index + 1} n'est pas valide.")
