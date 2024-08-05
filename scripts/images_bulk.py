# scripts/images_bulk.py

import streamlit as st
import pandas as pd
from wand.image import Image as WandImage
import requests
from io import BytesIO

def remove_background_and_add_gray(image_url):
    # Télécharger l'image
    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image: {response.status_code}")

    # Ouvrir l'image avec Wand
    with WandImage(file=BytesIO(response.content)) as img:
        img.format = 'png'  # Assurez-vous que l'image est au format PNG pour la transparence
        img.alpha_channel = 'remove'
        
        # Assurez-vous que l'image a un canal alpha pour la transparence
        img.alpha_channel = 'set'

        # Supprimer l'arrière-plan (nous supposons un fond blanc à supprimer)
        img.transparent_color('white', alpha=0.0, fuzz=0.10 * img.quantum_range)

        # Créer un nouveau fond gris clair
        with WandImage(width=img.width, height=img.height, background=(211, 211, 211)) as bg:
            bg.composite(img, 0, 0)

            # Convertir en bytes pour Streamlit
            img_bytes = bg.make_blob('png')
    
    return img_bytes

def app():
    # Titre de l'application
    st.title("Traitement d'images avec arrière-plan gris clair")

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

                    # Vérifier qu'il y a au moins deux URLs
                    if len(urls) > 1:
                        # Mettre la deuxième URL en première position
                        urls[0], urls[1] = urls[1], urls[0]
                        new_url = urls[0]  # Nouvelle première URL

                        try:
                            # Traiter l'image avec ImageMagick
                            processed_image_bytes = remove_background_and_add_gray(new_url)
                            
                            # Afficher l'image traitée
                            st.image(processed_image_bytes, caption=f"Ligne {cell_index + 1}, Image modifiée", use_column_width=True)
                        
                        except Exception as e:
                            st.error(f"Erreur lors du traitement de l'image dans la ligne {cell_index + 1}: {e}")
                    else:
                        st.error(f"La ligne {cell_index + 1} ne contient pas assez d'URLs pour effectuer la modification.")
