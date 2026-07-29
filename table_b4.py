import math

import streamlit as st

import partial_factors

# PD6694-1 Annex B, Table B.4 — directly determined design values of K per limit state
TABLE_B4 = {
    "SLS": {"Ka_traffic": 0.33, "Ka_earth": 0.33, "Kmax": 0.60},
    "EQU": {"Ka_traffic": 0.37, "Ka_earth": 0.44, "Kmax": 0.60},
    "STR/GEO Comb1": {"Ka_traffic": 0.33, "Ka_earth": 0.40, "Kmax": 0.72},
    "STR/GEO Comb2": {"Ka_traffic": 0.41, "Ka_earth": 0.49, "Kmax": 0.84},
}
COMBOS = ["SLS", "EQU", "STR/GEO Comb1", "STR/GEO Comb2"]

# PD6694-1 Table 6: horizontal UDL surcharge, coefficient of Kd (kN/m²) — see Global Calculations
F_HUDL_LM12_COEFF = 20.0
F_HUDL_LM3_COEFF = 30.0

GAMMA_SD_EC = 1.15   # PD6694-1 Cl. 10.2.2 model factor for superimposed permanent loads (fixed, all combos)
TAN_30 = math.tan(math.radians(30))


def _gamma(row_key, combo):
    return partial_factors.UNFAVOURABLE[row_key][combo]


def _fmt(gamma, is_sls):
    return "" if is_sls else f"{gamma:.2f} × "


