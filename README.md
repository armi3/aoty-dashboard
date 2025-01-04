# aoty-dashboard
💿 Streamlit dashboard for making AOTY lists based on scrobbles.

Export CSV from: https://lastfm.ghan.nl/export/

```
python3 -m pip install --upgrade pip

python3 -m venv env && source env/bin/activate

pip3 install --upgrade pip
pip3 install streamlit pandas musicbrainzngs
streamlit run app.py

deactivate
```