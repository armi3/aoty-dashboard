import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from services.cache import load_local_cache, save_local_cache, reset_local_cache
from services.musicbrainz import get_album_year_cached, get_album_cover_cached
from stqdm import stqdm
from streamlit_sortables import sort_items

# Set the title of the Streamlit dashboard
st.title("AOTY list from scrobbles")

# Load cache, check for serialization issues, and reset the cache if necessary
try:
    local_cache = load_local_cache()
    json.dumps(local_cache)  # Ensure local_cache is serializable
except Exception as e:
    reset_local_cache()
    st.warning("Local cache was corrupted and has been reset.")

# File uploader for the CSV
uploaded_file = st.sidebar.file_uploader("Upload your scrobble data CSV file:", type="csv")

# Ask the user for the target year
target_year = st.sidebar.number_input(
    "Enter the year for your AOTY list:", min_value=1900, max_value=2100, step=1, value=datetime.now().year
)

# Main page
if uploaded_file is not None:
    try:
        # Extract the username from the uploaded file name
        username = uploaded_file.name.split("recenttracks-")[1].split("-")[0]

        # Read the uploaded CSV file with headers
        scrobble_data = pd.read_csv(uploaded_file)

        # Verify the required columns are present
        required_columns = ["uts", "utc_time", "artist", "artist_mbid", "album", "album_mbid", "track", "track_mbid"]
        if all(column in scrobble_data.columns for column in required_columns):
            # Filter entries based on the target year using utc_time
            scrobble_data["utc_time"] = pd.to_datetime(scrobble_data["utc_time"], format="%d %b %Y, %H:%M")
            filtered_data = scrobble_data[scrobble_data["utc_time"].dt.year >= target_year]

            # Skip singles (entries without an album)
            filtered_data = filtered_data[filtered_data["album"].notna()]

            album_scrobble_counts = {}
            album_details = {}
            unretrievable_count = 0
            total_rows = len(filtered_data)

            # Process data with progress bar
            for row in stqdm(filtered_data.itertuples(index=False), total=total_rows, desc="Processing scrobbles"):
                cache_key = f"{row.artist}|{row.album}"

                # Fetch year and cover from cache or services
                year = local_cache.get(f"{cache_key}|year") or get_album_year_cached(local_cache, local_cache, row.album_mbid, row.artist, row.album)

                # Validate year and cover_url
                if year and int(year) == target_year:
                    local_cache[f"{cache_key}|year"] = year

                    # Only fetch cover if it's target year
                    cover_url = local_cache.get(f"{cache_key}|cover") or get_album_cover_cached(local_cache, local_cache, row.album_mbid, row.artist, row.album)

                    if cover_url:
                        local_cache[f"{cache_key}|cover"] = cover_url

                    album_key = (row.album, row.artist)
                    album_scrobble_counts[album_key] = album_scrobble_counts.get(album_key, 0) + 1
                    album_details[album_key] = cover_url
                else:
                    unretrievable_count += 1

            # Save the updated local cache
            save_local_cache(local_cache)

            # Display unique album cards after analysis
            st.header("Albums")

            # Prepare data for sortable list
            sortable_items = [
                f"{album}|{artist}|{album_scrobble_counts[(album, artist)]}"  # Use pipe delimiter for safer splitting
                for (album, artist) in album_details.keys()
                if album and artist
            ]

            sorted_items = sort_items(
                sortable_items,
                direction="vertical",
                key="sortable_albums",
            )

            # Parse and display sorted items
            for item in sorted_items:
                album, artist, scrobbles = item.split('|')  # Split by the pipe delimiter
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(album_details[(album, artist)])
                with cols[1]:
                    st.markdown(f"### {album}")
                    st.markdown(f"**Artist**: {artist}")
                    st.markdown(f"**Scrobbles**: {scrobbles}")

        else:
            st.error(f"The uploaded file is missing required columns: {required_columns}")

    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
else:
    st.info("Upload a file in the sidebar to begin.")
