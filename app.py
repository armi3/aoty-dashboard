import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from services.cache import load_local_cache, save_local_cache, reset_local_cache
from services.musicbrainz import get_album_year_cached, get_album_cover_cached

# Set the title of the Streamlit dashboard
st.title("AOTY List Creator from Last.fm Scrobble Data")

# Load cache and check for serialization issues and reset the cache if necessary
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

# Sidebar progress placeholders
progress_bar = st.sidebar.progress(0)
progress_text = st.sidebar.empty()
unretrievable_text = st.sidebar.empty()

# Main Page
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

            total_rows = len(filtered_data)
            unretrievable_count = 0
            start_time = time.time()

            # Dictionaries to store results
            album_scrobble_counts = {}
            album_details = {}

            for i, row in filtered_data.iterrows():
                # Fetch year and cover URL
                cache_key = f"{row['artist']}|{row['album']}"
                year = local_cache.get(f"{cache_key}|year")
                cover_url = local_cache.get(f"{cache_key}|cover")

                if not year or not cover_url:
                    # Fetch year if not cached
                    year = get_album_year_cached(local_cache, local_cache, row["album_mbid"], row["artist"], row["album"])
                    try:
                        if year is None or int(year) != target_year:
                            unretrievable_count += 1
                            continue
                    except ValueError:
                        unretrievable_count += 1
                        continue

                    # Fetch cover if not cached
                    cover_url = get_album_cover_cached(local_cache, local_cache, row["album_mbid"], row["artist"], row["album"])
                    if not cover_url:
                        unretrievable_count += 1
                        continue

                    # Update cache
                    local_cache[f"{cache_key}|year"] = year
                    local_cache[f"{cache_key}|cover"] = cover_url

                # Update scrobble counts and details
                album_key = (row["album"], row["artist"])
                album_scrobble_counts[album_key] = album_scrobble_counts.get(album_key, 0) + 1
                album_details[album_key] = cover_url

                # Update progress bar and messages
                progress_bar.progress((i + 1) / total_rows)
                elapsed_time = time.time() - start_time
                estimated_total_time = (elapsed_time / (i + 1)) * total_rows
                estimated_remaining_time = estimated_total_time - elapsed_time
                progress_text.markdown(f"**{i + 1:,} from {total_rows:,} scrobbles analyzed**")
                unretrievable_text.markdown(f"**Unretrievable: {unretrievable_count:,} ({(unretrievable_count / total_rows) * 100:.2f}%)**")

            # Save the updated local cache
            save_local_cache(local_cache)

            # Display unique album cards after analysis
            st.header("Albums")
            for (album, artist), cover_url in album_details.items():
                if album and artist and cover_url:  # Ensure no ghost cards
                    scrobble_count = album_scrobble_counts[(album, artist)]
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.image(cover_url)
                    with cols[1]:
                        st.markdown(f"### {album}")
                        st.markdown(f"**Artist**: {artist}")
                        st.markdown(f"**Scrobbles**: {scrobble_count:,}")

        else:
            st.error(f"The uploaded file is missing required columns: {required_columns}")

    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
else:
    st.info("Upload a file in the sidebar to begin.")
