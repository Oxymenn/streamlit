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
                all_urls = df[column].dropna().tolist()  # Extraire les lignes de la colonne, en supprimant les valeurs manquantes

                # Traiter chaque cellule (ligne) de la colonne
                for cell_index, cell in enumerate(all_urls):
                    # Diviser la cellule en URLs individuelles
                    urls = [url.strip() for url in cell.split(',') if url.strip().startswith(('http', 'https'))]

                    # Traiter seulement la deuxième URL
                    if len(urls) > 1:
                        url = urls[1]  # Sélectionner la deuxième URL
                        try:
                            # Télécharger l'image
                            response = requests.get(url)
                            
                            # Vérifier que la requête a réussi
                            if response.status_code == 200:
                                # Vérifier le type de contenu
                                content_type = response.headers['Content-Type']
                                if 'image' in content_type:
                                    image = Image.open(BytesIO(response.content))
                                    
                                    # Supprimer l'arrière-plan et ajouter un fond rouge
                                    processed_image = remove_background_and_add_red(image)
                                    
                                    # Afficher l'image traitée
                                    st.image(processed_image, caption=f"Ligne {cell_index + 1}, Deuxième Image", use_column_width=True)
                                else:
                                    st.error(f"Le contenu de l'URL dans la ligne {cell_index + 1} n'est pas une image (type: {content_type}).")
                            else:
                                st.error(f"Erreur HTTP pour l'URL dans la ligne {cell_index + 1}: {response.status_code}")
                        
                        except Exception as e:
                            st.error(f"Erreur lors du traitement de l'image dans la ligne {cell_index + 1}: {e}")
                    else:
                        st.error(f"La ligne {cell_index + 1} ne contient pas assez d'URLs pour traiter la deuxième image.")
