import math

import streamlit as st

import partial_factors
import ww_geometry as geo

COMBOS = ["SLS", "EQU", "STR/GEO Comb1", "STR/GEO Comb2"]

GAMMA_W = geo.GAMMA_W


def _gamma(row_key, combo, table=partial_factors.UNFAVOURABLE):
    return table[row_key][combo]


def combo_terms(combo, inputs, geometry_results, favourable):
    """Loading/self-weight terms for one combination.

    `favourable=True` switches the wall's own self-weight (and the heel surcharge's vertical
    contribution) to the minimum/favourable case used for sliding & overturning resistance —
    matching the culvert app's Table B.4 (max vertical) / Table B.5 (min vertical) split. Earth
    pressure and water uplift are always applied at their unfavourable (destabilising) value,
    since active pressure and buoyancy never help stability. Per EC0, a variable action (the
    surcharge) contributes zero when its effect would be favourable — so W_q_heel is dropped
    entirely in the favourable case rather than just down-factored.

    The additional horizontal point load and the vertical component of a sloped backfill's active
    thrust are both applied identically regardless of `favourable`, for the same reason F_active
    is: they're not the wall's own self-weight, so there's no "minimum self-weight" scenario for
    them to switch on.
    """
    H_stem, t_stem, t_base = inputs["H_stem"], inputs["t_stem"], inputs["t_base"]
    L_toe, L_heel = inputs["L_toe"], inputs["L_heel"]
    L_base, H_total = geometry_results["L_base"], geometry_results["H_total"]
    gamma_concrete = inputs["gamma_concrete"]
    gamma_backfill = inputs["gamma_backfill"]
    q_surcharge = inputs["q_surcharge"]
    h_wt = inputs["h_wt"]
    beta = inputs.get("beta", 0.0)
    P_h, h_P = inputs.get("P_h", 0.0), inputs.get("h_P", 0.0)

    gamma_M = _gamma("Material factor to phi', gamma_M", combo)
    phi_backfill_d = geo.design_angle(inputs["phi_backfill"], gamma_M)
    Ka = geo.rankine_ka(phi_backfill_d, beta)

    gamma_q = _gamma("Variable/traffic surcharge action, gamma_Q;sup", combo)
    gamma_water = _gamma("Vertical and horizontal water pressures, gamma_G;sup", combo)
    gamma_soil_drv = _gamma("Self weight of structure & backfill, gamma_G;sup", combo)

    depth_wt = max(H_total - h_wt, 0.0)
    F_active_earth, F_active_v, M_active_earth = geo.active_force_moment(
        Ka, gamma_soil_drv * gamma_backfill, gamma_q * q_surcharge, H_total, depth_wt, beta
    )
    P_h_design = gamma_q * P_h

    if favourable:
        gamma_self = partial_factors.FAVOURABLE["Self weight of structure & backfill, gamma_G;inf"][combo]
        W_q_heel = 0.0
    else:
        gamma_self = gamma_soil_drv
        W_q_heel = gamma_q * q_surcharge * L_heel

    h_wt_above_stem_base = max(h_wt - t_base, 0.0)
    gamma_eff = geo.gamma_eff_backfill(gamma_backfill, H_stem, h_wt_above_stem_base)

    W_stem = gamma_self * gamma_concrete * t_stem * H_stem
    W_base = gamma_self * gamma_concrete * L_base * t_base
    W_soil = gamma_self * gamma_eff * L_heel * H_stem
    U = gamma_water * GAMMA_W * h_wt * L_base

    x_stem = L_toe + t_stem / 2.0
    x_base = L_base / 2.0
    x_soil = L_toe + t_stem + L_heel / 2.0
    x_U = L_base / 2.0

    return {
        "Ka": Ka, "phi_backfill_d": phi_backfill_d, "gamma_M": gamma_M,
        "F_active_earth": F_active_earth, "M_active_earth": M_active_earth,
        "F_active_v": F_active_v, "x_active_v": L_base,
        "P_h_design": P_h_design, "h_P": h_P,
        "W_stem": W_stem, "x_stem": x_stem,
        "W_base": W_base, "x_base": x_base,
        "W_soil": W_soil, "x_soil": x_soil,
        "W_q_heel": W_q_heel, "x_q_heel": x_soil,
        "U": U, "x_U": x_U,
    }


