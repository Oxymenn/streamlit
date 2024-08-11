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
    
    # Traiter les mots spécifiques
    keyword = keyword.replace('table de chevet', 'table chevet')
    
    words = keyword.split()
    filtered_words = []
    for word in words:
        if word not in STOPWORDS or word == 'de':
            filtered_words.append(word)
    
    # Supprimer les terminaisons en 'e', 's', 'es' pour gérer le genre et le nombre
    filtered_words = [re.sub(r'e?s?$', '', word) if len(word) > 3 else word for word in filtered_words]
    
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

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Sélection des colonnes
        keyword_column = st.selectbox("Sélectionnez la colonne contenant les mots-clés", df.columns)
        volume_column = st.selectbox("Sélectionnez la colonne contenant les volumes", df.columns)
        
        if st.button("Traiter"):
            # Traiter les mots-clés
            unique_keywords = process_keywords(df, keyword_column, volume_column)
            
            # Création d'un nouveau DataFrame pour les mots-clés uniques
            unique_df = pd.DataFrame(unique_keywords, columns=['Mot-clé unique', 'Volume unique'])
            
            # Trier par volume décroissant
            unique_df = unique_df.sort_values('Volume unique', ascending=False)
            
            # Ajouter les nouvelles colonnes au DataFrame original
            df['Mot-clé unique'] = ''
            df['Volume unique'] = 0
            
            # Remplir les nouvelles colonnes avec les valeurs uniques
            df.loc[:len(unique_df)-1, 'Mot-clé unique'] = unique_df['Mot-clé unique'].values
            df.loc[:len(unique_df)-1, 'Volume unique'] = unique_df['Volume unique'].values
            
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
