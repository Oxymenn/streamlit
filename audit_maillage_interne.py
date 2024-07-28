import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

@st.cache_data
def load_data(file):
    return pd.read_excel(file)

@st.cache_data
def calculate_cosine_similarity(embeddings):
    return cosine_similarity(embeddings)

def convert_embeddings(embedding_str):
    return np.array(eval(embedding_str))

st.set_page_config(page_title="Audit Sémantique", layout="wide")
st.title("Audit Sémantique via Word Embedding")

st.markdown("""
## Comment utiliser cette application

1. Uploadez votre fichier Excel contenant les URLs et les embeddings.
2. Sélectionnez les colonnes correspondant aux URLs et aux embeddings.
3. Cliquez sur "Calculer la similarité" pour générer la matrice de similarité cosinus.
4. Visualisez la matrice de similarité cosinus pour toutes les URLs.
5. Utilisez le filtre pour sélectionner une URL spécifique et voir les URLs les plus proches sémantiquement.

La similarité cosinus est utilisée pour mesurer la proximité sémantique entre les embeddings. 
Une valeur proche de 1 indique une forte similarité, tandis qu'une valeur proche de 0 indique une faible similarité.
""")

uploaded_file = st.file_uploader("Choisissez votre fichier Excel", type="xlsx")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    url_column = st.selectbox("Sélectionnez la colonne des URLs", df.columns)
    embedding_column = st.selectbox("Sélectionnez la colonne des embeddings", df.columns)
    
    if st.button("Calculer la similarité"):
        with st.spinner('Calcul en cours...'):
            df['embedding_array'] = df[embedding_column].apply(convert_embeddings)
            embeddings_array = np.array(df['embedding_array'].tolist())
            similarity_matrix = calculate_cosine_similarity(embeddings_array)
            similarity_df = pd.DataFrame(similarity_matrix, columns=df[url_column], index=df[url_column])
        
        st.session_state['similarity_df'] = similarity_df
        st.session_state['calculated'] = True
        
        st.subheader("Matrice de similarité cosinus")
        st.dataframe(similarity_df)
    
    if 'calculated' in st.session_state and st.session_state['calculated']:
        similarity_df = st.session_state['similarity_df']
        
        # Sélectionner la première URL par défaut
        default_url = df[url_column].iloc[0]
        selected_url = st.selectbox("Sélectionnez une URL spécifique", df[url_column], index=0)
        
        if selected_url:
            similarities = similarity_df[selected_url].sort_values(ascending=False)
            result_df = pd.DataFrame({
                'URL': similarities.index,
                'Similarité': similarities.values
            })
            result_df = result_df[result_df['URL'] != selected_url]
            
            st.subheader(f"URLs les plus proches sémantiquement de {selected_url}")
            st.dataframe(result_df)
            
            st.subheader("Visualisation des similarités")
            chart_data = result_df.head(10)
            st.bar_chart(chart_data.set_index('URL')['Similarité'])
            
            csv = result_df.to_csv(index=False)
            st.download_button(
                label="Télécharger les résultats en CSV",
                data=csv,
                file_name="resultats_similarite.csv",
                mime="text/csv",
            )
else:
    st.info("Veuillez uploader un fichier Excel pour commencer l'analyse.")
