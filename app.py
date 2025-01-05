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
            try:
                scrobble_data["utc_time"] = pd.to_datetime(scrobble_data["utc_time"], format="%d %b %Y, %H:%M", errors="coerce")
            except Exception as e:
                st.error(f"Error parsing dates: {e}")
                scrobble_data["utc_time"] = pd.NaT

            filtered_data = scrobble_data[scrobble_data["utc_time"].dt.year >= target_year]

            # Skip singles (entries without an album)
            filtered_data = filtered_data[filtered_data["album"].notna()]

            # Compress data to combine entries with the same artist and album
            compressed_data = (
                filtered_data.groupby(["artist", "album"])
                .size()
                .reset_index(name="total_scrobbles")
            )

            album_scrobble_counts = {}
            album_details = {}
            unretrievable_count = 0
            total_rows = len(compressed_data)

            # Initialize progress bar and text
            progress_bar = st.sidebar.progress(0)
            progress_text = st.sidebar.empty()

            # Process data with progress bar
            for i, row in enumerate(compressed_data.itertuples(index=False), start=1):
                cache_key = f"{row.artist}|{row.album}"

                # Fetch year and cover from cache or services
                year = local_cache.get(f"{cache_key}|year") or get_album_year_cached(local_cache, local_cache, None, row.artist, row.album)

                if year and year.isdigit() and int(year) == target_year:
                    local_cache[f"{cache_key}|year"] = year

                    # Only fetch cover if year is valid
                    cover_url = local_cache.get(f"{cache_key}|cover") or get_album_cover_cached(local_cache, local_cache, None, row.artist, row.album)

                    if cover_url:
                        local_cache[f"{cache_key}|cover"] = cover_url

                        album_key = (row.album, row.artist)
                        album_scrobble_counts[album_key] = row.total_scrobbles
                        album_details[album_key] = {"cover": cover_url, "year": year}
                else:
                    unretrievable_count += 1

                # Update progress bar and text
                progress_bar.progress(i / total_rows)
                progress_text.markdown(f"Processing: {i}/{total_rows} ({(i / total_rows) * 100:.2f}%)")

            # Save the updated local cache
            save_local_cache(local_cache)

            # Prepare the initial AOTY DataFrame
            aoty_df = pd.DataFrame([
                {
                    "Album": album,
                    "Artist": artist,
                    "Release Year": details["year"],
                    "Total Scrobbles": album_scrobble_counts[(album, artist)]
                }
                for (album, artist), details in album_details.items()
            ])

            # Save the initial AOTY list to a CSV file
            initial_csv_path = f"aoty_list_{target_year}.csv"
            aoty_df.to_csv(initial_csv_path, index=False)
            st.sidebar.download_button("Download Initial AOTY List", initial_csv_path)

            # Display the sortable cards
            st.header("Albums")

            sortable_items = [
                f"{row['Album']}|{row['Artist']}|{row['Total Scrobbles']}"
                for _, row in aoty_df.iterrows()
            ]

            sorted_items = sort_items(
                sortable_items,
                direction="vertical",
                key="sortable_albums",
            )

            # Create final AOTY list after reordering
            if st.button("Generate Final AOTY List"):
                final_aoty_data = []
                for item in sorted_items:
                    try:
                        album, artist, scrobbles = item.split('|')
                        final_aoty_data.append({
                            "Album": album,
                            "Artist": artist,
                            "Release Year": aoty_df.loc[(aoty_df["Album"] == album) & (aoty_df["Artist"] == artist), "Release Year"].values[0],
                            "Total Scrobbles": int(scrobbles)
                        })
                    except ValueError:
                        st.warning(f"Skipping invalid item: {item}")

                final_aoty_df = pd.DataFrame(final_aoty_data)
                final_csv_path = f"final_aoty_list_{target_year}.csv"
                final_aoty_df.to_csv(final_csv_path, index=False)
                st.sidebar.download_button("Download Final AOTY List", final_csv_path)

            # Display the reordered list with cards
            for item in sorted_items:
                try:
                    album, artist, scrobbles = item.split('|')
                except ValueError:
                    st.warning(f"Skipping invalid item: {item}")
                    continue

                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(album_details[(album, artist)]["cover"])
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
