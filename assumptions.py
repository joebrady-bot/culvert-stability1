import streamlit as st

ASSUMPTIONS = [
    "Design is carried out on a 1.0 m strip basis.",
]


def render():
    st.subheader("Assumptions")
    for a in ASSUMPTIONS:
        st.markdown(f"- {a}")
