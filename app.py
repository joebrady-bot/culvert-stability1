import streamlit as st

import assumptions
import box_culvert
import user_inputs

st.set_page_config(page_title="Culvert Stability", layout="wide")
st.title("Culvert Stability")

tab_inputs, tab_calcs, tab_assumptions = st.tabs(["Inputs", "Calculations", "Assumptions"])

with tab_inputs:
    st.session_state["inputs"] = user_inputs.render()

with tab_calcs:
    st.session_state["box_culvert"] = box_culvert.render(st.session_state["inputs"])

with tab_assumptions:
    assumptions.render()
