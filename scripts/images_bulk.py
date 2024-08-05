# scripts/images_bulk.py

import streamlit as st
from rembg import remove
from PIL import Image, ImageOps
from io import BytesIO
import requests

def remove_background_with_rembg(image):
    # Supprimer l'arrière-plan de l'image
    output = remove(image)

    # Charger l'image résultante avec Pillow
    result_image = Image.open(BytesIO(output)).convert("RGBA")

    # Créer un fond gris clair
    background = Image.new('RGBA', result_image.size, (211, 211, 211, 255))

    # Combiner l'image avec le fond
    final_image = Image.alpha_composite(background, result_image)

    # Convertir en RGB pour supprimer le canal alpha
    final_image = final_image.convert("RGB")

    return final_image

def app():
    st.title("Suppression d'Arrière-Plan avec RemBG")

    uploaded_file = st.file_uploader("Téléchargez une image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image Originale", use_column_width=True)

        if st.button("Traiter l'image"):
            processed_image = remove_background_with_rembg(image)
            st.image(processed_image, caption="Image avec Arrière-Plan Gris Clair", use_column_width=True)

if __name__ == "__main__":
    app()
