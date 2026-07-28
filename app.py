import streamlit as st

import assumptions
import box_culvert
import lm1_calculations
import user_inputs

st.set_page_config(page_title="Culvert Stability", layout="wide")
st.title("Culvert Stability")

tab_inputs, tab_global_calcs, tab_lm1_calcs, tab_assumptions = st.tabs(
    ["Inputs", "Global Calculations", "LM1 Calculations", "Assumptions"]
)

with tab_inputs:
    st.session_state["inputs"] = user_inputs.render()

with tab_global_calcs:
    st.session_state["box_culvert"] = box_culvert.render(st.session_state["inputs"])

with tab_lm1_calcs:
    st.session_state["lm1"] = lm1_calculations.render(st.session_state["inputs"], st.session_state["box_culvert"])

with tab_assumptions:
    assumptions.render()
