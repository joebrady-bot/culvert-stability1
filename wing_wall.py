import streamlit as st

import ww_assumptions
import ww_geometry
import ww_inputs
import ww_stability
import ww_structural

st.page_link("home.py", label="Back to Home", icon="⬅️")
st.title("Wing Wall Design")
st.caption("BS EN 1997-1 (EC7) global stability + BS EN 1992-1-1 (EC2) structural checks, per UK NA.")

tab_inputs, tab_geometry, tab_stability, tab_structural, tab_assumptions = st.tabs(
    ["Inputs", "Geometry & Self-Weights", "Global Stability", "Structural Design", "Assumptions"]
)

with tab_inputs:
    st.session_state["ww_inputs"] = ww_inputs.render()

with tab_geometry:
    st.session_state["ww_geometry"] = ww_geometry.render(st.session_state["ww_inputs"])

with tab_stability:
    st.session_state["ww_stability"] = ww_stability.render(
        st.session_state["ww_inputs"], st.session_state["ww_geometry"]
    )

with tab_structural:
    st.session_state["ww_structural"] = ww_structural.render(
        st.session_state["ww_inputs"], st.session_state["ww_geometry"]
    )

with tab_assumptions:
    ww_assumptions.render()
