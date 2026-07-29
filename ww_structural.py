import math

import streamlit as st

import ww_geometry as geo
import ww_stability as stab

STRUCTURAL_COMBO = "STR/GEO Comb1"
ALPHA_CC = 0.85
GAMMA_C = 1.5
GAMMA_S = 1.15


def _bearing_dist(V, x_R, L_base):
    """Trapezoidal (or triangular, if the resultant falls outside the middle third) bearing
    pressure at the toe and heel ends of the base."""
    e = abs(x_R - L_base / 2.0)
    if e <= L_base / 6.0:
        q_center = V / L_base
        if x_R <= L_base / 2.0:
            q_toe = q_center * (1.0 + 6.0 * e / L_base)
            q_heel = q_center * (1.0 - 6.0 * e / L_base)
        else:
            q_toe = q_center * (1.0 - 6.0 * e / L_base)
            q_heel = q_center * (1.0 + 6.0 * e / L_base)
    else:
        if x_R <= L_base / 2.0:
            a = max(3.0 * x_R, 0.001)
            q_toe, q_heel = 2.0 * V / a, 0.0
        else:
            a = max(3.0 * (L_base - x_R), 0.001)
            q_heel, q_toe = 2.0 * V / a, 0.0
    return max(q_toe, 0.0), max(q_heel, 0.0)


def _section_capacity(name, M_Ed, V_Ed, h_mm, cover_mm, bar_dia_mm, bar_spacing_mm, f_ck, f_yk, tension_face):
    """EC2 capacity check for a given reinforcement arrangement — inverse of the usual design
    direction: As is provided (from bar diameter/spacing), M_Rd and V_Rd,c are calculated from it."""
    f_cd = ALPHA_CC * f_ck / GAMMA_C
    f_yd = f_yk / GAMMA_S
    b = 1000.0
    d = max(h_mm - cover_mm - bar_dia_mm / 2.0, 10.0)

    As_prov = (math.pi / 4.0 * bar_dia_mm ** 2) * (1000.0 / bar_spacing_mm)  # mm2/m

    x = (As_prov * f_yd) / (0.8 * b * f_cd)
    z = min(d - 0.4 * x, 0.95 * d)
    M_Rd = As_prov * f_yd * z / 1.0e6  # kNm/m

    xu_over_d = x / d if d > 0 else 0.0
    over_reinforced = xu_over_d > 0.45

    f_ctm = (0.30 * f_ck ** (2.0 / 3.0)) if f_ck <= 50 else (2.12 * math.log(1.0 + (f_ck + 8.0) / 10.0))
    As_min = max(0.26 * (f_ctm / f_yk) * b * d, 0.0013 * b * d)

    rho_l = min(As_prov / (b * d), 0.02)
    k_v = min(1.0 + math.sqrt(200.0 / d), 2.0)
    CRd_c = 0.18 / GAMMA_C
    v_min = 0.035 * k_v ** 1.5 * math.sqrt(f_ck)
    VRd_c = max(CRd_c * k_v * (100.0 * rho_l * f_ck) ** (1.0 / 3.0), v_min) * b * d / 1000.0  # kN/m

    UR_bend = abs(M_Ed) / M_Rd if M_Rd > 0 else float("inf")
    UR_shear = abs(V_Ed) / VRd_c if VRd_c > 0 else float("inf")

    return {
        "name": name, "M_Ed": M_Ed, "V_Ed": V_Ed, "h_mm": h_mm, "d_mm": d,
        "As_prov": As_prov, "As_min": As_min, "z_mm": z, "M_Rd": M_Rd,
        "over_reinforced": over_reinforced, "VRd_c": VRd_c,
        "UR_bend": UR_bend, "ok_bend": UR_bend <= 1.0 and not over_reinforced,
        "UR_shear": UR_shear, "ok_shear": UR_shear <= 1.0,
        "tension_face": tension_face,
    }


