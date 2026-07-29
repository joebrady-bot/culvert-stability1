import streamlit as st

import beam_assumptions
import beam_diagram
import beam_inputs
import beam_pdf_report
import rc_beam_design

st.page_link("home.py", label="Back to Home", icon="⬅️")
st.title("Beam Analysis — Bending & Shear")
st.caption("First-principles shear force and bending moment for beams on any number of simple supports.")

tab_inputs, tab_results, tab_rc_design, tab_assumptions = st.tabs(
    ["Inputs", "Results", "RC Design", "Assumptions"]
)

with tab_inputs:
    st.session_state["beam_inputs"] = beam_inputs.render()

with tab_results:
    st.session_state["beam_results"] = beam_diagram.render(st.session_state["beam_inputs"])

with tab_rc_design:
    st.session_state["rc_inputs"] = rc_beam_design.render_inputs(st.session_state.get("beam_results"))
    st.session_state["rc_results"] = rc_beam_design.render(st.session_state["rc_inputs"])
    st.divider()
    beam_pdf_report.render_button(st.session_state["beam_inputs"], st.session_state["rc_inputs"])

with tab_assumptions:
    beam_assumptions.render()
