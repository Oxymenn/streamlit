import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.formatting.rule import Rule
from openpyxl.styles.differential import DifferentialStyle

def analyze_url(url, keywords):
    scraper = cloudscraper.create_scraper()
    html = scraper.get(url, headers={"User-agent": "Mozilla/5.0"})
    soup = BeautifulSoup(html.text, 'html.parser')

    metatitle = soup.find('title').get_text() if soup.find('title') else ""
    metadescription = soup.find('meta', attrs={'name':'description'})
    metadescription = metadescription["content"] if metadescription else ""
    h1 = [a.get_text() for a in soup.find_all('h1')]
    h2 = [a.get_text() for a in soup.find_all('h2')]
    paragraph = [a.get_text() for a in soup.find_all('p')]

    results = []
    for keyword in keywords:
        metatitle_occurrence = all(term.lower() in metatitle.lower() for term in keyword.split())
        metadescription_occurrence = all(term.lower() in metadescription.lower() for term in keyword.split())
        h1_occurrence = any(all(term.lower() in h.lower() for term in keyword.split()) for h in h1)
        h2_occurrence = any(all(term.lower() in h.lower() for term in keyword.split()) for h in h2)
        paragraph_occurrence = any(all(term.lower() in p.lower() for term in keyword.split()) for p in paragraph)

        results.append([
            keyword,
            str(metatitle_occurrence),
            str(metadescription_occurrence),
            str(h1_occurrence),
            str(h2_occurrence),
            str(paragraph_occurrence)
        ])

    return results

def create_excel(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "SEO Analysis"

    headers = ["URL", "Keyword", "Ranking", "Searches", "Metatitle", "Metadescription", "H1", "H2", "Paragraph"]
    for col, header in enumerate(headers, start=1):
        ws.cell(row=1, column=col, value=header)

    for row, item in enumerate(data, start=2):
        for col, value in enumerate(item, start=1):
            ws.cell(row=row, column=col, value=value)

    red_text = Font(color="9C0006")
    red_fill = PatternFill(bgColor="FFC7CE")
    green_text = Font(color="FFFFFF")
    green_fill = PatternFill(bgColor="009c48")

    dxf = DifferentialStyle(font=red_text, fill=red_fill)
    dxf2 = DifferentialStyle(font=green_text, fill=green_fill)

    rule = Rule(type="containsText", operator="containsText", text="False", dxf=dxf)
    rule2 = Rule(type="containsText", operator="containsText", text="True", dxf=dxf2)

    ws.conditional_formatting.add(f'A1:I{len(data)+1}', rule)
    ws.conditional_formatting.add(f'A1:I{len(data)+1}', rule2)

    return wb

def app():
    st.title("Analyse SEO On-Site")

    uploaded_file = st.file_uploader("Importer votre fichier Excel (Ahrefs ou SEMrush)", type=['xlsx'])
    url = st.text_input("Entrez l'URL à analyser")

    if uploaded_file and url:
        df = pd.read_excel(uploaded_file)
        
        # Filtrer les mots-clés dans le top 15
        df_filtered = df[df['Position'] < 15]

        keywords = df_filtered['Keyword'].tolist()
        rankings = df_filtered['Position'].tolist()
        searches = df_filtered['Volume'].tolist()

        if st.button("Analyser"):
            with st.spinner("Analyse en cours..."):
                results = analyze_url(url, keywords)
                
                data = [[url] + list(df_filtered.iloc[i]) + result for i, result in enumerate(results)]
                
                wb = create_excel(data)
                
                # Sauvegarder le fichier Excel en mémoire
                excel_data = io.BytesIO()
                wb.save(excel_data)
                excel_data.seek(0)

                # Bouton de téléchargement
                st.download_button(
                    label="Télécharger l'analyse Excel",
                    data=excel_data,
                    file_name="seo_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # Afficher un aperçu des résultats
                st.subheader("Aperçu des résultats")
                preview_df = pd.DataFrame(data, columns=["URL", "Keyword", "Ranking", "Searches", "Metatitle", "Metadescription", "H1", "H2", "Paragraph"])
                st.dataframe(preview_df)

    else:
        st.info("Veuillez importer un fichier Excel et entrer une URL pour commencer l'analyse.")

if __name__ == "__main__":
    app()
