import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import re
import os
from sklearn.preprocessing import FunctionTransformer
import requests

# Liste des stopwords français
stopwords_fr = [
    'alors', 'site', 'boutique', 'commerce', 'ligne', 'produit', 'visiter', 'visitez', 'découvrez', 'découvrir', 'explorer', 'explorez', 'exploiter', 'exploitez', 'au', 'aucuns', 'aussi', 'autre', 'avant', 'avec', 'avoir', 'bon', 
    'car', 'ce', 'cela', 'ces', 'ceux', 'chaque', 'ci', 'comme', 'comment', 
    'dans', 'des', 'du', 'dedans', 'dehors', 'depuis', 'devrait', 'doit', 
    'donc', 'dos', 'droite', 'début', 'elle', 'elles', 'en', 'encore', 'essai', 
    'est', 'et', 'eu', 'fait', 'faites', 'fois', 'font', 'force', 'haut', 
    'hors', 'ici', 'il', 'ils', 'je', 'juste', 'la', 'le', 'les', 'leur', 'là', 
    'ma', 'maintenant', 'mais', 'mes', 'mine', 'moins', 'mon', 'mot', 'même', 
    'ni', 'nommés', 'notre', 'nous', 'nouveaux', 'ou', 'où', 'par', 'parce', 
    'parole', 'pas', 'personnes', 'peut', 'peu', 'pièce', 'plupart', 'pour', 
    'pourquoi', 'quand', 'que', 'quel', 'quelle', 'quelles', 'quels', 'qui', 
    'sa', 'sans', 'ses', 'seulement', 'si', 'sien', 'son', 'sont', 'sous', 
    'soyez', 'sujet', 'sur', 'ta', 'tandis', 'tellement', 'tels', 'tes', 
    'ton', 'tous', 'tout', 'trop', 'très', 'tu', 'valeur', 'voie', 'voient', 
    'vont', 'votre', 'vous', 'vu', 'ça', 'étaient', 'état', 'étions', 'été', 
    'être', 'à', 'moi', 'toi', 'si', 'oui', 'non', 'qui', 'quoi', 'où', 'quand', 
    'comment', 'pourquoi', 'parce', 'que', 'comme', 'lequel', 'laquelle', 
    'lesquels', 'lesquelles', 'de', 'lorsque', 'sans', 'sous', 'sur', 'vers', 
    'chez', 'dans', 'entre', 'parmi', 'après', 'avant', 'avec', 'chez', 'contre', 
    'dans', 'de', 'depuis', 'derrière', 'devant', 'durant', 'en', 'entre', 'envers', 
    'par', 'pour', 'sans', 'sous', 'vers', 'via', 'afin', 'ainsi', 'après', 'assez', 
    'aucun', 'aujourd', 'auquel', 'aussi', 'autant', 'autre', 'autres', 'avant', 
    'avec', 'avoir', 'bon', 'cette', 'ces', 'ceux', 'chaque', 'chez', 'comme', 
    'comment', 'dans', 'de', 'des', 'du', 'dedans', 'dehors', 'depuis', 'devant', 
    'derrière', 'dès', 'désormais', 'donc', 'dos', 'droite', 'début', 'elle', 
    'elles', 'en', 'encore', 'essai', 'est', 'et', 'eu', 'fait', 'faites', 'fois', 
    'font', 'force', 'haut', 'hors', 'ici', 'il', 'ils', 'je', 'juste', 'la', 'le', 
    'les', 'leur', 'là', 'ma', 'maintenant', 'mais', 'mes', 'mine', 'moins', 'mon', 
    'mot', 'même', 'ni', 'nommés', 'notre', 'nous', 'nouveaux', 'ou', 'où', 'par', 
    'parce', 'parole', 'pas', 'personnes', 'peut', 'peu', 'pièce', 'plupart', 'pour', 
    'pourquoi', 'quand', 'que', 'quel', 'quelle', 'quelles', 'quels', 'qui', 'sa', 
    'sans', 'ses', 'seulement', 'si', 'sien', 'son', 'sont', 'sous', 'soyez', 'sujet', 
    'sur', 'ta', 'tandis', 'tellement', 'tels', 'tes', 'ton', 'tous', 'tout', 'trop', 
    'très', 'tu', 'valeur', 'voie', 'voient', 'vont', 'votre', 'vous', 'vu', 'ça', 
    'étaient', 'état', 'étions', 'été', 'être', 'a', 'afin', 'ai', 'aie', 'aient', 
    'aies', 'ait', 'an', 'ans', 'au', 'aucun', 'aura', 'aurai', 'auraient', 'aurais', 
    'aurait', 'auras', 'aurez', 'auriez', 'aurions', 'aurons', 'auront', 'aussi', 
    'autre', 'autres', 'aux', 'auxquelles', 'auxquels', 'avaient', 'avais', 'avait', 
    'avant', 'avec', 'avez', 'aviez', 'avions', 'avoir', 'avons', 'ayant', 'ayez', 
    'ayons', 'bon', 'c', 'car', 'ce', 'ceci', 'cela', 'celle', 'celles', 'celui', 
    'cent', 'cependant', 'certain', 'certaine', 'certaines', 'certains', 'ces', 
    'cet', 'cette', 'ceux', 'chacun', 'chacune', 'chaque', 'cher', 'chère', 
    'chères', 'chers', 'chez', 'ci', 'cinq', 'comme', 'comment', 'concernant', 
    'contre', 'd', 'da', 'dans', 'de', 'dehors', 'delà', 'depuis', 'derrière', 
    'des', 'dès', 'désormais', 'desquelles', 'desquels', 'dessous', 'dessus', 
    'devant', 'devers', 'devra', 'devrait', 'devrez', 'devriez', 'devrions', 
    'devrons', 'devront', 'devrais', 'devrait', 'doit', 'doivent', 'donc', 
    'dont', 'douze', 'du', 'dû', 'durant', 'dès', 'désormais', 'e', 'elle', 
    'elles', 'en', 'encore', 'enfin', 'entre', 'envers', 'environ', 'es', 
    'est', 'et', 'étaient', 'étais', 'était', 'étant', 'etc', 'été', 'êtes', 
    'être', 'eux', 'ex', 'fait', 'fais', 'faisaient', 'faisais', 'faisait', 
    'faisant', 'fait', 'faites', 'faitons', 'fasse', 'fassent', 'fasses', 
    'faut', 'ferai', 'fera', 'feraient', 'ferais', 'ferait', 'feras', 'ferez', 
    'feriez', 'ferions', 'ferons', 'feront', 'fi', 'fois', 'font', 'force', 
    'fût', 'fussent', 'fusses', 'fût', 'fut', 'futé', 'g', 'général', 'gens', 
    'h', 'ha', 'hein', 'hélas', 'hem', 'hep', 'hi', 'ho', 'hormis', 'hors', 
    'hue', 'hui', 'huit', 'hum', 'hurrah', 'i', 'il', 'ils', 'j', 'je', 'jusque', 
    'k', 'l', 'la', 'laisser', 'laquelle', 'las', 'le', 'lequel', 'les', 'lès', 
    'lesquelles', 'lesquels', 'leur', 'leurs', 'longtemps', 'lorsque', 'lui', 
    'm', 'ma', 'maint', 'mais', 'malgré', 'me', 'merci', 'mes', 'mien', 'mienne', 
    'miennes', 'miens', 'moi', 'moins', 'mon', 'mot', 'même', 'n', 'na', 'ne', 
    'néanmoins', 'nos', 'notre', 'nous', 'nouveaux', 'nul', 'o', 'où', 'oh', 
    'ohé', 'olé', 'ollé', 'on', 'ont', 'onze', 'ou', 'où', 'ouf', 'ouias', 
    'oust', 'ouste', 'outre', 'p', 'paf', 'pan', 'par', 'parce', 'parfois', 
    'parle', 'parler', 'parmi', 'partant', 'particulier', 'pas', 'passé', 
    'pendant', 'personne', 'peu', 'peut', 'peut-être', 'pff', 'pfft', 'pfut', 
    'pif', 'plein', 'plouf', 'plus', 'plutôt', 'pouah', 'pour', 'pourquoi', 
    'premier', 'près', 'psitt', 'puisque', 'q', 'qu', 'quand', 'que', 'quel', 
    'quelle', 'quelles', 'quels', 'qui', 'quoi', 'quatrième', 'r', 'rien', 
    's', 'sa', 'sacrebleu', 'sans', 'sapristi', 'sauf', 'se', 'seize', 'selon', 
    'sept', 'sera', 'serai', 'seraient', 'serais', 'serait', 'seras', 'serez', 
    'seriez', 'serions', 'serons', 'seront', 'ses', 'seul', 'si', 'sien', 
    'sienne', 'siennes', 'siens', 'sinon', 'six', 'soi', 'soi-même', 'soit', 
    'soixante', 'son', 'sont', 'sous', 'stop', 'suis', 'suivant', 'sur', 
    'surtout', 't', 'ta', 'tac', 'tant', 'te', 'té', 'tel', 'telle', 'tellement', 
    'telles', 'tels', 'tenant', 'tes', 'tic', 'tien', 'tienne', 'tiennes', 
    'tiens', 'toc', 'toi', 'toi-même', 'ton', 'touchant', 'toujours', 'tous', 
    'tout', 'toute', 'toutes', 'treize', 'trente', 'très', 'trois', 'trop', 
    'tsoin', 'tsouin', 'tu', 'u', 'un', 'une', 'unes', 'uns', 'v', 'va', 
    'vais', 'vas', 'vé', 'vers', 'via', 'vif', 'vifs', 'vingt', 'vivat', 
    'vive', 'vives', 'vous', 'voyez', 'vu', 'w', 'x', 'y', 'z', 'zut'
]

