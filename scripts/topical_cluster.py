import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AffinityPropagation
import matplotlib.pyplot as plt
import seaborn as sns

def perform_clustering(keywords):
    # Create a Tf-idf Vector with Keywords
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(keywords)

    # Perform Affinity Propagation clustering
    af = AffinityPropagation().fit(X)
    cluster_centers_indices = af.cluster_centers_indices_
    labels = af.labels_

    # Get the number of clusters found
    n_clusters = len(cluster_centers_indices)

    # Create a DataFrame to store the cluster information
    cluster_data = {
        'Topic Clusters': labels, 
        'Keywords': keywords
    }

    # Convert cluster_data to a Pandas DataFrame
    cluster_df = pd.DataFrame(cluster_data)
    
    return cluster_df, n_clusters

def main():
    st.title("Keyword Topic Clustering for SEO")
    
    st.write("""
    This tool groups keywords into topic clusters using TF-IDF and Affinity Propagation clustering.
    Enter your keywords (one per line) in the text area below.
    """)

    # Text area for user input
    keywords_input = st.text_area("Enter your keywords (one per line):", height=200)

    if st.button("Perform Clustering"):
        if keywords_input:
            keywords = keywords_input.split('\n')
            keywords = [keyword.strip() for keyword in keywords if keyword.strip()]

            with st.spinner("Performing clustering..."):
                cluster_df, n_clusters = perform_clustering(keywords)

            st.success(f"Clustering complete! Found {n_clusters} clusters.")

            # Display results
            st.subheader("Clustered Keywords")
            st.dataframe(cluster_df)

            # Download button for CSV
            csv = cluster_df.to_csv(index=False)
            st.download_button(
                label="Download clustered keywords as CSV",
                data=csv,
                file_name="clustered_keywords.csv",
                mime="text/csv",
            )

            # Visualize clusters
            st.subheader("Cluster Distribution")
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.countplot(x='Topic Clusters', data=cluster_df, ax=ax)
            plt.title("Distribution of Keywords Across Clusters")
            plt.xlabel("Cluster")
            plt.ylabel("Number of Keywords")
            st.pyplot(fig)

        else:
            st.warning("Please enter some keywords before clustering.")
def app():
    st.title("Topical Cluster")

if __name__ == "__main__":
    main()