def _report_section(sec):
    st.write(
        f"As_provided = {sec['As_prov']:.0f}mm²/m (As_min = {sec['As_min']:.0f}mm²/m per Cl. 9.2.1.1), "
        f"d = {sec['d_mm']:.0f}mm, z = {sec['z_mm']:.0f}mm"
    )
    st.write(f"M_Rd = As_provided × f_yd × z = **{sec['M_Rd']:.2f}kNm/m**")
    bend_note = " — section over-reinforced (x/d > 0.45): add compression steel or increase section." \
        if sec["over_reinforced"] else ""
    st.write(
        f"UR_bend = M_Ed / M_Rd = {abs(sec['M_Ed']):.2f} / {sec['M_Rd']:.2f} = **{sec['UR_bend']:.2f}** "
        f"{'∴ **OK**.' if sec['ok_bend'] else '∴ **NOT OK**.'}{bend_note}"
    )
    st.write(f"V_Rd,c (no shear links) = **{sec['VRd_c']:.2f}kN/m**")
    st.write(
        f"UR_shear = V_Ed / V_Rd,c = {abs(sec['V_Ed']):.2f} / {sec['VRd_c']:.2f} = **{sec['UR_shear']:.2f}** "
        f"{'∴ **OK**.' if sec['ok_shear'] else '∴ **NOT OK** — shear links required.'}"
    )