def clean_text(text):
    # Convertir en minuscules
    text = text.lower()
    # Supprimer les caractères spéciaux et diviser en mots
    words = re.findall(r'\b\w+\b', text)
    # Filtrer les stopwords
    words = [word for word in words if word not in stopwords_fr]
    # Mettre les mots au singulier
    words = [word.rstrip('s') for word in words] # Simplified singular form
    return ' '.join(words)

def get_openai_embeddings(text, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "text-embedding-3-small",
        "input": text,
        "encoding_format": "float"
    }
    response = requests.post('https://api.openai.com/v1/embeddings', headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        st.error("Error fetching embeddings from OpenAI API")
        return None

def generate_embeddings(texts, api_key):
    embeddings = []
    for text in texts:
        cleaned_text = clean_text(text)
        embedding = get_openai_embeddings(cleaned_text, api_key)
        if embedding:
            embeddings.append(embedding)
    return embeddings

def app():
    st.title("Génération des Embeddings pour un site E-commerce")

    # Lire la clé API depuis les secrets
    try:
        api_key = st.secrets["api_key"]
    except KeyError:
        st.error("Clé API OpenAI manquante dans les secrets. Veuillez la définir dans les paramètres de votre application Streamlit.")
        return

    uploaded_file = st.file_uploader("Choisissez un fichier Excel ou CSV", type=["xlsx", "csv"])
    
    if uploaded_file:
        file_type = uploaded_file.name.split('.')[-1]
        
        if file_type == 'xlsx':
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif file_type == 'csv':
            df = pd.read_csv(uploaded_file)
        
        st.write("Aperçu des données :")
        st.write(df.head())
        
        url_column = st.selectbox("Sélectionnez la colonne des URL", df.columns)
        embedding_column = st.selectbox("Sélectionnez la colonne pour les Embeddings", df.columns)

        if st.button("Générer les Embeddings"):
            if api_key:
                with st.spinner("Génération des embeddings en cours..."):
                    texts = df[url_column].tolist()
                    embeddings = generate_embeddings(texts, api_key)
                    
                    df[embedding_column] = embeddings
                    st.write("Embeddings générés avec succès !")
                    st.write(df.head())

                st.download_button(label="Télécharger le fichier avec Embeddings",
                                   data=df.to_csv(index=False).encode('utf-8'),
                                   file_name='embeddings_output.csv',
                                   mime='text/csv')
            else:
                st.error("Veuillez entrer votre clé API OpenAI")

if __name__ == "__main__":
    app()


