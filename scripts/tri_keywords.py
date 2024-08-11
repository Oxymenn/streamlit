import streamlit as st
import pandas as pd
import re
from collections import defaultdict
from unidecode import unidecode

# Liste de stopwords français
STOPWORDS = set([
    'le', 'la', 'les', 'l', 'un', 'une', 'des', 'du', 'a', 'à', 'au', 'aux',
    'et', 'ou', 'mais', 'donc', 'car', 'ni', 'or', 'que', 'qui', 'quoi', 'dont', 'où',
    'ce', 'cet', 'cette', 'ces', 'mon', 'ton', 'son', 'notre', 'votre', 'leur',
    'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'me', 'te', 'se', 'lui',
    'en', 'y', 'pour', 'par', 'avec', 'sans', 'sous', 'sur', 'dans', 'entre', 'vers',
    'chez', 'hors', 'avant', 'après', 'pendant', 'depuis', 'durant',
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
    
    # Traiter les pluriels spécifiques et autres cas particuliers
    keyword = re.sub(r'tables? de chevet', 'table chevet', keyword)
    keyword = re.sub(r'machines? a? cafe', 'machine cafe', keyword)
    
    words = keyword.split()
    filtered_words = []
    for word in words:
        if word not in STOPWORDS or word in ['de', 'a']:
            # Supprimer les terminaisons pour gérer le genre, le nombre et certains adjectifs
            word = re.sub(r'(e|s|es|he|che|ee)$', '', word)
            filtered_words.append(word)
    
    # Trier les mots pour gérer l'ordre différent
    return ' '.join(sorted(filtered_words))

def process_keywords(df, keyword_column, volume_column):
    keyword_groups = defaultdict(list)
    
    for _, row in df.iterrows():
        keyword = row[keyword_column]
        volume = row[volume_column]
        normalized_kw = normalize_keyword(keyword)
        keyword_groups[normalized_kw].append((keyword, volume))
    
    unique_keywords = []
    for group in keyword_groups.values():
        # Sélectionner le mot-clé avec le plus gros volume dans le groupe
        unique_keyword, max_volume = max(group, key=lambda x: x[1])
        unique_keywords.append((unique_keyword, max_volume))
    
    return unique_keywords

def app():
    st.title("Tri et Nettoyage de mots-clés")

    if 'processed_df' not in st.session_state:
        st.session_state.processed_df = None
    if 'file_uploaded' not in st.session_state:
        st.session_state.file_uploaded = False

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")
    
    if uploaded_file is not None and not st.session_state.file_uploaded:
        st.session_state.df = pd.read_csv(uploaded_file)
        st.session_state.file_uploaded = True
    
    if st.session_state.file_uploaded:
        keyword_column = st.selectbox("Sélectionnez la colonne contenant les mots-clés", st.session_state.df.columns)
        volume_column = st.selectbox("Sélectionnez la colonne contenant les volumes", st.session_state.df.columns)
        
        if st.button("Traiter"):
            unique_keywords = process_keywords(st.session_state.df, keyword_column, volume_column)
            
            unique_df = pd.DataFrame(unique_keywords, columns=['Mot-clé unique', 'Volume unique'])
            unique_df = unique_df.sort_values('Volume unique', ascending=False)
            
            st.session_state.df['Mot-clé unique'] = ''
            st.session_state.df['Volume unique'] = 0
            
            st.session_state.df.loc[:len(unique_df)-1, 'Mot-clé unique'] = unique_df['Mot-clé unique'].values
            st.session_state.df.loc[:len(unique_df)-1, 'Volume unique'] = unique_df['Volume unique'].values
            
            st.session_state.processed_df = st.session_state.df

        if st.session_state.processed_df is not None:
            st.write("Résultats après traitement :")
            st.dataframe(st.session_state.processed_df)
            
            csv = st.session_state.processed_df.to_csv(index=False)
            st.download_button(
                label="Télécharger les résultats en CSV",
                data=csv,
                file_name="mots_cles_traites.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    app()
