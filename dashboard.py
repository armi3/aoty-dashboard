import streamlit as st
import pandas as pd
from streamlit_sortables import sort_items

# Set page configuration to enable wide mode
st.set_page_config(
    page_title="Favorite Albums Selector",
    layout="wide",  # Enables wide mode
    initial_sidebar_state="expanded",  # Sidebar is expanded by default
)

# Sidebar for controls
with st.sidebar:
    st.title("Controls")
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
    st.number_input(
        "Enter the target year:",
        min_value=1900,
        max_value=2100,
        value=2024,
        key="target_year",
    )
    process_data = st.button("Process Data")

# Ensure session state variables for processing
if "sorted_items" not in st.session_state:
    st.session_state.sorted_items = []
if "data_processed" not in st.session_state:
    st.session_state.data_processed = False

# Process data when triggered
if uploaded_file and process_data:
    st.session_state.sorted_items = []
    st.session_state.data_processed = True

    # Load and process the data
    df = pd.read_csv(uploaded_file)
    df["utc_time"] = pd.to_datetime(df["utc_time"], format="%d %b %Y, %H:%M")
    df = df[df["utc_time"].dt.year >= st.session_state.target_year]
    df = df.dropna(subset=["album", "artist"])
    summary = (
        df.groupby(["album", "album_mbid", "artist", "artist_mbid"], as_index=False)
        .size()
        .rename(columns={"size": "scrobbles"})
    )

    # Create album cards
    st.session_state.sorted_items = [
        {
            "text": f"{row['album']} by {row['artist']} ({row['scrobbles']} scrobbles)",
            "album": row["album"],
        }
        for _, row in summary.iterrows()
    ]

# Main page layout: Two equal columns
if st.session_state.data_processed and st.session_state.sorted_items:
    col1, col2 = st.columns([1, 1])  # Equal-width columns

    # Column 1: Sortable list
    with col1:
        st.header("Sortable Albums")
        items = [item["text"] for item in st.session_state.sorted_items]
        sorted_items = sort_items(items, direction="vertical", key="sortable_list")

        # Update session state with the new order
        st.session_state.sorted_items = [
            item
            for text in sorted_items
            for item in st.session_state.sorted_items
            if item["text"] == text
        ]

    # Column 2: Render sorted items with Discard buttons
    with col2:
        st.header("Sorted Albums with Actions")
        updated_items = []
        for idx, item in enumerate(st.session_state.sorted_items):
            col_left, col_right = st.columns([4, 1])
            with col_left:
                st.markdown(f"**{item['text']}**")
            with col_right:
                if st.button("Discard", key=f"discard_{idx}"):
                    # Remove the album from the list
                    continue  # Skip adding this item to updated_items
            updated_items.append(item)
        st.session_state.sorted_items = updated_items

        # Save button
        if st.button("Save Final List"):
            # Extract sorted and remaining album names
            final_album_names = [item["album"] for item in st.session_state.sorted_items]
            final_summary = summary[summary["album"].isin(final_album_names)].copy()

            # Rearrange the DataFrame to match the sorted order
            final_summary["sort_order"] = final_summary["album"].apply(
                lambda x: final_album_names.index(x)
            )
            final_summary = final_summary.sort_values("sort_order").drop(
                columns="sort_order"
            )

            # Prepare the CSV
            csv = final_summary.to_csv(index=False)
            st.download_button("Download Final List", csv, "final_album_list.csv", "text/csv")
else:
    st.info("Upload a file and click 'Process Data' in the sidebar to begin.")
