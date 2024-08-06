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
    
    # Appliquer un flou gaussien léger pour réduire le bruit
    lab_blur = cv2.GaussianBlur(lab, (3, 3), 0)
    
    # Normaliser les valeurs LAB
    lab_norm = lab_blur.astype(float) / 255.0
    
    # Augmenter le poids des canaux a et b pour une meilleure distinction des couleurs
    lab_norm[:,:,1:] *= 2.0
    
    # Appliquer K-means clustering avec plus de clusters
    pixels = lab_norm.reshape((-1, 3))
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    # Créer un masque basé sur les clusters
    mask = kmeans.labels_.reshape(np_image.shape[:2])
    
    # Déterminer quel cluster représente l'arrière-plan (le plus grand cluster)
    unique, counts = np.unique(mask, return_counts=True)
    background_label = unique[np.argmax(counts)]
    
    # Créer le masque final
    mask = np.uint8(mask != background_label) * 255
    
    # Appliquer des opérations morphologiques pour améliorer le masque
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Appliquer un flou gaussien au masque pour adoucir les bords
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    
    # Augmenter le contraste du masque
    mask = cv2.normalize(mask, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    _, mask = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    
    # Appliquer un nouveau flou gaussien pour lisser les bords
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    
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

# Le reste du code (fonction app() et main) reste inchangé
