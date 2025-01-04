import streamlit as st
import pandas as pd

# Set the title of the Streamlit dashboard
st.title("AOTY List Creator from Last.fm Scrobble Data")

# File uploader for the CSV
uploaded_file = st.file_uploader("Upload your scrobble data CSV file:", type="csv")

# Check if a file is uploaded
if uploaded_file is not None:
    try:
        # Extract the username from the uploaded file name
        username = uploaded_file.name.replace(".csv", "")

        # Read the uploaded CSV file without headers
        scrobble_data = pd.read_csv(uploaded_file, header=None)

        # Verify the shape of the CSV and assign column names
        if scrobble_data.shape[1] == 4:
            scrobble_data.columns = ["Artist", "Album", "Song", "Scrobble Date"]

            # Display the username and the first few rows of the data
            st.subheader(f"Scrobble data for user: {username}")
            st.dataframe(scrobble_data.head())
        else:
            st.error("The uploaded file does not have the expected format (4 columns: Artist, Album, Song, Scrobble Date).")

    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
else:
    st.info("Please upload a CSV file to load the scrobble data.")
