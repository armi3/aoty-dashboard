# aoty-dashboard
💿 Streamlit dashboard for making AOTY lists based on Last.fm scrobbles.
🚧 WIP! The challenge is to start over until I get it done in only a couple of sittings.

Export scrobbles CSV from: https://lastfm.ghan.nl/export/

```
python3 -m pip install --upgrade pip

python3 -m venv env && source env/bin/activate

pip3 install --upgrade pip
pip3 install streamlit pandas musicbrainzngs streamlit_sortables
streamlit run app.py

deactivate
```