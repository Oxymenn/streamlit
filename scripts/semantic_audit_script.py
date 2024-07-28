import streamlit as st
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Sample data
data = {
    'URL': ['http://example.com/1', 'http://example.com/2', 'http://example.com/3'],
    'Embedding': [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9]
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Streamlit app
st.title('URL Similarity Calculator')

# Display the DataFrame
st.subheader('Data')
st.write(df)

# Select URLs
selected_urls = st.multiselect('Select URLs', df['URL'].tolist())

# Filter DataFrame based on selected URLs
filtered_df = df[df['URL'].isin(selected_urls)]

# Calculate similarity
if len(filtered_df) > 1:
    embeddings = np.array(filtered_df['Embedding'].tolist())
    similarity_matrix = cosine_similarity(embeddings)

    # Display similarity matrix
    st.subheader('Similarity Matrix')
    st.write(pd.DataFrame(similarity_matrix, index=selected_urls, columns=selected_urls))
else:
    st.warning('Please select at least two URLs to calculate similarity.')
