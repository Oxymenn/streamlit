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
    # Supprimer les accents et mettre en minuscules
    keyword = unidecode(keyword.lower())
    
    # Supprimer la ponctuation et les chiffres
    keyword = re.sub(r'[^\w\s]', '', keyword)
    keyword = re.sub(r'\d+', '', keyword)
    
    # Supprimer les espaces supplémentaires
    keyword = re.sub(r'\s+', ' ', keyword).strip()
    
    # Supprimer les stopwords
    words = [word for word in keyword.split() if word not in STOPWORDS]
    
    # Supprimer les 's' à la fin des mots pour gérer singulier/pluriel
    words = [word[:-1] if word.endswith('s') and len(word) > 3 else word for word in words]
    
    # Trier les mots pour gérer l'ordre différent
    return ' '.join(sorted(words))

def group_similar_keywords(df, keyword_column, volume_column):
    keyword_groups = defaultdict(list)
    
    for _, row in df.iterrows():
        keyword = row[keyword_column]
        volume = row[volume_column]
        normalized_kw = normalize_keyword(keyword)
        keyword_groups[normalized_kw].append((keyword, volume))
    
    return keyword_groups

def find_unique_keywords(keyword_groups):
    unique_keywords = {}
    for normalized_kw, group in keyword_groups.items():
        # Sélectionner le mot-clé avec le plus gros volume dans le groupe
        unique_keyword, max_volume = max(group, key=lambda x: x[1])
        unique_keywords[normalized_kw] = (unique_keyword, max_volume)
    
    return unique_keywords

def app():
    st.title("Tri et Nettoyage de mots-clés")

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Sélection des colonnes
        keyword_column = st.selectbox("Sélectionnez la colonne contenant les mots-clés", df.columns)
        volume_column = st.selectbox("Sélectionnez la colonne contenant les volumes", df.columns)
        
        if st.button("Traiter"):
            # Grouper les mots-clés similaires
            keyword_groups = group_similar_keywords(df, keyword_column, volume_column)
            
            # Trouver les mots-clés uniques
            unique_keywords = find_unique_keywords(keyword_groups)
            
            # Création des nouvelles colonnes
            df['Mot-clé unique'] = df[keyword_column].apply(lambda x: unique_keywords[normalize_keyword(x)][0])
            df['Volume associé'] = df[keyword_column].apply(lambda x: unique_keywords[normalize_keyword(x)][1])
            
            # Affichage des résultats
            st.write("Résultats après traitement :")
            st.dataframe(df)
            
            # Option de téléchargement
            csv = df.to_csv(index=False)
            st.download_button(
                label="Télécharger les résultats en CSV",
                data=csv,
                file_name="mots_cles_traites.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    app()
