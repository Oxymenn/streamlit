import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import Counter
from treelib import Tree
import pandas as pd
import re

def app():
    # Configuration for the scraping process
    st.title('Google SERP Analysis')
    keyword = st.text_input('Enter Keyword for SERP Analysis', 'SERP analysis')
    language = st.selectbox('Select Language', ['en', 'es', 'fr', 'de', 'it', 'pt'])
    country = st.selectbox('Select Country', ['us', 'uk', 'es', 'fr', 'de', 'it'])
    search_entities = st.checkbox('Search for Entities?', value=True)
    
    # Prepare the Google search URL
    url_initial = f"https://www.google.com/search?hl={language}&gl={country}&q={keyword}&oq={keyword}"

    # Stopwords directly embedded in the code
    stopwords = {
        'en': set("i me my myself we our ours ourselves you your yours yourself yourselves he him his himself she her hers herself it its itself they them their theirs themselves what which who whom this that these those am is are was were be been being have has had having do does did doing a an the and but if or because as until while of at by for with about against between into through during before after above below to from up down in out on off over under again further then once here there when where why how all any both each few more most other some such no nor not only own same so than too very can will just don should now".split()),
        'es': set("de la que el en y a los del se las por un para con no una su al lo como más pero sus le ya o este sí porque esta entre cuando muy sin sobre también me hasta hay donde quien desde todo nos durante todos uno les ni contra otros ese eso había ante ellos e esto mí antes algunos qué unos yo otro otras otra él tanto esa estos mucho quienes nada muchos cual poco ella estar estas algunas algo nosotros mi mis tú te ti tu tus ellas nosotras vosotres vosotras os míos mía míos mías tuyos tuyo tuya tuyas suyo suyos suya suyas nuestros nuestras vuestro vuestra vuestros vuestras esos esas estoy estás está estamos estáis están mía tuya suya nuestros vuestras".split()),
        'fr': set("au aux avec ce cetteces dans de des du elle en et eux il je la le leur lui ma mais me même mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous c d j l à m n s t y été étée étées étés étant étante étants étant de le la les en l était étais était étions étiez étaient suis est es sommes sont êtes sont avais avait avions aviez avaient aurions aurait auriez auraient avons aie aies ait ayons ayez aient fus fut furent soit soyons soyez soient fusse fusses fût fussions fussiez fussent ayant eu étant étant eu une une".split()),
        'de': set("aber alle allem allen alles als also am an ander andere anderem anderen anderer anderes anderm andern anderr anderrs auch auf aus bei bin bis bist da damit dann der den des dem die das dass dein deine deinem deinen deiner deines derer deses deines da da da sie den die das die sie des dem den die sie sie dieser demselben diese dieselben dieses dieselbe sie sie das darüber danach unter darüber dabei danach ebenfalls einmal erstmals unverzüglich so so darauf dazu dabei darin darüber dabei das da deshalb dabei darüber dazu die der die die".split()),
        'it': set("di a da in con su per tra fra il lo la gli le un uno una unostante nel nelle sù tra trent' ontro sono ho ha anche può".split()),
        'pt': set("a o e do da em um para é com não uma os no se na por mais as dos como mas foi ao ser de tem já está estávamos mais ou menos eras sou tua seu sua sua sua suas estáŃăo estivemos estariam muito coisa coisa nós".split())
    }

    def clean_text(text, lang):
        text = text.lower()
        text = re.sub(r'\b\w{1,2}\b', '', text)  # remove short words
        text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
        text = " ".join([word for word in text.split() if word not in stopwords[lang]])
        return text

    def parse_serp(url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            tree = Tree()

            # Extract "People Also Ask" questions
            paa_elems = soup.select(".related-question-pair")
            paa_questions = []
            if paa_elems:
                tree.create_node("People Also Ask", "PAA")
                for elem in paa_elems:
                    question = elem.get_text().strip().lower()
                    if question and question not in paa_questions:
                        paa_questions.append((question, url))
                        tree.create_node(question, question, parent='PAA')

            # Extract Related Searches
            related_elems = soup.select(".k8XOCe a")
            related_searches = []
            if related_elems:
                tree.create_node("Related Searches", "Related")
                for elem in related_elems:
                    related_search = elem.get_text().strip().lower()
                    if related_search and related_search not in related_searches:
                        related_searches.append(related_search)
                        tree.create_node(related_search, related_search, parent='Related')

            # Extract Google Suggestions
            suggestions = []
            suggestion_elems = soup.select(".s75CSd")
            if suggestion_elems:
                tree.create_node("Google Suggestions", "Suggest")
                for elem in suggestion_elems:
                    suggestion = elem.get_text().strip().lower()
                    if suggestion and suggestion not in suggestions:
                        suggestions.append(suggestion)
                        tree.create_node(suggestion, suggestion, parent='Suggest')

            if len(tree) > 1:
                st.write(f"Results for Keyword: {keyword}")
                tree.show(key=False)

            return related_searches, paa_questions, suggestions

        except Exception as e:
            st.write(f"Exception: {e}")
            return [], [], []

    def scrape_serp_results():
        related_searches, paa_questions, google_suggest = parse_serp(url_initial)
        return related_searches, paa_questions, google_suggest

    related_searches, paa_questions, google_suggest = scrape_serp_results()

    # Displaying Gathered Data
    st.write("**Related Searches**")
    st.table(related_searches)

    st.write("**People Also Ask**")
    st.table(paa_questions)

    st.write("**Google Suggestions**")
    st.table(google_suggest)

    # Analysis on extracted headings, titles, meta descriptions
    def analyze_textual_data(data, lang):
        text = " ".join(data).lower()
        text_cleaned = clean_text(text, lang)

        word_freq = Counter(text_cleaned.split()).most_common()
        df = pd.DataFrame(word_freq, columns=['Term', 'Frequency'])

        return df

    # Combine all data into a single text block for analysis
    combined_text = related_searches + [q[0] for q in paa_questions] + google_suggest
    if len(combined_text) > 0:
        df_terms = analyze_textual_data(combined_text, language)
        st.write("**Frequent Terms on SERP**")
        st.dataframe(df_terms)

        # Option to download the data as CSV
        csv = df_terms.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name=f'serp_frequent_terms_{keyword}.csv', mime='text/csv')

    # Entity analysis using Wikipedia API
    if search_entities:
        st.write("**Entity Analysis** (Approx 3-5 Minutes)")
        import wikipedia
        wikipedia.set_lang(language)

        def find_entities(text):
            try:
                entities = wikipedia.search(text)
                if entities:
                    st.write(f"Entities Found: {entities[:3]}")
            except Exception as e:
                st.write(f"Error fetching entities for: {text}. Exception: {e}")

        entity_results = []
        for text in related_searches + google_suggest + paa_questions:
            text_content = text[0] if isinstance(text, tuple) else text
            find_entities(text_content)
        
        st.write("**Entities Identified**")
        st.table(entity_results)

if __name__ == "__main__":
    app()
