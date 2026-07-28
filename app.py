import streamlit as st

import user_inputs

st.set_page_config(page_title="Culvert Stability", layout="wide")
st.title("Culvert Stability")

(tab_inputs,) = st.tabs(["Inputs"])

with tab_inputs:
    st.session_state["inputs"] = user_inputs.render()