def render(inputs, geometry_results):
    st.subheader("Structural Design (EC2) — Capacity Check")
    st.write(
        "Stem, heel and toe are checked against the reinforcement specified in Inputs, using "
        "STR/GEO Combination 1 action factors (γG=1.35 / γQ=1.35) — the combination with the "
        "largest actions, and the one used for structural (EC2) design per the UK NA to BS EN 1990."
    )

    H_stem, t_stem, t_base = inputs["H_stem"], inputs["t_stem"], inputs["t_base"]
    L_toe, L_heel = inputs["L_toe"], inputs["L_heel"]
    L_base = geometry_results["L_base"]
    f_ck, f_yk, cover = inputs["f_ck"], inputs["f_yk"], inputs["cover"]
    gamma_concrete = inputs["gamma_concrete"]
    gamma_backfill = inputs["gamma_backfill"]
    q_surcharge = inputs["q_surcharge"]
    h_wt = inputs["h_wt"]

    combo = STRUCTURAL_COMBO
    gamma_M = stab._gamma("Material factor to phi', gamma_M", combo)
    phi_backfill_d = geo.design_angle(inputs["phi_backfill"], gamma_M)
    Ka = geo.rankine_ka(phi_backfill_d)
    gamma_q = stab._gamma("Variable/traffic surcharge action, gamma_Q;sup", combo)
    gamma_soil = stab._gamma("Self weight of structure & backfill, gamma_G;sup", combo)

    # ── Stem — vertical cantilever from the top of the base slab ──────────────────────
    st.markdown("#### Stem (at base)")
    depth_wt_stem = max(H_stem - max(h_wt - t_base, 0.0), 0.0)
    F_stem, M_stem = geo.active_force_moment(
        Ka, gamma_soil * gamma_backfill, gamma_q * q_surcharge, H_stem, depth_wt_stem
    )
    st.write(f"M_Ed (stem base) = **{M_stem:.2f}kNm/m**, V_Ed = **{F_stem:.2f}kN/m**")

    sec_stem = _section_capacity(
        "Stem", M_stem, F_stem, t_stem * 1000.0, cover, inputs["stem_bar_dia"], inputs["stem_bar_spacing"],
        f_ck, f_yk, "back (retained soil) face",
    )
    _report_section(sec_stem)

    # ── Factored bearing pressure distribution at the structural combo ────────────────
    t_res = stab.combo_terms(combo, inputs, geometry_results, favourable=False)
    V_str = t_res["W_stem"] + t_res["W_base"] + t_res["W_soil"] + t_res["W_q_heel"] - t_res["U"]
    M_stb_str = (
        t_res["W_stem"] * t_res["x_stem"] + t_res["W_base"] * t_res["x_base"]
        + t_res["W_soil"] * t_res["x_soil"] + t_res["W_q_heel"] * t_res["x_q_heel"]
        - t_res["U"] * t_res["x_U"]
    )
    x_R_str = (M_stb_str - t_res["M_active"]) / V_str if V_str > 0 else L_base / 2.0
    q_toe, q_heel = _bearing_dist(V_str, x_R_str, L_base)
    st.write(f"Factored bearing pressure at {combo}: q_toe = **{q_toe:.2f}kPa**, q_heel = **{q_heel:.2f}kPa**")

    def q_at(x):
        return q_toe + (q_heel - q_toe) * x / L_base

    gamma_eff = geo.gamma_eff_backfill(gamma_backfill, H_stem, max(h_wt - t_base, 0.0))

    # ── Heel — cantilever fixed at the stem face, free at the heel end ────────────────
    st.markdown("#### Heel slab (at stem face)")
    x_root_heel = L_toe + t_stem
    q_h1, q_h2 = q_at(x_root_heel), q_at(L_base)
    w_down_heel = gamma_soil * gamma_eff * H_stem + gamma_soil * gamma_concrete * t_base + gamma_q * q_surcharge
    p_h1, p_h2 = q_h1 - w_down_heel, q_h2 - w_down_heel
    M_heel = L_heel ** 2 / 6.0 * (p_h1 + 2.0 * p_h2)
    V_heel = L_heel * (p_h1 + p_h2) / 2.0
    # A cantilever always hogs under a net downward load (tension on top at the support — the same
    # reason balcony/canopy slabs need top steel), and sags under a net upward load (bottom tension).
    tf_heel = "bottom face" if M_heel > 0 else "top face"
    st.write(f"Net pressure (upward +): root = {p_h1:.2f}kPa, free end = {p_h2:.2f}kPa")
    st.write(f"M_Ed = **{M_heel:.2f}kNm/m**, V_Ed = **{V_heel:.2f}kN/m** — tension in {tf_heel}")

    sec_heel = _section_capacity(
        "Heel", M_heel, V_heel, t_base * 1000.0, cover, inputs["heel_bar_dia"], inputs["heel_bar_spacing"],
        f_ck, f_yk, tf_heel,
    )
    _report_section(sec_heel)

    # ── Toe — cantilever fixed at the stem face, free at the toe end ──────────────────
    st.markdown("#### Toe slab (at stem face)")
    if L_toe > 1e-3:
        q_t1, q_t2 = q_at(L_toe), q_at(0.0)
        w_down_toe = gamma_soil * gamma_concrete * t_base
        p_t1, p_t2 = q_t1 - w_down_toe, q_t2 - w_down_toe
        M_toe = L_toe ** 2 / 6.0 * (p_t1 + 2.0 * p_t2)
        V_toe = L_toe * (p_t1 + p_t2) / 2.0
        tf_toe = "bottom face" if M_toe > 0 else "top face"
        st.write(f"Net pressure (upward +): root = {p_t1:.2f}kPa, free end = {p_t2:.2f}kPa")
        st.write(f"M_Ed = **{M_toe:.2f}kNm/m**, V_Ed = **{V_toe:.2f}kN/m** — tension in {tf_toe}")
    else:
        M_toe, V_toe, tf_toe = 0.0, 0.0, "bottom face"
        st.write("L_toe = 0 — no toe slab to design.")

    sec_toe = _section_capacity(
        "Toe", M_toe, V_toe, t_base * 1000.0, cover, inputs["toe_bar_dia"], inputs["toe_bar_spacing"],
        f_ck, f_yk, tf_toe,
    )
    _report_section(sec_toe)

    return {"stem": sec_stem, "heel": sec_heel, "toe": sec_toe}
