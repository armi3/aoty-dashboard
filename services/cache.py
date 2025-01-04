import os
import json

LOCAL_STORAGE_FILE = "static/retrieved_data.json"

def load_local_cache():
    if os.path.exists(LOCAL_STORAGE_FILE):
        with open(LOCAL_STORAGE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_local_cache(cache):
    with open(LOCAL_STORAGE_FILE, "w") as f:
        json.dump(cache, f)

def reset_local_cache():
    """
    Resets the local cache to an empty dictionary.
    """
    global local_cache
    local_cache = {}
    save_local_cache(local_cache)
