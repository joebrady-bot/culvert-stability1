import streamlit as st

import beam_assumptions
import beam_diagram
import beam_inputs

st.page_link("home.py", label="Back to Home", icon="⬅️")
st.title("Beam Analysis — Bending & Shear")
st.caption("First-principles shear force and bending moment for beams on any number of simple supports.")

tab_inputs, tab_results, tab_assumptions = st.tabs(["Inputs", "Results", "Assumptions"])

with tab_inputs:
    st.session_state["beam_inputs"] = beam_inputs.render()

with tab_results:
    st.session_state["beam_results"] = beam_diagram.render(st.session_state["beam_inputs"])

with tab_assumptions:
    beam_assumptions.render()
