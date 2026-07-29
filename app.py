import streamlit as st

st.set_page_config(page_title="Calculation Sheets", layout="wide")

home = st.Page("home.py", title="Home", icon="🏠", default=True)
culvert_stability = st.Page("culvert_stability.py", title="Culvert Stability", icon="🌉")

pg = st.navigation([home, culvert_stability])
pg.run()
