import streamlit as st
import pandas as pd
import time
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Fonction pour simuler le scraping des SERP (à remplacer par une vraie fonction de scraping)
def scrape_serp(keyword):
    # Simuler les résultats de recherche
    return [f"https://example.com/{keyword}_{i}" for i in range(10)]

# Fonction pour calculer la similarité entre deux listes d'URLs
def calculate_similarity(urls1, urls2):
    vectorizer = TfidfVectorizer().fit_transform(urls1 + urls2)
    vectors = vectorizer.toarray()
    similarity = cosine_similarity([vectors[:10].mean(axis=0)], [vectors[10:].mean(axis=0)])[0][0]
    return similarity

# Fonction principale
def main():
    st.title("Comparaison de Similarité des SERP")

    # Charger le fichier CSV ou Excel
    uploaded_file = st.file_uploader("Charger un fichier CSV ou Excel", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.write("Fichier chargé avec succès.")

            # Sélectionner les colonnes des mots clés et des volumes
            keyword_column = st.selectbox("Sélectionner la colonne des mots clés", df.columns)
            volume_column = st.selectbox("Sélectionner la colonne des volumes", df.columns)

            # Sélectionner le pourcentage de similarité
            similarity_threshold = st.slider("Sélectionner le pourcentage de similarité", 10, 100, 40, 10) / 100

            # Sélectionner le délai de scrape
            min_delay, max_delay = st.slider("Sélectionner le délai de scrape (en secondes)", 1, 60, (1, 10))

            # Bouton pour lancer le scraping et la comparaison
            if st.button("Lancer la comparaison"):
                unique_keywords = []
                unique_volumes = []

                for index, row in df.iterrows():
                    keyword = row[keyword_column]
                    volume = row[volume_column]

                    st.write(f"Traitement du mot clé: {keyword}")

                    # Simuler le scraping des SERP
                    serp_results = scrape_serp(keyword)

                    # Comparer avec les mots clés déjà traités
                    similar = False
                    for i, unique_keyword in enumerate(unique_keywords):
                        unique_serp_results = scrape_serp(unique_keyword)
                        similarity = calculate_similarity(serp_results, unique_serp_results)
                        if similarity >= similarity_threshold:
                            similar = True
                            if volume > unique_volumes[i]:
                                unique_keywords[i] = keyword
                                unique_volumes[i] = volume
                            break

                    if not similar:
                        unique_keywords.append(keyword)
                        unique_volumes.append(volume)

                    # Attendre le délai de scrape
                    delay = random.uniform(min_delay, max_delay)
                    time.sleep(delay)

                # Créer un DataFrame avec les résultats
                result_df = pd.DataFrame({
                    "Mots-clés uniques": unique_keywords,
                    "Volumes": unique_volumes
                })

                # Trier par ordre décroissant de volume
                result_df = result_df.sort_values(by="Volumes", ascending=False)

                # Afficher les résultats
                st.write(result_df)

                # Exporter les résultats en CSV
                st.download_button(
                    label="Télécharger les résultats en CSV",
                    data=result_df.to_csv(index=False),
                    file_name="resultats_cannibalisation.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Une erreur s'est produite: {e}")

if __name__ == "__main__":
    main()
