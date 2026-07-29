import streamlit as st

import assumptions
import box_culvert
import lm1_calculations
import lm3_calculations
import table_b4
import table_b5
import user_inputs

st.set_page_config(page_title="Culvert Stability", layout="wide")
st.title("Culvert Stability")

tab_inputs, tab_global_calcs, tab_lm1_calcs, tab_lm3_calcs, tab_table_b4, tab_table_b5, tab_assumptions = st.tabs(
    ["Inputs", "Global Calculations", "LM1 Calculations", "LM3 Calculations", "Table B.4", "Table B.5", "Assumptions"]
)

with tab_inputs:
    st.session_state["inputs"] = user_inputs.render()

with tab_global_calcs:
    st.session_state["box_culvert"] = box_culvert.render(st.session_state["inputs"])

with tab_lm1_calcs:
    st.session_state["lm1"] = lm1_calculations.render(st.session_state["inputs"], st.session_state["box_culvert"])

with tab_lm3_calcs:
    st.session_state["lm3"] = lm3_calculations.render(st.session_state["inputs"], st.session_state["box_culvert"])

with tab_table_b4:
    st.session_state["table_b4"] = table_b4.render(
        st.session_state["inputs"],
        st.session_state["box_culvert"],
        st.session_state["lm1"],
        st.session_state["lm3"],
    )

with tab_table_b5:
    st.session_state["table_b5"] = table_b5.render(
        st.session_state["inputs"],
        st.session_state["box_culvert"],
        st.session_state["lm1"],
        st.session_state["lm3"],
    )

with tab_assumptions:
    assumptions.render()
