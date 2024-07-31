import streamlit as st
import pandas as pd
import re
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertModel, BertTokenizer
import torch

def remove_html_tags(text):
    if not isinstance(text, str):
        return ''
    return BeautifulSoup(text, "html.parser").get_text()

def clean_text(text):
    if not isinstance(text, str):
        return ''
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def get_bert_embedding(text, model, tokenizer):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).numpy()

def find_similarities(text1, text2, vectorizers, bert_model, bert_tokenizer):
    vectors1 = [vectorizer.transform([text1]).toarray() for vectorizer in vectorizers]
    vectors2 = [vectorizer.transform([text2]).toarray() for vectorizer in vectorizers]

    bert_vector1 = get_bert_embedding(text1, bert_model, bert_tokenizer)
    bert_vector2 = get_bert_embedding(text2, bert_model, bert_tokenizer)
    bert_similarity = cosine_similarity(bert_vector1, bert_vector2)[0][0]

    similarities = [cosine_similarity(v1, v2)[0][0] for v1, v2 in zip(vectors1, vectors2)]
    similarities.append(bert_similarity)
    return sum(similarities) / len(similarities)

def app():
    st.title('Application de Catégorisation de Produits')
    uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])

    if uploaded_file is not None:
        # Lire le fichier Excel et afficher les noms des feuilles
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names

        st.write("Feuilles disponibles :", sheet_names)

        # Sélection de la feuille principale et secondaire
        primary_sheet = st.selectbox("Sélectionnez la feuille principale", sheet_names)
        secondary_sheet = st.selectbox("Sélectionnez la feuille secondaire", sheet_names)

        if primary_sheet and secondary_sheet:
            df_primary = pd.read_excel(xls, sheet_name=primary_sheet)
            df_secondary = pd.read_excel(xls, sheet_name=secondary_sheet)

            st.write("Aperçu des données de la feuille principale :", df_primary.head())
            st.write("Aperçu des données de la feuille secondaire :", df_secondary.head())

            # Sélection des colonnes
            product_title_col = st.selectbox("Sélectionnez la colonne pour le titre du produit", df_primary.columns)
            product_desc_col = st.selectbox("Sélectionnez la colonne pour la description du produit", df_primary.columns)
            collection_name_col = st.selectbox("Sélectionnez la colonne pour le nom de collection", df_secondary.columns)

            if st.button("Catégoriser les produits"):
                df_primary['Catégorisation'] = ''

                # Obtenir les noms de collections tels quels
                collections = df_secondary[collection_name_col].dropna().tolist()

                # Nettoyer la colonne de description
                df_primary[product_desc_col] = df_primary[product_desc_col].apply(remove_html_tags)

                # Combiner les titres et descriptions pour chaque produit
                df_primary['combined_text'] = df_primary[product_title_col] + " " + df_primary[product_desc_col]

                # Nettoyer les textes combinés
                df_primary['combined_text'] = df_primary['combined_text'].apply(clean_text)

                # Nettoyer les noms de collections
                cleaned_collections = [clean_text(collection) for collection in collections]

                # Préparer les vectorizers TF-IDF et Count Vectorizer
                tfidf_vectorizer = TfidfVectorizer().fit(df_primary['combined_text'].tolist() + cleaned_collections)
                count_vectorizer = CountVectorizer().fit(df_primary['combined_text'].tolist() + cleaned_collections)
                vectorizers = [tfidf_vectorizer, count_vectorizer]

                # Charger BERT
                bert_model = BertModel.from_pretrained('bert-base-uncased')
                bert_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

                # Calculer les embeddings BERT pour les collections
                collection_embeddings = [get_bert_embedding(collection, bert_model, bert_tokenizer) for collection in cleaned_collections]

                for i, row in df_primary.iterrows():
                    combined_text = row['combined_text']
                    matched_collections = []
                    product_bert_embedding = get_bert_embedding(combined_text, bert_model, bert_tokenizer)
                    
                    for collection, cleaned_collection, collection_embedding in zip(collections, cleaned_collections, collection_embeddings):
                        similarity = find_similarities(combined_text, cleaned_collection, vectorizers, bert_model, bert_tokenizer)
                        bert_similarity = cosine_similarity(product_bert_embedding, collection_embedding)[0][0]
                        final_similarity = (similarity + bert_similarity) / 2  # Moyenne des similarités
                        
                        if final_similarity > 0.1:  # Seuil de similarité (ajustable)
                            matched_collections.append(collection)

                    if matched_collections:
                        df_primary.at[i, 'Catégorisation'] = ', '.join(matched_collections)

                # S'assurer que chaque collection est associée au moins une fois
                for collection in collections:
                    if collection not in df_primary['Catégorisation'].str.cat(sep=', '):
                        st.warning(f"La collection '{collection}' n'a pas été associée à un produit.")

                st.write("Données après catégorisation :", df_primary.head())

                @st.cache
                def convert_df(df):
                    return df.to_csv(index=False).encode('utf-8')

                csv = convert_df(df_primary)

                st.download_button(
                    label="Télécharger les données avec catégorisation",
                    data=csv,
                    file_name='produits_categorises.csv',
                    mime='text/csv',
                )

# Assurez-vous d'installer les packages nécessaires :
# pip install streamlit pandas scikit-learn beautifulsoup4 openpyxl transformers torch
