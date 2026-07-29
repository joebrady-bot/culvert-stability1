import streamlit as st

st.set_page_config(page_title="Calculation Sheets", page_icon="assets/logo.png", layout="wide")
st.logo("assets/logo.png", size="large")

home = st.Page("home.py", title="Home", icon="🏠", default=True)
culvert_stability = st.Page("culvert_stability.py", title="Culvert Stability", icon="🌉")
wing_wall = st.Page("wing_wall.py", title="Wing Wall Design", icon="🧱")
beam_analysis = st.Page("beam_analysis.py", title="Beam Analysis", icon="📏")

pg = st.navigation([home, culvert_stability, wing_wall, beam_analysis])
pg.run()