def _bearing_capacity(combo, inputs, L_base, B_eff, V_bearing, F_active, phi_backfill_d):
    """EC7 Annex D bearing resistance (drained), strip footing — shape/depth/base-inclination
    factors taken as 1.0 (Annex D itself omits depth & ground-inclination factors; see BS EN
    1997-1:2004+A1:2013, Annex D.3 and the note under 5.3)."""
    gamma_M = _gamma("Material factor to phi', gamma_M", combo)
    phi_founding_d = geo.design_angle(inputs["phi_founding"], gamma_M)
    c_founding_d = inputs["c_founding"] / gamma_M
    phi_rad = math.radians(phi_founding_d)

    D_emb = inputs["D_emb"]
    h_wt = inputs["h_wt"]
    gamma_founding = inputs["gamma_founding"]

    # Effective overburden at founding level, in front of the toe, accounting for the water table
    submerged_depth = min(h_wt, D_emb)
    q_eff = gamma_founding * (D_emb - submerged_depth) + (gamma_founding - GAMMA_W) * submerged_depth

    # Founding soil below bearing level is submerged whenever the water table sits above it
    gamma_founding_Ngamma = gamma_founding - GAMMA_W if h_wt > 0 else gamma_founding

    if phi_founding_d > 1e-6:
        Nq = math.exp(math.pi * math.tan(phi_rad)) * math.tan(math.radians(45.0 + phi_founding_d / 2.0)) ** 2
        Nc = (Nq - 1.0) / math.tan(phi_rad)
        Ngamma = 2.0 * (Nq - 1.0) * math.tan(phi_rad)
    else:
        Nq, Nc, Ngamma = 1.0, math.pi + 2.0, 0.0

    # Inclination factors (strip footing, m=2), per EC7 Annex D.4
    denom = V_bearing + L_base * c_founding_d / math.tan(phi_rad) if phi_founding_d > 1e-6 and c_founding_d > 0 else V_bearing
    ratio = max(0.0, 1.0 - F_active / denom) if denom > 0 else 0.0
    iq = ratio ** 2
    igamma = ratio ** 3
    ic = (iq - (1.0 - iq) / (Nc * math.tan(phi_rad))) if phi_founding_d > 1e-6 else iq

    R_bearing = c_founding_d * Nc * ic + q_eff * Nq * iq + 0.5 * gamma_founding_Ngamma * B_eff * Ngamma * igamma

    return {
        "phi_founding_d": phi_founding_d, "Nq": Nq, "Nc": Nc, "Ngamma": Ngamma,
        "q_eff": q_eff, "iq": iq, "igamma": igamma, "ic": ic,
        "R_bearing": R_bearing,
    }


