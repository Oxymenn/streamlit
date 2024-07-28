import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import re

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
    return ' '.join(words)

# Charger le modèle Sentence-BERT
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

def generate_embeddings(texts):
    cleaned_texts = [clean_text(text) for text in texts]
    embeddings = model.encode(cleaned_texts)
    return embeddings.tolist()

def app():
    st.title("Audit de Maillage Interne")

    uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file, sheet_name=None, engine='openpyxl')
        sheet_names = list(df.keys())
        
        st.write("Aperçu des feuilles :")
        st.write(sheet_names)
        
        main_sheet = st.selectbox("Choisissez la feuille contenant les données principales", sheet_names)
        secondary_sheet = st.selectbox("Choisissez la feuille contenant les données secondaires", sheet_names)
        
        if main_sheet and secondary_sheet:
            main_df = df[main_sheet]
            secondary_df = df[secondary_sheet]
            
            st.write("Aperçu des données principales :")
            st.write(main_df.head())
            
            st.write("Aperçu des données secondaires :")
            st.write(secondary_df.head())
            
            url_column_main = st.selectbox("Colonne des URL de départ", main_df.columns)
            url_column_secondary = st.selectbox("Colonne des URL de destination", secondary_df.columns)
            embedding_column = st.selectbox("Colonne des embeddings", secondary_df.columns)
            anchor_column = st.selectbox("Colonne des ancres de liens", secondary_df.columns)
            min_links = st.number_input("Nombre minimum de liens pour une URL de destination (nécessaire pour le calcul des métriques de maillage interne)", min_value=1, value=5)
            
            if st.button("Générer les Embeddings et Rapports"):
                with st.spinner("Génération des embeddings en cours..."):
                    texts = main_df[url_column_main].tolist()
                    embeddings = generate_embeddings(texts)
                    
                    secondary_df[embedding_column] = embeddings
                    
                    # Calcul des métriques de maillage interne
                    metrics = calculate_internal_link_metrics(main_df, secondary_df, url_column_main, url_column_secondary, min_links)
                    
                    st.write("Métriques de maillage interne pour chaque URL de destination :")
                    st.write(metrics)
                    
                    st.download_button(label="Télécharger le fichier avec Embeddings",
                                       data=secondary_df.to_csv(index=False).encode('utf-8'),
                                       file_name='embeddings_output.csv',
                                       mime='text/csv')
                    
                    # Visualisation des graphiques
                    display_gauges(metrics, url_column_main, url_column_secondary)

def calculate_internal_link_metrics(main_df, secondary_df, url_column_main, url_column_secondary, min_links):
    # Fonction de calcul des métriques de maillage interne
    # Pour chaque URL de destination, calculer le nombre de liens existants, à conserver, à retirer et à remplacer
    metrics = pd.DataFrame(columns=["URL de destination", "Nombre de liens existants", "Nombre de liens à conserver", "Nombre de liens à retirer", "Nombre de liens à remplacer"])
    # Remplir le DataFrame metrics avec les valeurs calculées
    for url in secondary_df[url_column_secondary].unique():
        existing_links = len(main_df[main_df[url_column_main] == url])
        links_to_keep = min(existing_links, min_links)
        links_to_remove = max(0, existing_links - links_to_keep)
        links_to_replace = min_links - links_to_keep
        metrics = metrics.append({"URL de destination": url, "Nombre de liens existants": existing_links, "Nombre de liens à conserver": links_to_keep, "Nombre de liens à retirer": links_to_remove, "Nombre de liens à remplacer": links_to_replace}, ignore_index=True)
    return metrics

def display_gauges(metrics, url_column_main, url_column_secondary):
    # Fonction d'affichage des graphiques de jauge
    st.write("Visualisation des scores de maillage interne")
    
    selected_start_url = st.selectbox("Sélectionnez des URLs de départ", metrics["URL de destination"].unique())
    selected_end_url = st.selectbox("Sélectionnez des URLs de destination", metrics["URL de destination"].unique())
    
    if selected_start_url and selected_end_url:
        # Calcul des scores de maillage interne
        internal_link_score = calculate_internal_link_score(metrics, selected_start_url, selected_end_url)
        replacement_percentage = calculate_replacement_percentage(metrics, selected_start_url, selected_end_url)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Score moyen de maillage interne (sur une base de 5 liens internes minimum)")
            st.write(internal_link_score)
        
        with col2:
            st.write("Pourcentage de liens à remplacer et/ou à ajouter (sur une base de 5 liens internes minimum)")
            st.write(replacement_percentage)

def calculate_internal_link_score(metrics, start_url, end_url):
    # Fonction de calcul du score moyen de maillage interne
    return metrics[(metrics["URL de destination"] == start_url) & (metrics["URL de destination"] == end_url)]["Nombre de liens à conserver"].mean()

def calculate_replacement_percentage(metrics, start_url, end_url):
    # Fonction de calcul du pourcentage de liens à remplacer et/ou à ajouter
    return metrics[(metrics["URL de destination"] == start_url) & (metrics["URL de destination"] == end_url)]["Nombre de liens à remplacer"].mean()

if __name__ == "__main__":
    app()
