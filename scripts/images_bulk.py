# scripts/images_bulk.py

import streamlit as st
import torch
from torchvision import transforms
from PIL import Image
from io import BytesIO
import requests
from modnet.src.models.modnet import MODNet  # Assurez-vous que le chemin est correct

# Charger le modèle MODNet
@st.cache_resource
def load_modnet():
    # Charger le modèle pré-entraîné
    modnet = MODNet(backbone_pretrained=False)
    modnet = torch.nn.DataParallel(modnet)
    modnet.load_state_dict(torch.load('modnet_photographic_portrait_matting.ckpt', map_location=torch.device('cpu')))
    modnet.eval()
    return modnet

modnet = load_modnet()

# Transformation de l'image
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((512, 512))
])

def remove_background_with_modnet(image):
    image = transform(image).unsqueeze(0)

    # Passer l'image dans le modèle
    with torch.no_grad():
        matte = modnet(image, True)[0]
        matte = matte[0][0].cpu().numpy()

    # Appliquer le masque pour remplacer l'arrière-plan
    matte = Image.fromarray((matte * 255).astype('uint8')).resize(image.size[1:], Image.BILINEAR)

    # Fusionner avec un fond gris clair
    background = Image.new('RGB', image.size[1:], (211, 211, 211))
    output = Image.composite(image, background, matte)
    return output

def app():
    st.title("Suppression d'Arrière-Plan avec MODNet")

    uploaded_file = st.file_uploader("Téléchargez une image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image Originale", use_column_width=True)

        if st.button("Traiter l'image"):
            processed_image = remove_background_with_modnet(image)
            st.image(processed_image, caption="Image avec Arrière-Plan Gris Clair", use_column_width=True)

if __name__ == "__main__":
    app()
