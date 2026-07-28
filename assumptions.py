import streamlit as st

ASSUMPTIONS = [
    "Design is carried out on a 1.0 m strip basis.",
    "The structure has no longitudinal joints, so full load dispersal through the fill can be considered "
    "(PD6694-1 Cl. 10.2.7) — dispersal is not curtailed by a segment joint.",
    "The Transverse Dispersal formula (b·W1/L1 + a·W2/L2, PD6694-1 Figure 11) assumes the dispersed "
    "wheel width L1 is at least the 1.0 m design strip width (b). This requires H_c ≳ 0.52 m — not "
    "currently checked in the tool.",
    "Per PD6694-1 Cl. 10.2.1, dispersal through fill is only valid for H_c ≥ 0.6 m; below that, the "
    "structure should be treated as a normal bridge deck with undispersed traffic loading. This minimum "
    "is not currently enforced or flagged in the tool.",
    "The Transverse Dispersal formula assumes only two adjacent wheels' dispersion zones overlap in the "
    "critical 1 m strip. If H_c is deep enough for three or more wheels to overlap, PD6694-1 NOTE 2 to "
    "Figure 11 requires using the most heavily loaded segment/strip instead — not currently handled.",
]


def render():
    st.subheader("Assumptions")
    for a in ASSUMPTIONS:
        st.markdown(f"- {a}")
