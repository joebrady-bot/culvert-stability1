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
    "RC Design tab: rectangular sections only — flanged (T/L) beams are not covered. The section "
    "is designed once for the governing sagging moment, hogging moment and shear from the Results "
    "tab (M_max, M_min, V_max) — it does not check moment/shear at every position along the beam, "
    "or curtail reinforcement, so it is only valid where a uniform section is provided throughout.",
    "RC Design follows the flexure (Figure 2) and vertical shear, strut-inclination (Figure 5) "
    "procedures in 'How to Design Concrete Structures using Eurocode 2: 4. Beams' (Moss & "
    "Brooker, The Concrete Centre), using UK NA values (αcc = 0.85, γc = 1.5, γs = 1.15). "
    "Deflection and crack width are not checked.",
    "The minimum shear reinforcement ratio (ρw,min = 0.08√fck/fyk, EC2 Cl. 9.2.2) is included even "
    "though it isn't part of Figure 5's own flowchart, since it's a mandatory EC2 requirement "
    "wherever shear links are provided.",
]


def render():
    st.subheader("Assumptions")
    for a in ASSUMPTIONS:
        st.markdown(f"- {a}")