def _sliding_check(combo, inputs, box_culvert_results, lm1_results, lm3_results):
    is_sls = combo == "SLS"
    st.markdown(f"#### Sliding at {combo}")

    H_ext = box_culvert_results["H_ext"]
    B_ext = box_culvert_results["B_ext"]
    W_box = box_culvert_results["W_box"]
    layer_udls = box_culvert_results["layer_udls"]
    F_hll_1m_coeff = box_culvert_results["F_hll_1m_coeff"]

    gamma_backfill = inputs["gamma_backfill"]
    phi_founding = inputs["phi_founding"]
    L_L = inputs["L_L"]

    Ka_traffic = TABLE_B4[combo]["Ka_traffic"]
    Ka_earth = TABLE_B4[combo]["Ka_earth"]
    Kmax = TABLE_B4[combo]["Kmax"]

    gamma_self = _gamma("Self weight of structure & backfill, gamma_G;sup", combo)
    gamma_super = _gamma("Superimposed permanent load, gamma_G;sup", combo)
    gamma_Q_sup = _gamma("Road traffic action on box, gamma_Q;sup", combo)
    gamma_M = _gamma("Material factor to phi', gamma_M", combo)

    if is_sls:
        st.write("γF = 1.0 for all elements.")

    # Road construction (Layer 1) vs fill (remaining layers) — see nomenclature.md for this assumption
    road_udl_char = layer_udls[0] if layer_udls else 0.0
    fill_udl_char = sum(layer_udls[1:]) if len(layer_udls) > 1 else 0.0
    surcharge_road = partial_factors.ROAD_CONSTRUCTION_DEVIATION["unfavourable"] * road_udl_char
    if is_sls:
        st.write(
            f"Maximum surcharge from road construction = "
            f"{partial_factors.ROAD_CONSTRUCTION_DEVIATION['unfavourable']:.2f} × {road_udl_char:.2f} "
            f"= **{surcharge_road:.2f}kN/m**"
        )
        st.write(f"Maximum surcharge from fill above roof level = **{fill_udl_char:.2f}kN/m**")

    g_super = _fmt(gamma_super, is_sls)
    active_surcharge = Ka_earth * gamma_super * (surcharge_road + fill_udl_char) * H_ext
    passive_surcharge = Kmax * gamma_super * (surcharge_road + fill_udl_char) * H_ext
    st.write(
        f"Active force from surcharge = {Ka_earth:.2f} × {g_super}({surcharge_road:.2f} + {fill_udl_char:.2f}) "
        f"× {H_ext:.1f} = **{active_surcharge:.2f}kN**"
    )
    st.write(
        f"Passive force from surcharge = {Kmax:.2f} × {g_super}({surcharge_road:.2f} + {fill_udl_char:.2f}) "
        f"× {H_ext:.1f} = **{passive_surcharge:.2f}kN**"
    )

    backfill_pressure = gamma_backfill * H_ext
    if is_sls:
        st.write(
            f"Backfill pressure at foundation level = {gamma_backfill:.0f} × {H_ext:.1f} "
            f"= **{backfill_pressure:.1f}kN/m²**"
        )

    g_self = _fmt(gamma_self, is_sls)
    active_backfill = Ka_earth * gamma_self * backfill_pressure * H_ext / 2
    passive_backfill = Kmax * gamma_self * backfill_pressure * H_ext / 2
    st.write(
        f"Active force from backfill up to roof = {Ka_earth:.2f} × {g_self}{backfill_pressure:.1f} "
        f"× {H_ext:.1f} / 2 = **{active_backfill:.2f}kN**"
    )
    st.write(
        f"Passive force from backfill up to roof = {Kmax:.2f} × {g_self}{backfill_pressure:.1f} "
        f"× {H_ext:.1f} / 2 = **{passive_backfill:.2f}kN**"
    )

    g_Q = _fmt(gamma_Q_sup, is_sls)
    active_line_load = Ka_traffic * gamma_Q_sup * F_hll_1m_coeff
    st.write(
        f"Active force from traffic surcharge line load = {Ka_traffic:.2f} × {g_Q}{F_hll_1m_coeff:.2f} "
        f"= **{active_line_load:.2f}kN**"
    )

    if is_sls:
        active_lm1_udl = Ka_traffic * gamma_Q_sup * F_HUDL_LM12_COEFF * H_ext
        st.write(
            f"Active force from LM1 traffic UDL surcharge = {Ka_traffic:.2f} × {F_HUDL_LM12_COEFF:.0f} "
            f"× {H_ext:.1f} = **{active_lm1_udl:.2f}kN**"
        )

    active_lm3_udl = Ka_traffic * gamma_Q_sup * F_HUDL_LM3_COEFF * H_ext
    st.write(
        f"Active force from LM3 traffic UDL surcharge = {Ka_traffic:.2f} × {g_Q}{F_HUDL_LM3_COEFF:.0f} "
        f"× {H_ext:.1f} = **{active_lm3_udl:.2f}kN**"
    )

    lm1_braking_per_m = lm1_results["Q_lk"] / L_L
    lm3_braking_per_m = lm3_results["Q_brk_per_m"]
    if is_sls:
        st.write(f"Braking and acceleration force for LM1 traffic = **{lm1_braking_per_m:.2f}kN**")
        st.write(f"Braking and acceleration force for LM3 traffic = **{lm3_braking_per_m:.2f}kN**")
        braking_lm3 = lm3_braking_per_m
    else:
        braking_lm3 = gamma_Q_sup * lm3_braking_per_m
        st.write(
            f"Braking and acceleration force for LM3 traffic = {gamma_Q_sup:.2f} × {lm3_braking_per_m:.2f} "
            f"= **{braking_lm3:.2f}kN**"
        )

    total_active = active_surcharge + active_backfill + active_line_load + active_lm3_udl + braking_lm3
    st.write(
        f"Total active force with LM3 traffic = {active_surcharge:.2f} + {active_backfill:.2f} "
        f"+ {active_line_load:.2f} + {active_lm3_udl:.2f} + {braking_lm3:.2f} = **{total_active:.2f}kN**"
    )

    total_passive = passive_surcharge + passive_backfill
    st.write(f"Total passive force = {passive_surcharge:.2f} + {passive_backfill:.2f} = **{total_passive:.2f}kN**")

    if total_active > total_passive:
        st.write("Active force > Passive force ∴ friction under the base is required to stop sliding.")
    else:
        st.write("Passive force ≥ Active force ∴ no friction under the base is required.")

    st.write("Vertical load on foundation:")
    road_vertical_base = GAMMA_SD_EC * partial_factors.ROAD_CONSTRUCTION_DEVIATION["unfavourable"] * road_udl_char * B_ext
    fill_vertical_base = GAMMA_SD_EC * fill_udl_char * B_ext

    if is_sls:
        road_vertical = road_vertical_base
        fill_vertical = fill_vertical_base
        self_weight_vertical = W_box
        st.write(
            f"Road construction = {GAMMA_SD_EC:.2f} × "
            f"{partial_factors.ROAD_CONSTRUCTION_DEVIATION['unfavourable']:.2f} × {road_udl_char:.2f} "
            f"× {B_ext:.1f} = **{road_vertical:.2f}kN**"
        )
        st.write(f"Fill on roof = {GAMMA_SD_EC:.2f} × {fill_udl_char:.2f} × {B_ext:.1f} = **{fill_vertical:.2f}kN**")
        st.write(f"Self weight of concrete = **{self_weight_vertical:.1f}kN**")
    else:
        road_vertical = gamma_super * road_vertical_base
        fill_vertical = gamma_super * fill_vertical_base
        self_weight_vertical = gamma_self * W_box
        st.write(f"Road construction = {gamma_super:.2f} × {road_vertical_base:.2f} = **{road_vertical:.2f}kN**")
        st.write(f"Fill on roof = {gamma_super:.2f} × {fill_vertical_base:.2f} = **{fill_vertical:.2f}kN**")
        st.write(f"Self weight of concrete = {gamma_self:.2f} × {W_box:.1f} = **{self_weight_vertical:.2f}kN**")

    if is_sls:
        lm1_udl_vertical = lm1_results["lane_udls"].get(1, 0.0) * B_ext
        st.write(
            f"LM1 traffic UDL = {lm1_results['lane_udls'].get(1, 0.0):.2f} × {B_ext:.1f} "
            f"= **{lm1_udl_vertical:.2f}kN**"
        )
        lm1_ts_vertical = lm1_results["patch_load"] * lm1_results["disp_m"] * 2
        st.write(
            f"LM1 traffic Tandem System = {lm1_results['patch_load']:.1f} × {lm1_results['disp_m']:.3f} × 2 "
            f"= **{lm1_ts_vertical:.0f}kN**"
        )
        lm3_vertical = lm3_results["max_V_per_m"]
        st.write(f"LM3 traffic (Maximum Vertical Load, LM3 Calculations) = **{lm3_vertical:.2f}kN**")
        st.write("By inspection LM3 traffic critical (maximum horizontal with minimum vertical loading).")
    else:
        lm3_vertical = gamma_Q_sup * lm3_results["max_V_per_m"]
        st.write(
            f"LM3 traffic = {gamma_Q_sup:.2f} × {lm3_results['max_V_per_m']:.1f} = **{lm3_vertical:.1f}kN**"
        )

    V_d = road_vertical + fill_vertical + self_weight_vertical + lm3_vertical
    st.write(
        f"V'_d = {road_vertical:.2f} + {fill_vertical:.2f} + {self_weight_vertical:.2f} + {lm3_vertical:.2f} "
        f"= **{V_d:.2f}kN**"
    )

    delta_d_rad = math.atan(math.tan(math.radians(phi_founding)) / gamma_M)
    delta_d_deg = math.degrees(delta_d_rad)
    max_Rd = V_d * math.tan(delta_d_rad)
    st.write(f"Maximum R_d = {V_d:.2f} × tan{delta_d_deg:.1f}° = **{max_Rd:.0f}kN**")

    friction_required = total_active - total_passive
    if friction_required < max_Rd:
        st.write(
            f"Friction required = {total_active:.2f} - {total_passive:.2f} = {friction_required:.2f} "
            f"< {max_Rd:.0f} ∴ sliding can be resisted using Kmax = {Kmax:.2f} ∴ **OK**."
        )
    else:
        st.write(
            f"Friction required = {total_active:.2f} - {total_passive:.2f} = {friction_required:.2f} "
            f"≥ {max_Rd:.0f} ∴ sliding **CANNOT** be resisted using Kmax = {Kmax:.2f} — review required."
        )

    return {
        "total_active": total_active,
        "total_passive": total_passive,
        "V_d": V_d,
        "delta_d_deg": delta_d_deg,
        "max_Rd": max_Rd,
        "friction_required": friction_required,
        "ok": friction_required < max_Rd,
    }


