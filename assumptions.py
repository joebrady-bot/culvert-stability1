import streamlit as st

ASSUMPTIONS = [
    "Design is carried out on a 1.0 m strip basis.",
    "The structure has no longitudinal joints, so full load dispersal through the fill can be considered "
    "(PD6694-1 Cl. 10.2.7) — dispersal is not curtailed by a segment joint.",
]


def render():
    st.subheader("Assumptions")
    for a in ASSUMPTIONS:
        st.markdown(f"- {a}")
