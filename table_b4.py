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


def common_terms(combo, inputs, box_culvert_results, favourable=False):
    """Terms shared by both traffic models — surcharge, backfill, road/fill/self-weight vertical loads.

    `favourable=True` switches every permanent-load quantity to its favourable/minimum counterpart
    (used by Table B.5 — "minimum vertical load"): gamma_G;inf instead of gamma_G;sup, the -40% road
    construction deviation instead of +55%, and no GAMMA_SD_EC model factor (that factor only applies
    to the unfavourable/maximum case per PD6694-1 Cl. 10.2.2 and Figure B.4 — Figure B.5 omits it).
    """
    is_sls = combo == "SLS"

    H_ext = box_culvert_results["H_ext"]
    B_ext = box_culvert_results["B_ext"]
    W_box = box_culvert_results["W_box"]
    layer_udls = box_culvert_results["layer_udls"]
    gamma_backfill = inputs["gamma_backfill"]

    Ka_earth = TABLE_B4[combo]["Ka_earth"]
    Kmax = TABLE_B4[combo]["Kmax"]
    if favourable:
        gamma_self = partial_factors.FAVOURABLE["Self weight of structure & backfill, gamma_G;inf"][combo]
        gamma_super = partial_factors.FAVOURABLE["Superimposed permanent load, gamma_G;inf"][combo]
        road_dev = partial_factors.ROAD_CONSTRUCTION_DEVIATION["favourable"]
        gamma_sd_ec = 1.0
        extreme_word = "Minimum"
    else:
        gamma_self = _gamma("Self weight of structure & backfill, gamma_G;sup", combo)
        gamma_super = _gamma("Superimposed permanent load, gamma_G;sup", combo)
        road_dev = partial_factors.ROAD_CONSTRUCTION_DEVIATION["unfavourable"]
        gamma_sd_ec = GAMMA_SD_EC
        extreme_word = "Maximum"

    if is_sls:
        st.write("γF = 1.0 for all elements.")

    # Road construction (Layer 1) vs fill (remaining layers) — see nomenclature.md for this assumption
    road_udl_char = layer_udls[0] if layer_udls else 0.0
    fill_udl_char = sum(layer_udls[1:]) if len(layer_udls) > 1 else 0.0
    surcharge_road = road_dev * road_udl_char
    if is_sls:
        st.write(
            f"{extreme_word} surcharge from road construction = "
            f"{road_dev:.2f} × {road_udl_char:.2f} = **{surcharge_road:.2f}kN/m**"
        )
        st.write(f"{extreme_word} surcharge from fill above roof level = **{fill_udl_char:.2f}kN/m**")

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

    total_passive = passive_surcharge + passive_backfill
    st.write(f"Total passive force = {passive_surcharge:.2f} + {passive_backfill:.2f} = **{total_passive:.2f}kN**")

    st.write("Vertical load on foundation (common terms):")
    sd_ec_label = f"{gamma_sd_ec:.2f} × " if gamma_sd_ec != 1.0 else ""
    road_vertical_base = gamma_sd_ec * road_dev * road_udl_char * B_ext
    fill_vertical_base = gamma_sd_ec * fill_udl_char * B_ext

    if is_sls:
        road_vertical = road_vertical_base
        fill_vertical = fill_vertical_base
        self_weight_vertical = W_box
        st.write(
            f"Road construction = {sd_ec_label}{road_dev:.2f} × {road_udl_char:.2f} "
            f"× {B_ext:.1f} = **{road_vertical:.2f}kN**"
        )
        st.write(
            f"Fill on roof = {sd_ec_label}{fill_udl_char:.2f} × {B_ext:.1f} = **{fill_vertical:.2f}kN**"
        )
        st.write(f"Self weight of concrete = **{self_weight_vertical:.1f}kN**")
    else:
        road_vertical = gamma_super * road_vertical_base
        fill_vertical = gamma_super * fill_vertical_base
        self_weight_vertical = gamma_self * W_box
        st.write(f"Road construction = {gamma_super:.2f} × {road_vertical_base:.2f} = **{road_vertical:.2f}kN**")
        st.write(f"Fill on roof = {gamma_super:.2f} × {fill_vertical_base:.2f} = **{fill_vertical:.2f}kN**")
        st.write(f"Self weight of concrete = {gamma_self:.2f} × {W_box:.1f} = **{self_weight_vertical:.2f}kN**")

    return {
        "total_passive": total_passive,
        "passive_surcharge": passive_surcharge,
        "passive_backfill": passive_backfill,
        "active_surcharge": active_surcharge,
        "active_backfill": active_backfill,
        "common_vertical": road_vertical + fill_vertical + self_weight_vertical,
    }