def stability_check(combo, inputs, geometry_results):
    st.markdown(f"#### Stability at {combo}")

    L_base = geometry_results["L_base"]
    phi_founding = inputs["phi_founding"]

    # ── Sliding & overturning: favourable (minimum) self-weight scenario ──────────────
    t_res = combo_terms(combo, inputs, geometry_results, favourable=True)
    gamma_M = t_res["gamma_M"]
    phi_founding_d = geo.design_angle(phi_founding, gamma_M)
    c_founding_d = inputs["c_founding"] / gamma_M

    st.write(f"Ka (design) = **{t_res['Ka']:.3f}** (φ_d = {t_res['phi_backfill_d']:.1f}°)")
    F_active = t_res["F_active_earth"] + t_res["P_h_design"]
    M_active = t_res["M_active_earth"] + t_res["P_h_design"] * t_res["h_P"]
    st.write(
        f"F_active = F_earth + P_h = {t_res['F_active_earth']:.2f} + {t_res['P_h_design']:.2f} = "
        f"**{F_active:.2f}kN/m**"
    )
    st.write(
        f"M_active (about base) = M_earth + P_h×h_P = {t_res['M_active_earth']:.2f} + "
        f"{t_res['P_h_design']:.2f}×{t_res['h_P']:.2f} = **{M_active:.2f}kNm/m**"
    )
    if t_res["F_active_v"] > 0:
        st.write(
            f"Sloped backfill also gives a vertical thrust component, F_active,v = "
            f"**{t_res['F_active_v']:.2f}kN/m**, acting at the back of the heel (x = L_base)."
        )

    st.markdown("**Sliding**")
    V_resist = (
        t_res["W_stem"] + t_res["W_base"] + t_res["W_soil"] + t_res["W_q_heel"]
        + t_res["F_active_v"] - t_res["U"]
    )
    st.write(
        f"V_resist = {t_res['W_stem']:.2f} + {t_res['W_base']:.2f} + {t_res['W_soil']:.2f} + "
        f"{t_res['W_q_heel']:.2f} + {t_res['F_active_v']:.2f} (F_active,v) − {t_res['U']:.2f} (uplift) "
        f"= **{V_resist:.2f}kN/m**"
    )
    st.write(f"δ_d = phi_founding,d = tan⁻¹(tan{phi_founding:.0f} / {gamma_M:.2f}) = **{phi_founding_d:.1f}°**")
    R_sliding = V_resist * math.tan(math.radians(phi_founding_d)) + c_founding_d * L_base
    st.write(
        f"R_sliding = V_resist × tanδ_d + c'_d × L_base = {V_resist:.2f} × tan{phi_founding_d:.1f}° + "
        f"{c_founding_d:.2f} × {L_base:.2f} = **{R_sliding:.2f}kN/m**"
    )
    ur_sliding = F_active / R_sliding if R_sliding > 0 else float("inf")
    ok_sliding = ur_sliding <= 1.0
    st.write(
        f"UR_sliding = F_active / R_sliding = {F_active:.2f} / {R_sliding:.2f} = "
        f"**{ur_sliding:.2f}** {'∴ **OK**.' if ok_sliding else '∴ **NOT OK** — review required.'}"
        f" (passive resistance in front of the toe neglected)"
    )

    st.markdown("**Overturning (about the toe)**")
    M_stabilizing = (
        t_res["W_stem"] * t_res["x_stem"] + t_res["W_base"] * t_res["x_base"]
        + t_res["W_soil"] * t_res["x_soil"] + t_res["W_q_heel"] * t_res["x_q_heel"]
        + t_res["F_active_v"] * t_res["x_active_v"] - t_res["U"] * t_res["x_U"]
    )
    st.write(f"M_stabilizing = **{M_stabilizing:.2f}kNm/m**")
    ur_ot = M_active / M_stabilizing if M_stabilizing > 0 else float("inf")
    ok_ot = ur_ot <= 1.0
    st.write(
        f"UR_overturning = M_active / M_stabilizing = {M_active:.2f} / {M_stabilizing:.2f} = "
        f"**{ur_ot:.2f}** {'∴ **OK**.' if ok_ot else '∴ **NOT OK** — review required.'}"
    )

    # ── Bearing: unfavourable (maximum) self-weight scenario ──────────────────────────
    st.markdown("**Bearing**")
    b_res = combo_terms(combo, inputs, geometry_results, favourable=False)
    F_active_b = b_res["F_active_earth"] + b_res["P_h_design"]
    M_active_b = b_res["M_active_earth"] + b_res["P_h_design"] * b_res["h_P"]
    V_bearing = (
        b_res["W_stem"] + b_res["W_base"] + b_res["W_soil"] + b_res["W_q_heel"]
        + b_res["F_active_v"] - b_res["U"]
    )
    M_stb_bearing = (
        b_res["W_stem"] * b_res["x_stem"] + b_res["W_base"] * b_res["x_base"]
        + b_res["W_soil"] * b_res["x_soil"] + b_res["W_q_heel"] * b_res["x_q_heel"]
        + b_res["F_active_v"] * b_res["x_active_v"] - b_res["U"] * b_res["x_U"]
    )
    x_R = (M_stb_bearing - M_active_b) / V_bearing if V_bearing > 0 else L_base / 2.0
    e = abs(x_R - L_base / 2.0)
    ecc_ok = e <= L_base / 6.0
    B_eff = max(L_base - 2.0 * e, 0.05)
    q_Ed = V_bearing / B_eff

    st.write(f"V_bearing = **{V_bearing:.2f}kN/m**, resultant at x_R = {x_R:.2f}m from toe")
    st.write(
        f"Eccentricity e = |x_R − L_base/2| = **{e:.3f}m** "
        f"({'within' if ecc_ok else 'OUTSIDE'} middle third, L_base/6 = {L_base / 6:.3f}m)"
    )
    st.write(f"B_eff = L_base − 2e = **{B_eff:.2f}m**")
    st.write(f"q_Ed = V_bearing / B_eff = {V_bearing:.2f} / {B_eff:.2f} = **{q_Ed:.2f}kPa**")

    bc = _bearing_capacity(combo, inputs, L_base, B_eff, V_bearing, F_active_b, t_res["phi_backfill_d"])
    st.write(
        f"phi_founding,d = **{bc['phi_founding_d']:.1f}°** → Nq = {bc['Nq']:.2f}, Nc = {bc['Nc']:.2f}, "
        f"Nγ = {bc['Ngamma']:.2f}"
    )
    st.write(
        f"Inclination factors (strip, m=2): iq = {bc['iq']:.3f}, iγ = {bc['igamma']:.3f} "
        f"(from F_active/V_bearing = {F_active_b:.2f} / {V_bearing:.2f})"
    )
    st.write(
        f"R_bearing = c'_d·Nc·ic + q'·Nq·iq + 0.5·γ'·B_eff·Nγ·iγ = **{bc['R_bearing']:.2f}kPa**"
    )
    ur_bearing = q_Ed / bc["R_bearing"] if bc["R_bearing"] > 0 else float("inf")
    ok_bearing = ur_bearing <= 1.0
    st.write(
        f"UR_bearing = q_Ed / R_bearing = {q_Ed:.2f} / {bc['R_bearing']:.2f} = **{ur_bearing:.2f}** "
        f"{'∴ **OK**.' if ok_bearing else '∴ **NOT OK** — review required.'}"
    )

    return {
        "ur_sliding": ur_sliding, "ok_sliding": ok_sliding,
        "ur_overturning": ur_ot, "ok_overturning": ok_ot,
        "ur_bearing": ur_bearing, "ok_bearing": ok_bearing,
        "eccentricity": e, "ecc_ok": ecc_ok,
        "V_bearing": V_bearing, "q_Ed": q_Ed, "B_eff": B_eff, "x_R": x_R,
    }


