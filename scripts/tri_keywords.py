import streamlit as st
import pandas as pd
import re
from collections import defaultdict

# Liste de stopwords français
STOPWORDS = set([
    'le', 'la', 'les', 'l', 'un', 'une', 'des', 'du', 'de', 'a', 'à', 'au', 'aux',
    'et', 'ou', 'mais', 'donc', 'car', 'ni', 'or', 'que', 'qui', 'quoi', 'dont', 'où',
    'ce', 'cet', 'cette', 'ces', 'mon', 'ton', 'son', 'notre', 'votre', 'leur',
    'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'me', 'te', 'se', 'lui',
    'en', 'y', 'pour', 'par', 'avec', 'sans', 'sous', 'sur', 'dans', 'entre', 'vers',
    'chez', 'hors', 'de', 'avant', 'après', 'pendant', 'depuis', 'durant',
    'être', 'avoir', 'faire', 'dire', 'aller', 'voir', 'venir', 'devoir', 'pouvoir',
    'vouloir', 'falloir', 'savoir',
    'tout', 'tous', 'toute', 'toutes', 'aucun', 'aucune', 'autre', 'autres',
    'même', 'mêmes', 'tel', 'telle', 'tels', 'telles',
    'peu', 'plupart', 'beaucoup', 'plus', 'moins', 'très', 'assez', 'trop',
    'comment', 'pourquoi', 'quand', 'si', 'ne', 'pas', 'plus', 'jamais', 'toujours',
    'ici', 'là', 'voici', 'voilà', 'alors', 'ainsi', 'comme', 'bien', 'mal',
    'oui', 'non', 'peut-être',
])

def remove_stopwords(text):
    return ' '.join([word for word in text.lower().split() if word not in STOPWORDS])

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = remove_stopwords(text)
    return text

def are_similar(kw1, kw2, threshold=0.8):
    set1 = set(kw1.split())
    set2 = set(kw2.split())
    intersection = set1.intersection(set2)
    return len(intersection) / max(len(set1), len(set2)) >= threshold

def app():
    st.title("Tri et Nettoyage de mots-clés")

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Sélection des colonnes
        keyword_column = st.selectbox("Sélectionnez la colonne contenant les mots-clés", df.columns)
        volume_column = st.selectbox("Sélectionnez la colonne contenant les volumes", df.columns)
        
        if st.button("Traiter"):
            # Nettoyage des mots-clés
            df['cleaned_keywords'] = df[keyword_column].apply(clean_text)
            
            # Tri et nettoyage des mots-clés similaires
            keyword_dict = defaultdict(lambda: {'keyword': '', 'volume': 0})
            
            for _, row in df.iterrows():
                cleaned_kw = row['cleaned_keywords']
                volume = row[volume_column]
                
                similar_found = False
                for key in keyword_dict:
                    if are_similar(cleaned_kw, key):
                        if volume > keyword_dict[key]['volume']:
                            keyword_dict[key] = {'keyword': row[keyword_column], 'volume': volume}
                        similar_found = True
                        break
                
                if not similar_found:
                    keyword_dict[cleaned_kw] = {'keyword': row[keyword_column], 'volume': volume}
            
            # Création d'un nouveau DataFrame avec les mots-clés uniques
            unique_keywords = pd.DataFrame.from_dict(keyword_dict, orient='index')
            unique_keywords = unique_keywords.reset_index(drop=True)
            
            # Affichage des résultats
            st.write("Mots-clés uniques après nettoyage :")
            st.dataframe(unique_keywords)
            
            # Option de téléchargement
            csv = unique_keywords.to_csv(index=False)
            st.download_button(
                label="Télécharger les résultats en CSV",
                data=csv,
                file_name="mots_cles_uniques.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    app()
