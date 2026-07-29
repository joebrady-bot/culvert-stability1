import streamlit as st

import partial_factors
import table_b4

# Table B.6's Ka values and initial passive coefficient are identical to Table B.4/B.5's (confirmed against
# the source PDF) — reuse directly. The passive coefficient is labelled Kr rather than Kmax in Table B.6 /
# Figure B.6, reflecting PD6694-1 Cl. 10.3.3: the passive pressure may initially be based on Kmax, and
# increased above Kmax (Kr > Kmax) if that proves insufficient to prevent sliding/overturning, provided the
# structure is designed for the increased pressure and the associated movements are acceptable at the
# relevant limit state. The numeric starting point is identical to Kmax, so no separate table is needed.
TABLE_B6 = table_b4.TABLE_B4
COMBOS = table_b4.COMBOS

GAMMA_W = 9.81  # kN/m3 — unit weight of water


def render(inputs, box_culvert_results, lm1_results, lm3_results):
    """Render the PD6694-1 Annex B Table B.6 / Figure B.6 sliding check — minimum vertical load case with a
    water table present.

    Identical to Table B.5 (minimum vertical load: favourable self weight and superimposed permanent load,
    −40% road construction deviation, no γSd;ec model factor) except V'_d is additionally reduced by a
    buoyancy force, computed from Archimedes' principle over the box's submerged external cross-section:
    F_buoyancy = γw × B_ext × min(h_wt, H_ext). Figure B.6 shows Buoyancy as a single discrete upward force
    alongside Friction — not folded into the earth pressure diagrams, which are unchanged from B.4/B.5 — so
    no adjustment is made to backfill unit weight or earth pressure coefficients below the water table.
    """
    results = {}

    st.subheader("Load Case Table B.6")

    left, right = st.columns([1, 1])
    with right:
        st.image("assets/pd6694_table_b6.png", use_container_width=True)
        st.image("assets/pd6694_figure_b6.png", use_container_width=True)

    with left:
        st.write(
            "Stability needs to be considered by assessing the resistance to sliding and overturning "
            "together with the bearing pressure to PD 6694-1:2011 Clauses 10.3.2 and 10.3.3."
        )
        st.write(
            "This is Table B.5's minimum vertical load case (favourable self weight and superimposed "
            "permanent load, −40% road construction deviation, no γSd;ec model factor) with a water table "
            "present: a buoyancy force now acts upward on the structure, reducing V'_d and hence the "
            "friction available to resist sliding."
        )
        st.write(
            "Per PD6694-1 Cl. 10.3.3, the earth pressure on the passive face may initially be based on "
            "Kmax (identical values to Tables B.4/B.5). If that is insufficient to prevent sliding, the "
            "passive pressure may be increased above Kmax — denoted Kr in Table B.6/Figure B.6 — provided "
            "the structure is designed for the increased pressure and the associated movements are "
            "acceptable at the relevant limit state."
        )

        h_wt = inputs["h_wt"]
        H_ext = box_culvert_results["H_ext"]
        B_ext = box_culvert_results["B_ext"]
        submerged_height = min(h_wt, H_ext)
        F_buoyancy_char = GAMMA_W * B_ext * submerged_height

        st.write("Consider buoyancy uplift on the box (Archimedes' principle, submerged external cross-section):")
        st.write(
            f"Submerged height = min(h_wt, H_ext) = min({h_wt:.2f}, {H_ext:.2f}) = **{submerged_height:.2f}m**"
        )
        st.write(
            f"F_buoyancy (characteristic) = γw × B_ext × submerged height = {GAMMA_W:.2f} × {B_ext:.2f} × "
            f"{submerged_height:.2f} = **{F_buoyancy_char:.2f}kN/m**"
        )

        st.write(
            "Both LM1 and LM3 are checked fully at every limit state — the one with the smaller margin "
            "(max R_d − friction required) governs. Neither is assumed critical in advance."
        )

    st.divider()

    combo_results = {}
    for combo in COMBOS:
        gamma_water = partial_factors.UNFAVOURABLE["Vertical and horizontal water pressures, gamma_G;sup"][combo]
        F_buoyancy_design = gamma_water * F_buoyancy_char
        st.write(f"{combo}: F_buoyancy = {gamma_water:.2f} × {F_buoyancy_char:.2f} = **{F_buoyancy_design:.2f}kN**")
        combo_results[combo] = table_b4.sliding_check(
            combo, inputs, box_culvert_results, lm1_results, lm3_results,
            favourable=True, buoyancy=F_buoyancy_design,
        )
        st.markdown("---")

    results["sliding"] = combo_results

    return results
