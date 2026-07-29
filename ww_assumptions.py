import streamlit as st

import partial_factors

ASSUMPTIONS = [
    "Design is carried out on a 1.0 m length of wall (cantilever L-shape wing wall), with a "
    "constant stem thickness (no taper) and a constant-thickness base slab.",
    "Active earth pressure uses the classical Rankine coefficient Ka = tan²(45 − φ'_d/2) — a "
    "horizontal retained surface and a vertical back plane at the heel end are assumed. Unlike "
    "the culvert-stability sheet's buried-structure earth pressure tables (PD 6694-1 Annex B), "
    "no γSd;K = 1.2 model factor is applied — that factor is specific to soil strain-ratcheting "
    "around buried box/portal structures under cyclic traffic loading, which does not apply to "
    "an exposed cantilever retaining wall.",
    "The live load surcharge behind the wall is a simple uniform UDL (default 10 kPa, per the UK's "
    "traditional BD 30/87 Cl. 3.4 convention for backfilled retaining walls/abutments), rather than "
    "a vehicle-specific model — this is simpler than the PD 6694-1 Table 6 model used for the "
    "culvert, and is an editable input.",
    "Passive resistance in front of the toe is neglected in the sliding check — conservative, and "
    "particularly appropriate for a wing wall where toe cover can be lost to scour at a watercourse.",
    "Sliding and overturning resistance use the wall's minimum (favourable) self-weight, with the "
    "surcharge's vertical contribution on the heel dropped entirely — a variable action is not "
    "credited when its effect would be favourable (BS EN 1990 principle). Bearing uses the maximum "
    "(unfavourable) self-weight, since higher self-weight increases bearing demand.",
    "Bearing resistance follows BS EN 1997-1 Annex D (drained, strip footing), including load "
    "inclination factors from the horizontal shear at the base. Shape, depth and base/ground "
    "inclination factors are all taken as 1.0 — Annex D itself omits depth and ground-inclination "
    "factors (see the note under 5.3), and a horizontal base/ground surface is assumed.",
    "The water table is defined by height above the underside of the base slab. Below it, active "
    "pressure uses effective (submerged) soil stress plus separate hydrostatic pressure, and an "
    "uplift force (γw × h_wt × L_base, uniform head) acts on the underside of the base — the same "
    "discrete-force treatment used for Table B.6 in the culvert-stability sheet, rather than a full "
    "seepage/flow-net analysis.",
    "No overall (slip-circle) slope stability check is performed — this tool covers sliding, "
    "bearing and overturning of the wall itself only. Global slope stability of the wider "
    "embankment/cutting should be checked separately where relevant.",
    "Structural (EC2) checks are capacity checks against a reinforcement arrangement you specify "
    "(bar diameter and spacing for stem, heel and toe), not a reinforcement design — the tool "
    "reports the utilisation of the given arrangement rather than solving for the required area. "
    "Shear is checked without links (VRd,c only); if V_Ed exceeds VRd,c, shear reinforcement design "
    "is not currently covered.",
    "Structural design uses STR/GEO Combination 1 action factors throughout (γG = 1.35, γQ = 1.35), "
    "consistent with UK NA practice of using the Set B combination for EC2 member design.",
]


def render():
    st.subheader("Assumptions")
    for a in ASSUMPTIONS:
        st.markdown(f"- {a}")

    st.divider()
    partial_factors.render()