def model_check(model, combo, common, inputs, box_culvert_results, lm1_results, lm3_results, buoyancy=0.0):
    """Full active/vertical/friction check for a single traffic model (LM1 or LM3) at a given combo.

    `buoyancy` (design/factored value, kN) is a Table B.6 addition — a water-table uplift force that
    reduces V'_d before the friction resistance is computed. Zero for Tables B.4/B.5 (no water table).
    """
    is_sls = combo == "SLS"

    H_ext = box_culvert_results["H_ext"]
    B_ext = box_culvert_results["B_ext"]
    F_hll_1m_coeff = box_culvert_results["F_hll_1m_coeff"]
    phi_founding = inputs["phi_founding"]
    L_L = inputs["L_L"]

    Ka_traffic = TABLE_B4[combo]["Ka_traffic"]
    Kmax = TABLE_B4[combo]["Kmax"]
    gamma_Q_sup = _gamma("Road traffic action on box, gamma_Q;sup", combo)
    gamma_M = _gamma("Material factor to phi', gamma_M", combo)

    st.markdown(f"**{model} Scenario**")

    g_Q = _fmt(gamma_Q_sup, is_sls)
    active_line_load = Ka_traffic * gamma_Q_sup * F_hll_1m_coeff
    st.write(
        f"Active force from traffic surcharge line load = {Ka_traffic:.2f} × {g_Q}{F_hll_1m_coeff:.2f} "
        f"= **{active_line_load:.2f}kN**"
    )

    udl_coeff = F_HUDL_LM12_COEFF if model == "LM1" else F_HUDL_LM3_COEFF
    active_udl = Ka_traffic * gamma_Q_sup * udl_coeff * H_ext
    st.write(
        f"Active force from {model} traffic UDL surcharge = {Ka_traffic:.2f} × {g_Q}{udl_coeff:.0f} "
        f"× {H_ext:.1f} = **{active_udl:.2f}kN**"
    )

    if model == "LM1":
        braking_char = lm1_results["Q_lk"] / L_L
        vertical_char = lm1_results["lane_udls"].get(1, 0.0) * B_ext + lm1_results["patch_load"] * lm1_results["disp_m"] * 2
    else:
        braking_char = lm3_results["Q_brk_per_m"]
        vertical_char = lm3_results["max_V_per_m"]

    if is_sls:
        st.write(f"Braking and acceleration force for {model} traffic = **{braking_char:.2f}kN**")
        braking = braking_char
    else:
        braking = gamma_Q_sup * braking_char
        st.write(
            f"Braking and acceleration force for {model} traffic = {gamma_Q_sup:.2f} × {braking_char:.2f} "
            f"= **{braking:.2f}kN**"
        )

    total_active = common["active_surcharge"] + common["active_backfill"] + active_line_load + active_udl + braking
    st.write(
        f"Total active force with {model} traffic = {common['active_surcharge']:.2f} + "
        f"{common['active_backfill']:.2f} + {active_line_load:.2f} + {active_udl:.2f} + {braking:.2f} "
        f"= **{total_active:.2f}kN**"
    )

    total_passive = common["total_passive"]
    if total_active > total_passive:
        st.write("Active force > Passive force ∴ friction under the base is required to stop sliding.")
    else:
        st.write("Passive force ≥ Active force ∴ no friction under the base is required.")

    if is_sls:
        vertical = vertical_char
        if model == "LM1":
            st.write(
                f"LM1 traffic UDL = {lm1_results['lane_udls'].get(1, 0.0):.2f} × {B_ext:.1f} "
                f"= **{lm1_results['lane_udls'].get(1, 0.0) * B_ext:.2f}kN**"
            )
            st.write(
                f"LM1 traffic Tandem System = {lm1_results['patch_load']:.1f} × {lm1_results['disp_m']:.3f} × 2 "
                f"= **{lm1_results['patch_load'] * lm1_results['disp_m'] * 2:.2f}kN**"
            )
        else:
            st.write(f"LM3 traffic (Maximum Vertical Load, LM3 Calculations) = **{vertical_char:.2f}kN**")
    else:
        vertical = gamma_Q_sup * vertical_char
        st.write(f"{model} traffic = {gamma_Q_sup:.2f} × {vertical_char:.2f} = **{vertical:.2f}kN**")

    V_d = common["common_vertical"] + vertical
    if buoyancy:
        st.write(f"V'_d (before buoyancy) = {common['common_vertical']:.2f} + {vertical:.2f} = **{V_d:.2f}kN**")
        V_d = V_d - buoyancy
        st.write(f"V'_d = {V_d + buoyancy:.2f} − {buoyancy:.2f} (buoyancy) = **{V_d:.2f}kN**")
    else:
        st.write(f"V'_d = {common['common_vertical']:.2f} + {vertical:.2f} = **{V_d:.2f}kN**")

    delta_d_rad = math.atan(math.tan(math.radians(phi_founding)) / gamma_M)
    delta_d_deg = math.degrees(delta_d_rad)
    max_Rd = V_d * math.tan(delta_d_rad)
    st.write(f"Maximum R_d = {V_d:.2f} × tan{delta_d_deg:.1f}° = **{max_Rd:.2f}kN**")

    friction_required = total_active - total_passive
    ok = friction_required < max_Rd
    if ok:
        st.write(
            f"Friction required = {total_active:.2f} - {total_passive:.2f} = {friction_required:.2f} "
            f"< {max_Rd:.2f} ∴ sliding can be resisted using Kmax = {Kmax:.2f} ∴ **OK**."
        )
    else:
        st.write(
            f"Friction required = {total_active:.2f} - {total_passive:.2f} = {friction_required:.2f} "
            f"≥ {max_Rd:.2f} ∴ sliding **CANNOT** be resisted using Kmax = {Kmax:.2f} — review required."
        )

    # Overturning about the toe (base edge on the passive side) — same forces and Kmax/Kr as sliding,
    # taken as a moment: rectangular pressures (surcharge, UDL) act at H_ext/2, the triangular backfill
    # pressure acts at H_ext/3, and line loads (traffic line load, braking) act at the roof, H_ext.
    st.write("Consider moments about the toe to check overturning:")
    M_active = (
        common["active_surcharge"] * (H_ext / 2)
        + common["active_backfill"] * (H_ext / 3)
        + active_line_load * H_ext
        + active_udl * (H_ext / 2)
        + braking * H_ext
    )
    M_passive = common["passive_surcharge"] * (H_ext / 2) + common["passive_backfill"] * (H_ext / 3)
    st.write(
        f"M_active = {common['active_surcharge']:.2f}×{H_ext / 2:.2f} + {common['active_backfill']:.2f}×"
        f"{H_ext / 3:.2f} + {active_line_load:.2f}×{H_ext:.2f} + {active_udl:.2f}×{H_ext / 2:.2f} + "
        f"{braking:.2f}×{H_ext:.2f} = **{M_active:.2f}kNm**"
    )
    st.write(
        f"M_passive = {common['passive_surcharge']:.2f}×{H_ext / 2:.2f} + {common['passive_backfill']:.2f}×"
        f"{H_ext / 3:.2f} = **{M_passive:.2f}kNm**"
    )

    M_driving = max(0.0, M_active - M_passive)
    M_stabilizing = V_d * (B_ext / 2)
    st.write(f"M_driving = {M_active:.2f} − {M_passive:.2f} = **{M_driving:.2f}kNm**")
    st.write(f"M_stabilizing = V'_d × B_ext/2 = {V_d:.2f} × {B_ext / 2:.2f} = **{M_stabilizing:.2f}kNm**")

    ok_ot = M_driving < M_stabilizing
    if ok_ot:
        st.write(
            f"M_driving = {M_driving:.2f} < M_stabilizing = {M_stabilizing:.2f} "
            f"∴ overturning can be resisted using Kmax = {Kmax:.2f} ∴ **OK**."
        )
    else:
        st.write(
            f"M_driving = {M_driving:.2f} ≥ M_stabilizing = {M_stabilizing:.2f} "
            f"∴ overturning **CANNOT** be resisted using Kmax = {Kmax:.2f} — review required."
        )

    return {
        "total_active": total_active,
        "total_passive": total_passive,
        "V_d": V_d,
        "delta_d_deg": delta_d_deg,
        "max_Rd": max_Rd,
        "friction_required": friction_required,
        "margin": max_Rd - friction_required,
        "ok": ok,
        "M_driving": M_driving,
        "M_stabilizing": M_stabilizing,
        "ot_margin": M_stabilizing - M_driving,
        "ot_ok": ok_ot,
    }


