import streamlit as st
import pandas as pd
import re
from collections import Counter

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
    # Ajoutez d'autres stopwords si nécessaire
])

def remove_stopwords(text):
    return ' '.join([word for word in text.lower().split() if word not in STOPWORDS])

def clean_text(text):
    # Convertir en minuscules
    text = text.lower()
    # Supprimer la ponctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Supprimer les chiffres
    text = re.sub(r'\d+', '', text)
    # Supprimer les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    # Supprimer les stopwords
    text = remove_stopwords(text)
    return text

def app():
    st.title("Tri et Nettoyage de mots-clés")

    uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Sélection de la colonne contenant les mots-clés
        column = st.selectbox("Sélectionnez la colonne contenant les mots-clés", df.columns)
        
        if st.button("Traiter"):
            # Nettoyage des mots-clés
            df['cleaned_keywords'] = df[column].apply(clean_text)
            
            # Comptage des mots
            all_words = ' '.join(df['cleaned_keywords']).split()
            word_counts = Counter(all_words)
            
            # Création d'un nouveau DataFrame avec les mots et leur fréquence
            word_freq_df = pd.DataFrame(word_counts.items(), columns=['Mot', 'Fréquence'])
            word_freq_df = word_freq_df.sort_values('Fréquence', ascending=False)
            
            # Affichage des résultats
            st.write("Mots-clés les plus fréquents :")
            st.dataframe(word_freq_df)
            
            # Option de téléchargement
            csv = word_freq_df.to_csv(index=False)
            st.download_button(
                label="Télécharger les résultats en CSV",
                data=csv,
                file_name="mots_cles_frequents.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    app()
