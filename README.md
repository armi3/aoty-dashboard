# aoty-dashboard
💿 Streamlit dashboard for making AOTY lists based on scrobbles.

Export CSV from: https://lastfm.ghan.nl/export/

```
python3 -m pip install --upgrade pip

python3 -m venv env && source env/bin/activate

pip3 install --upgrade pip
pip3 install streamlit pandas musicbrainzngs streamlit_sortables
streamlit run app.py

deactivate
```


creo que debería:
* raw scrobble data
* initial aoty list
* custom aoty list

- filter out older than target year
- filter out w/o album
- if album not cached:
  - fetch album release date
  - if release date older than target year, discard
  - if single, discard
- if album cached:
  - add scrobble count

- order by scrobble count > save

- customize > save



see: https://stridegpt.streamlit.app