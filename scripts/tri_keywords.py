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
    keyword = unidecode(keyword.lower())
    keyword = re.sub(r'[^\w\s]', '', keyword)
    keyword = re.sub(r'\d+', '', keyword)
    keyword = re.sub(r'\s+', ' ', keyword).strip()
    words = [word for word in keyword.split() if word not in STOPWORDS]
    words = [word[:-1] if word.endswith('s') and len(word) > 3 else word for word in words]
    return ' '.join(sorted(words))

def process_keywords(df, keyword_column, volume_column):
    keyword_groups = defaultdict(list)
    
    for _, row in df.iterrows():
        keyword = row[keyword_column]
        volume = row[volume_column]
        normalized_kw = normalize_keyword(keyword)
        keyword_groups[normalized_kw].append((keyword, volume))
    
    unique_keywords = {}
    for group in keyword_groups.values():
        unique_keyword, max_volume = max(group, key=lambda x: x[1])
        unique_keywords[normalize_keyword(unique_keyword)] = (unique_keyword, max_volume)
    
    return unique_keywords

def app():
    st.title("Tri et Nettoyage de mots-clés")

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        keyword_column = st.selectbox("Sélectionnez la colonne contenant les mots-clés", df.columns)
        volume_column = st.selectbox("Sélectionnez la colonne contenant les volumes", df.columns)
        
        if st.button("Traiter"):
            unique_keywords = process_keywords(df, keyword_column, volume_column)
            
            df['Mot-clé unique'] = df[keyword_column].apply(lambda x: unique_keywords[normalize_keyword(x)][0])
            df['Volume unique'] = df[keyword_column].apply(lambda x: unique_keywords[normalize_keyword(x)][1])
            
            st.write("Résultats après traitement :")
            st.dataframe(df)
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Télécharger les résultats en CSV",
                data=csv,
                file_name="mots_cles_traites.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    app()
