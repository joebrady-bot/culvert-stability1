import math

import streamlit as st

import table_b4

# Table B.5's K values are identical to Table B.4's (confirmed against the source PDF) — reuse directly.
TABLE_B5 = table_b4.TABLE_B4
COMBOS = table_b4.COMBOS


def render(inputs, box_culvert_results, lm1_results, lm3_results):
    """Render the PD6694-1 Annex B Table B.5 / Figure B.5 sliding check — minimum vertical load case.

    Structurally identical to Table B.4 (same K values, same active/passive/traffic mechanics), but every
    permanent-load quantity switches to its favourable/minimum counterpart: gamma_G;inf instead of
    gamma_G;sup, -40% road construction deviation instead of +55%, and no GAMMA_SD_EC model factor
    (Figure B.5 omits it — that factor only applies to the unfavourable/maximum case). Traffic-related
    terms (line load, UDL surcharge, braking, LM1/LM3 vertical) are unchanged from Table B.4, since they're
    live actions, not permanent loads — confirmed with the user rather than assumed (see conversation).
    """
    results = {}

    st.subheader("Load Case Table B.5")

    left, right = st.columns([1, 1])
    with right:
        st.image("assets/pd6694_table_b5.png", use_container_width=True)
        st.image("assets/pd6694_figure_b5.png", use_container_width=True)

    with left:
        st.write(
            "Stability needs to be considered by assessing the resistance to sliding and overturning "
            "together with the bearing pressure to PD 6694-1:2011 Clauses 10.3.2 and 10.3.3."
        )
        st.write(
            "Load effects in the members will need to be considered if Kmax has to be increased above "
            "the values given in PD 6694-1:2011 Table B.5."
        )
        st.write(
            "This is the minimum vertical load case: self weight and superimposed permanent load use "
            "favourable γF, road construction uses the −40% deviation, and no γSd;ec model factor applies "
            "(Figure B.5 omits it — that factor only applies to the maximum/unfavourable case, Table B.4)."
        )

        st.write("Consider horizontal forces to check sliding:")
        st.write(
            "For drained conditions design resistance to sliding R_d = V'_d tan δ_d where δ = "
            "structure-ground interface friction angle = phi_founding"
        )
        st.write("Applying γM to tanδ we get δ_d = tan⁻¹(tanδ / γM)")

        phi_founding = inputs["phi_founding"]
        for combo in COMBOS:
            gamma_M = table_b4._gamma("Material factor to phi', gamma_M", combo)
            delta_d = math.degrees(math.atan(math.tan(math.radians(phi_founding)) / gamma_M))
            st.write(f"{combo}: δ_d = tan⁻¹(tan{phi_founding:.0f} / {gamma_M:.2f}) = **{delta_d:.1f}°**")

        st.write(
            "Both LM1 and LM3 are checked fully at every limit state — the one with the smaller margin "
            "(max R_d − friction required) governs. Neither is assumed critical in advance."
        )

    st.divider()

    combo_results = {}
    for combo in COMBOS:
        combo_results[combo] = table_b4.sliding_check(
            combo, inputs, box_culvert_results, lm1_results, lm3_results, favourable=True
        )
        st.markdown("---")

    results["sliding"] = combo_results

    return results
