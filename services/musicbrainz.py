import musicbrainzngs
import requests
import os
import pandas as pd  # Import pandas for `pd.notna`

COVER_IMAGE_DIR = "static/album_covers"
os.makedirs(COVER_IMAGE_DIR, exist_ok=True)  # Ensure the directory exists

musicbrainzngs.set_useragent("AOTY Dashboard", "1.0", "your_email@example.com")

def get_album_year_cached(cache, local_cache, album_mbid, artist, album):
    cache_key = f"{artist.lower()}|{album.lower()}"
    if cache_key in cache or cache_key in local_cache:
        return cache.get(cache_key, local_cache.get(cache_key))

    try:
        if album_mbid:
            result = musicbrainzngs.get_release_by_id(album_mbid)
            if "release" in result and "date" in result["release"]:
                year = result["release"]["date"][:4]
                cache[cache_key] = year
                local_cache[cache_key] = year
                return year
    except Exception:
        pass
    return None

def get_album_cover_cached(cache, local_cache, album_mbid, artist, album):
    # Create a unique file name for the cover image
    sanitized_artist = artist.lower().replace(" ", "_").replace("/", "_")
    sanitized_album = album.lower().replace(" ", "_").replace("/", "_")
    local_image_path = os.path.join(COVER_IMAGE_DIR, f"{sanitized_artist}_{sanitized_album}.jpg")

    # Check if the image already exists locally
    if os.path.exists(local_image_path):
        return local_image_path

    # Check the cache
    cache_key = f"{sanitized_artist}|{sanitized_album}|cover"
    if cache_key in cache or cache_key in local_cache:
        return cache.get(cache_key, local_cache.get(cache_key))

    try:
        # Fetch the cover art from the Cover Art Archive
        if pd.notna(album_mbid):
            cover_url = f"https://coverartarchive.org/release/{album_mbid}/front"
            response = requests.get(cover_url, stream=True)

            if response.status_code == 200:
                # Save the image locally
                with open(local_image_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

                # Cache the local path
                cache[cache_key] = local_image_path
                local_cache[cache_key] = local_image_path
                return local_image_path

    except Exception as e:
        print(f"Error fetching cover art for {artist} - {album}: {e}")

    return None