def render(inputs, geometry_results):
    st.subheader("Global Stability")

    st.write(
        "Sliding, overturning and bearing are checked across all four limit states (SLS, EQU, "
        "STR/GEO Comb1, STR/GEO Comb2), reusing the same UK NA partial factors as the culvert "
        "calculation sheet."
    )
    st.write(
        "Passive resistance in front of the toe is neglected — conservative, and appropriate here "
        "given the toe cover can be lost to scour at a watercourse."
    )
    st.write(
        "Sliding and overturning use the wall's minimum (favourable) self-weight, as the variable "
        "surcharge is dropped from the resisting side entirely (EC0: a variable action contributes "
        "nothing when its effect would be favourable). Bearing uses the wall's maximum (unfavourable) "
        "self-weight, since higher self-weight increases bearing demand."
    )
    beta = inputs.get("beta", 0.0)
    if beta > 0:
        st.write(
            "A sloped backfill (Rankine) makes the active thrust act inclined at β to the horizontal — "
            "its vertical component is treated as an additional downward load at the back of the heel "
            "(x = L_base), identically in every check (it isn't the wall's own self-weight, so there's "
            "no favourable/unfavourable scenario for it to switch between)."
        )
    if inputs.get("P_h", 0.0) > 0:
        st.write(
            "The additional horizontal point load is treated as a variable action (same partial factors "
            "as the surcharge) and included in every check — it has no vertical component."
        )

    combo_results = {}
    for combo in COMBOS:
        combo_results[combo] = stability_check(combo, inputs, geometry_results)
        st.markdown("---")

    return combo_results
