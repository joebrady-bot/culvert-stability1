import streamlit as st

ASSUMPTIONS = [
    "All supports are simple (pin/roller) — vertical reaction only, no moment restraint. Fixed "
    "or cantilever supports are not currently modelled.",
    "The beam spans exactly between the first and last support — no overhangs beyond the outer "
    "supports.",
    "A single, uniform flexural rigidity (EI) is assumed along the whole beam. Reactions, shear "
    "and moment do not depend on the actual EI value under this assumption — only deflection "
    "would, and deflection is not calculated by this tool.",
    "Loads are point loads and/or UDLs (uniform over any part of the span) only — applied point "
    "moments (couples) are not currently supported.",
    "For 2 supports (a single span), reactions and internal forces are found directly from "
    "statics — the beam is statically determinate. For 3 or more supports, the beam is "
    "statically indeterminate and the redundant support moments are found using the three-moment "
    "theorem (Clapeyron's equation), with the area/centroid terms it needs computed by "
    "numerically integrating each span's own simple-beam moment diagram — this generalises the "
    "theorem to any combination of point loads and UDLs, rather than being limited to the "
    "specific load patterns usually tabulated for it.",
    "Sagging is taken as positive throughout, matching the convention used in standard beam "
    "formula references. The bending moment diagram is plotted with sagging (positive) drawn "
    "downward, also matching that convention.",
]


def render():
    st.subheader("Assumptions")
    for a in ASSUMPTIONS:
        st.markdown(f"- {a}")
