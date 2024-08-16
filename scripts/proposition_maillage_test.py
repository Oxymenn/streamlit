def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

@st.cache_data
def process_data(urls_list, df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords, api_key):
    start_time = time.time()
    max_workers = min(20, len(urls_list) // 10 + 1)  # Ajuste dynamiquement le nombre de threads
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    time_text = st.empty()
    
    def update_progress(current, total):
        progress = current / total
        progress_bar.progress(progress)
        elapsed_time = time.time() - start_time
        estimated_total_time = elapsed_time / progress if progress > 0 else 0
        remaining_time = estimated_total_time - elapsed_time
        status_text.text(f"Analysé {current}/{total} URLs")
        time_text.text(f"Temps écoulé: {format_time(elapsed_time)} | Temps restant estimé: {format_time(remaining_time)}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        contents = list(executor.map(lambda url: extract_and_clean_content(url, include_classes, exclude_classes, additional_stopwords), urls_list))
        for i, _ in enumerate(contents, 1):
            update_progress(i, len(urls_list))
    
    contents = [content for content in contents if content]

    if not contents:
        return None, "Aucun contenu n'a pu être extrait des URLs fournies.", time.time() - start_time

    status_text.text("Génération des embeddings...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        embeddings = list(executor.map(lambda content: get_embeddings(content, api_key), contents))
        for i, _ in enumerate(embeddings, 1):
            update_progress(i, len(contents))
    
    embeddings = [emb for emb in embeddings if emb is not None]

    if not embeddings:
        return None, "Impossible de générer des embeddings pour les contenus extraits. Vérifiez votre clé API et les limites de votre compte.", time.time() - start_time

    status_text.text("Calcul des similarités...")
    similarity_matrix = calculate_similarity(embeddings)

    if similarity_matrix is None:
        return None, "Erreur lors du calcul de la similarité.", time.time() - start_time

    status_text.text("Génération des résultats...")
    results = []
    for i, url_start in enumerate(urls_list):
        similarities = similarity_matrix[i]
        similar_urls = sorted(zip(urls_list, similarities), key=lambda x: x[1], reverse=True)
        
        similar_urls = [(url, sim) for url, sim in similar_urls if url != url_start]

        for j, (url_dest, sim) in enumerate(similar_urls):
            ancres_df = df_excel[df_excel[col_url] == url_dest]
            ancres_df[col_priorite] = pd.to_numeric(ancres_df[col_priorite], errors='coerce')
            ancres_df = ancres_df.sort_values(col_priorite, ascending=False)[[col_ancre, col_priorite]]
            
            if not ancres_df.empty:
                ancres = ancres_df[col_ancre].tolist()
                ancre = ancres[j] if j < len(ancres) else ancres[0]
            else:
                ancre = url_dest

            results.append({
                'URL de départ': url_start, 
                'URL de destination': url_dest, 
                'Ancre': ancre,
                'Score de similarité': sim
            })

    df_results = pd.DataFrame(results)

    if df_results.empty:
        return None, "Aucun résultat n'a été trouvé avec les critères spécifiés.", time.time() - start_time

    return df_results, None, time.time() - start_time

def app():
    st.title("Proposition de Maillage Interne Personnalisé")

    api_key = st.text_input("Entrez votre clé API OpenAI", type="password")

    if 'df_results' not in st.session_state:
        st.session_state.df_results = None
    if 'urls_to_analyze' not in st.session_state:
        st.session_state.urls_to_analyze = ""
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'num_similar_urls' not in st.session_state:
        st.session_state.num_similar_urls = 5
    if 'include_classes' not in st.session_state:
        st.session_state.include_classes = ""
    if 'exclude_classes' not in st.session_state:
        st.session_state.exclude_classes = ""
    if 'additional_stopwords' not in st.session_state:
        st.session_state.additional_stopwords = ""

    st.session_state.urls_to_analyze = st.text_area("Collez ici les URLs à analyser (une URL par ligne)", st.session_state.urls_to_analyze)
    
    uploaded_file = st.file_uploader("Importer le fichier Excel contenant les URLs, ancres et indices de priorité", type=["xlsx"])
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file

    if st.session_state.uploaded_file is not None and st.session_state.urls_to_analyze and api_key:
        try:
            df_excel = pd.read_excel(st.session_state.uploaded_file)

            st.subheader("Sélectionnez les données GSC")
            col_url = st.selectbox("Sélectionnez la colonne contenant les URLs", df_excel.columns)
            col_ancre = st.selectbox("Sélectionnez la colonne contenant les ancres", df_excel.columns)
            col_priorite = st.selectbox("Sélectionnez la colonne contenant l'indice de priorité (nombre d'impressions)", df_excel.columns)

            if not all(col in df_excel.columns for col in [col_url, col_ancre, col_priorite]):
                st.error("Erreur: Une ou plusieurs colonnes sélectionnées n'existent pas dans le fichier Excel.")
                return

            if not pd.to_numeric(df_excel[col_priorite], errors='coerce').notna().all():
                st.error(f"Erreur: La colonne '{col_priorite}' contient des valeurs non numériques.")
                return

            urls_list = [url.strip() for url in st.session_state.urls_to_analyze.split('\n') if url.strip()]
            max_similar_urls = len(urls_list) - 1
            st.session_state.num_similar_urls = st.slider("Nombre d'URLs similaires à considérer", min_value=1, max_value=max_similar_urls, value=st.session_state.num_similar_urls)

            st.subheader("Filtrer le contenu HTML et termes")
            st.session_state.include_classes = st.text_area("Classes HTML à analyser exclusivement (une classe par ligne, optionnel)", st.session_state.include_classes)
            st.session_state.exclude_classes = st.text_area("Classes HTML à exclure de l'analyse (une classe par ligne, optionnel)", st.session_state.exclude_classes)
            st.session_state.additional_stopwords = st.text_area("Termes/stopwords supplémentaires à exclure de l'analyse (un terme par ligne, optionnel)", st.session_state.additional_stopwords)

            if st.button("Exécuter l'analyse"):
                include_classes = [cls.strip() for cls in st.session_state.include_classes.split('\n') if cls.strip()]
                exclude_classes = [cls.strip() for cls in st.session_state.exclude_classes.split('\n') if cls.strip()]
                additional_stopwords = [word.strip() for word in st.session_state.additional_stopwords.split('\n') if word.strip()]

                st.session_state.df_results, error_message, execution_time = process_data(urls_list, df_excel, col_url, col_ancre, col_priorite, include_classes, exclude_classes, additional_stopwords, api_key)

                if error_message:
                    st.error(error_message)
                elif st.session_state.df_results is None:
                    st.warning("Aucun résultat n'a été généré.")
                else:
                    st.success(f"Analyse terminée en {format_time(execution_time)}. {len(urls_list)} URLs traitées.")

            if st.session_state.df_results is not None:
                filtered_results = st.session_state.df_results.groupby('URL de départ').apply(lambda x: x.nlargest(st.session_state.num_similar_urls, 'Score de similarité')).reset_index(drop=True)
                st.dataframe(filtered_results)

                csv = filtered_results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Télécharger les résultats (CSV)",
                    data=csv,
                    file_name='maillage_interne_personnalise.csv',
                    mime='text/csv'
                )

        except Exception as e:
            st.error(f"Erreur lors du traitement : {str(e)}")

    elif not api_key:
        st.warning("Veuillez entrer votre clé API OpenAI pour continuer.")

    if st.button("Réinitialiser l'analyse"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

if __name__ == "__main__":
    app()