def sliding_check(combo, inputs, box_culvert_results, lm1_results, lm3_results, favourable=False, buoyancy=0.0):
    st.markdown(f"#### Sliding & Overturning at {combo}")

    common = common_terms(combo, inputs, box_culvert_results, favourable=favourable)

    lm1_result = model_check(
        "LM1", combo, common, inputs, box_culvert_results, lm1_results, lm3_results, buoyancy=buoyancy
    )
    lm3_result = model_check(
        "LM3", combo, common, inputs, box_culvert_results, lm1_results, lm3_results, buoyancy=buoyancy
    )

    governing = "LM1" if lm1_result["margin"] < lm3_result["margin"] else "LM3"
    st.markdown(
        f"**Governing case (sliding): {governing}** "
        f"(margin = max R_d − friction required: LM1 = {lm1_result['margin']:.2f}kN, "
        f"LM3 = {lm3_result['margin']:.2f}kN — smaller margin governs)."
    )

    governing_ot = "LM1" if lm1_result["ot_margin"] < lm3_result["ot_margin"] else "LM3"
    st.markdown(
        f"**Governing case (overturning): {governing_ot}** "
        f"(margin = M_stabilizing − M_driving: LM1 = {lm1_result['ot_margin']:.2f}kNm, "
        f"LM3 = {lm3_result['ot_margin']:.2f}kNm — smaller margin governs)."
    )

    return {"LM1": lm1_result, "LM3": lm3_result, "governing": governing, "governing_overturning": governing_ot}


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

        st.write("Consider moments about the toe (base edge on the passive side) to check overturning:")
        st.write(
            "M_driving = active surcharge (arm H_ext/2) + active backfill (arm H_ext/3) + traffic line load "
            "and braking (arm H_ext, at roof level) + traffic UDL surcharge (arm H_ext/2), less the "
            "restoring moment from the same Kmax passive pressure used for sliding."
        )
        st.write("M_stabilizing = V'_d × B_ext/2, using the same V'_d as the sliding check.")

        st.write(
            "Both LM1 and LM3 are checked fully at every limit state — the one with the smaller margin "
            "(max R_d − friction required, or M_stabilizing − M_driving for overturning) governs. Neither "
            "is assumed critical in advance."
        )

    st.divider()

    combo_results = {}
    for combo in COMBOS:
        combo_results[combo] = sliding_check(combo, inputs, box_culvert_results, lm1_results, lm3_results)
        st.markdown("---")

    results["sliding"] = combo_results

    return results