def render(inputs, box_culvert_results, lm1_results, lm3_results):
    """Render the PD6694-1 Annex B Table B.4 / Figure B.4 stability checks (sliding, overturning, bearing)."""
    results = {}

    st.subheader("Load Case Table B.4")

    left, right = st.columns([1, 1])
    with right:
        st.image("assets/pd6694_table_b4.png", use_container_width=True)
        st.image("assets/pd6694_figure_b4.png", use_container_width=True)

    with left:
        st.write(
            "Stability needs to be considered by assessing the resistance to sliding and overturning "
            "together with the bearing pressure to PD 6694-1:2011 Clauses 10.3.2 and 10.3.3."
        )
        st.write(
            "Load effects in the members will need to be considered if Kmax has to be increased above "
            "the values given in PD 6694-1:2011 Table B.4."
        )
        st.write("Partial Factors can be determined as before.")

        st.write("Consider horizontal forces to check sliding:")
        st.write(
            "For drained conditions design resistance to sliding R_d = V'_d tan δ_d where δ = "
            "structure-ground interface friction angle = phi_founding"
        )
        st.write("Applying γM to tanδ we get δ_d = tan⁻¹(tanδ / γM)")

        phi_founding = inputs["phi_founding"]
        for combo in COMBOS:
            gamma_M = _gamma("Material factor to phi', gamma_M", combo)
            delta_d = math.degrees(math.atan(math.tan(math.radians(phi_founding)) / gamma_M))
            st.write(f"{combo}: δ_d = tan⁻¹(tan{phi_founding:.0f} / {gamma_M:.2f}) = **{delta_d:.1f}°**")

    st.divider()

    combo_results = {}
    for combo in COMBOS:
        combo_results[combo] = _sliding_check(combo, inputs, box_culvert_results, lm1_results, lm3_results)
        st.markdown("---")

    results["sliding"] = combo_results

    return results
