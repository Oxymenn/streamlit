import streamlit as st
import pandas as pd
import re
from collections import defaultdict
from unidecode import unidecode

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

def normalize_keyword(keyword):
    # Supprimer les accents, mettre en minuscules et supprimer la ponctuation
    keyword = unidecode(keyword.lower())
    keyword = re.sub(r'[^\w\s]', '', keyword)
    
    # Supprimer les stopwords
    words = [word for word in keyword.split() if word not in STOPWORDS]
    
    # Supprimer les 's' à la fin des mots pour gérer singulier/pluriel
    words = [word[:-1] if word.endswith('s') and len(word) > 3 else word for word in words]
    
    # Trier les mots pour gérer l'ordre différent
    return ' '.join(sorted(words))

def are_similar(kw1, kw2):
    return normalize_keyword(kw1) == normalize_keyword(kw2)

def app():
    st.title("Tri et Nettoyage de mots-clés")

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Sélection des colonnes
        keyword_column = st.selectbox("Sélectionnez la colonne contenant les mots-clés", df.columns)
        volume_column = st.selectbox("Sélectionnez la colonne contenant les volumes", df.columns)
        
        if st.button("Traiter"):
            # Tri et nettoyage des mots-clés similaires
            keyword_dict = defaultdict(lambda: {'keyword': '', 'volume': 0})
            
            for _, row in df.iterrows():
                keyword = row[keyword_column]
                volume = row[volume_column]
                normalized_kw = normalize_keyword(keyword)
                
                if volume > keyword_dict[normalized_kw]['volume']:
                    keyword_dict[normalized_kw] = {'keyword': keyword, 'volume': volume}
            
            # Création d'un nouveau DataFrame avec les mots-clés uniques
            unique_keywords = pd.DataFrame.from_dict(keyword_dict, orient='index')
            unique_keywords = unique_keywords.reset_index(drop=True)
            unique_keywords.columns = ['Mot-clé unique', 'Volume associé']
            
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
