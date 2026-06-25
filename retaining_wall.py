"""
retaining_wall.py — L-Shape Retaining Wall Design Checker

Standards:
  BS EN 1997-1:2004 + UK National Annex  (EC7 Design Approach 1)
  BS EN 1992-1-1:2004 + UK National Annex  (EC2 concrete design)

Geometry convention (all dimensions in metres, per unit length of wall):

       t_stem
       |←──→|
       ████   ← Stem (front face flush with start of toe/stem junction)
       ████     Height = H_stem
       ████
  ─────████──────────────────
  |    ████                 |  ← Base slab, thickness = t_base
  └────┴───┴────────────────┘
  ←L_toe→← →←──── L_heel ──→
          t_stem
  ←────── L_base ────────────→

  Retained fill sits on the HEEL side (right).
  Active earth pressure acts on a virtual vertical back plane at the heel end.
  Total wall height for pressure: H = H_stem + t_base.
"""

import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# Partial factors  (EN 1997-1 Annex A Tables A.1–A.4, UK NA)
# ─────────────────────────────────────────────────────────────────────────────
# EQU  — equilibrium LS (overturning of rigid body)
# C1   — GEO/STR DA1 Combination 1: A1+M1+R1
# C2   — GEO/STR DA1 Combination 2: A2+M2+R1
# STR  — EN 1992-1-1 structural ULS (matches C1 action factors + concrete/steel)

PF = {
    "EQU": dict(gG_dst=1.10, gG_stb=0.90, gQ=1.50, gphi=1.10),
    "C1":  dict(gG_unf=1.35, gG_fav=1.00, gQ=1.50, gphi=1.00),
    "C2":  dict(gG_unf=1.00, gG_fav=1.00, gQ=1.30, gphi=1.25),
    "STR": dict(gG_unf=1.35, gG_fav=1.00, gQ=1.50, gc=1.50, gs=1.15, acc=0.85),
}

GAMMA_W = 10.0   # kN/m³  (water unit weight, EN 1997-1)


# ─────────────────────────────────────────────────────────────────────────────
# Earth pressure coefficients (Rankine — horizontal surface, vertical back)
# ─────────────────────────────────────────────────────────────────────────────

def _Ka(phi_deg: float) -> float:
    r = math.radians(phi_deg)
    return math.tan(math.pi / 4.0 - r / 2.0) ** 2


def _phi_d(phi_k_deg: float, gphi: float) -> float:
    return math.degrees(math.atan(math.tan(math.radians(phi_k_deg)) / gphi))


# ─────────────────────────────────────────────────────────────────────────────
# Active earth pressure: resultant force and moment about base of virtual back
# ─────────────────────────────────────────────────────────────────────────────

def _active(Ka: float, gr_fac: float, q_fac: float, H: float, h_wt: float):
    """
    Returns (F_a, M_a) — horizontal active resultant (kN/m) and moment
    about the BASE of the virtual back plane (kNm/m).

    gr_fac  = factored soil unit weight (γG × γ_soil) already applied by caller.
    q_fac   = factored surcharge (γQ × q_k).
    h_wt    = water-table depth below top of retained height (use large number for dry).
    """
    if h_wt >= H:
        # Fully dry
        F_q = Ka * q_fac * H
        F_s = Ka * gr_fac * H ** 2 / 2.0
        return F_q + F_s, F_q * H / 2.0 + F_s * H / 3.0

    h_dry = h_wt
    h_wet = H - h_wt
    gr_sub = max(gr_fac - GAMMA_W, 0.0)   # submerged effective (already factored)

    # Dry zone (depth h_dry from top)
    F1 = Ka * q_fac * h_dry                     # surcharge rect in dry zone
    F2 = Ka * gr_fac * h_dry ** 2 / 2.0         # soil tri in dry zone
    M1 = F1 * (h_wet + h_dry / 2.0)
    M2 = F2 * (h_wet + h_dry / 3.0)

    # Wet zone (depth h_wet, from WT to base)
    F3 = Ka * (q_fac + gr_fac * h_dry) * h_wet  # rect from overburden above WT
    F4 = Ka * gr_sub * h_wet ** 2 / 2.0          # tri from submerged soil
    F5 = GAMMA_W * h_wet ** 2 / 2.0              # hydrostatic
    M3 = F3 * h_wet / 2.0
    M4 = F4 * h_wet / 3.0
    M5 = F5 * h_wet / 3.0

    return F1+F2+F3+F4+F5, M1+M2+M3+M4+M5


# ─────────────────────────────────────────────────────────────────────────────
# Effective heel soil unit weight (accounting for partial submergence)
# ─────────────────────────────────────────────────────────────────────────────

def _gamma_r_eff(gamma_r: float, H_stem: float, h_wt: float) -> float:
    if h_wt >= H_stem:
        return gamma_r
    h_dry = min(h_wt, H_stem)
    h_wet = H_stem - h_dry
    return (gamma_r * h_dry + (gamma_r - GAMMA_W) * h_wet) / H_stem


# ─────────────────────────────────────────────────────────────────────────────
# Water uplift on base slab
# ─────────────────────────────────────────────────────────────────────────────

def _uplift(H_stem: float, t_base: float, L_base: float, h_wt: float):
    H_total = H_stem + t_base
    if h_wt >= H_total:
        return 0.0
    return GAMMA_W * (H_total - h_wt) * L_base   # kN/m (uniform head = conservative)


# ─────────────────────────────────────────────────────────────────────────────
# Bearing pressure distribution (factored) under base slab
# ─────────────────────────────────────────────────────────────────────────────

def _bearing_dist(V: float, x_R: float, L_base: float):
    """
    Returns (q_toe, q_heel) — trapezoidal or triangular bearing pressure (kPa).
    x_R measured from toe end.
    """
    e = abs(x_R - L_base / 2.0)
    if e <= L_base / 6.0:
        # Trapezoidal
        q_center = V / L_base
        if x_R <= L_base / 2.0:
            q_toe  = q_center * (1.0 + 6.0 * e / L_base)
            q_heel = q_center * (1.0 - 6.0 * e / L_base)
        else:
            q_toe  = q_center * (1.0 - 6.0 * e / L_base)
            q_heel = q_center * (1.0 + 6.0 * e / L_base)
    else:
        # Triangular — resultant outside middle-third
        if x_R <= L_base / 2.0:
            a = 3.0 * x_R
            q_toe  = 2.0 * V / max(a, 0.001)
            q_heel = 0.0
        else:
            a = 3.0 * (L_base - x_R)
            q_heel = 2.0 * V / max(a, 0.001)
            q_toe  = 0.0
    return max(q_toe, 0.0), max(q_heel, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# GEO stability check for one combination
# ─────────────────────────────────────────────────────────────────────────────

def _geo_check(combo: str, pf: dict,
               phi_k: float, gamma_r: float, q_k: float,
               gamma_conc: float, phi_f_k: float, q_Rd: float,
               H_stem: float, t_stem: float, L_base: float,
               L_toe: float, t_base: float, h_wt: float) -> dict:

    L_heel = L_base - L_toe - t_stem
    H = H_stem + t_base

    if combo == "EQU":
        gG_dst = pf['gG_dst']   # 1.10
        gG_stb = pf['gG_stb']   # 0.90
        gQ     = pf['gQ']       # 1.50
        gphi   = pf['gphi']     # 1.10
    else:
        gG_dst = pf['gG_unf']   # C1: 1.35 / C2: 1.00
        gG_stb = pf['gG_fav']   # 1.00 both
        gQ     = pf['gQ']       # C1: 1.50 / C2: 1.30
        gphi   = pf['gphi']     # C1: 1.00 / C2: 1.25

    phi_d   = _phi_d(phi_k, gphi)
    phi_f_d = _phi_d(phi_f_k, gphi)
    Ka      = _Ka(phi_d)

    # ── Component characteristic weights ──────────────────────────────────
    W_stem = gamma_conc * t_stem * H_stem
    x_stem = L_toe + t_stem / 2.0

    W_base = gamma_conc * L_base * t_base
    x_base = L_base / 2.0

    gr_eff = _gamma_r_eff(gamma_r, H_stem, h_wt)
    W_soil = gr_eff * L_heel * H_stem
    x_soil = L_toe + t_stem + L_heel / 2.0

    W_q_heel = q_k * L_heel    # variable surcharge on heel (characteristic)
    x_q_heel = x_soil

    U_k = _uplift(H_stem, t_base, L_base, h_wt)
    x_U = L_base / 2.0

    # ── Factored active force ─────────────────────────────────────────────
    F_a, M_a = _active(
        Ka=Ka,
        gr_fac=gG_dst * gamma_r,    # driving soil weight factored unfavourably
        q_fac=gQ * q_k,
        H=H,
        h_wt=h_wt,
    )

    # ─────────────────────────────────────────────────────────────────────
    # OVERTURNING (moment about toe of base)
    # Stabilising: permanent favourable only (variable = 0 on retained side)
    # ─────────────────────────────────────────────────────────────────────
    M_stb_ot = gG_stb * (
        W_stem * x_stem + W_base * x_base + W_soil * x_soil - U_k * x_U
    )
    M_drv_ot = M_a
    UR_ot    = M_drv_ot / M_stb_ot if M_stb_ot > 0 else 999.0
    pass_ot  = UR_ot <= 1.0

    # ─────────────────────────────────────────────────────────────────────
    # SLIDING
    # Resisting: min vertical (gG_stb × permanent) × tan(δ_d)
    # Driving: factored active horizontal
    # Passive on toe neglected (conservative)
    # ─────────────────────────────────────────────────────────────────────
    V_res = max(gG_stb * (W_stem + W_base + W_soil) - U_k, 0.0)
    R_sl  = V_res * math.tan(math.radians(phi_f_d))
    UR_sl = F_a / R_sl if R_sl > 0 else 999.0
    pass_sl = UR_sl <= 1.0

    # ─────────────────────────────────────────────────────────────────────
    # BEARING
    # Max vertical (permanent unfav + variable unfav)
    # ─────────────────────────────────────────────────────────────────────
    V_bear = (
        gG_dst * (W_stem + W_base + W_soil)
        + gQ * W_q_heel
        - U_k
    )
    M_stb_bear = (
        gG_dst * (W_stem * x_stem + W_base * x_base + W_soil * x_soil)
        + gQ * W_q_heel * x_q_heel
        - U_k * x_U
    )
    x_R  = (M_stb_bear - M_a) / V_bear if V_bear > 0 else L_base / 2.0
    e    = abs(x_R - L_base / 2.0)
    B_eff = max(L_base - 2.0 * e, 0.001)
    q_Ed  = V_bear / B_eff if V_bear > 0 else 0.0
    UR_bear  = q_Ed / q_Rd if q_Rd > 0 else 999.0
    pass_bear = UR_bear <= 1.0
    pass_ecc  = x_R > 0 and x_R < L_base   # resultant inside base footprint

    return {
        'combo': combo,
        'phi_d': phi_d, 'Ka': Ka, 'phi_f_d': phi_f_d,
        'W_stem': W_stem, 'x_stem': x_stem,
        'W_base': W_base, 'x_base': x_base,
        'W_soil': W_soil, 'x_soil': x_soil,
        'W_q_heel': W_q_heel, 'U_k': U_k,
        'F_active': F_a, 'M_active': M_a,
        'M_stb_ot': M_stb_ot, 'M_drv_ot': M_drv_ot,
        'UR_overturning': UR_ot, 'pass_overturning': pass_ot,
        'V_resist': V_res, 'R_sliding': R_sl,
        'UR_sliding': UR_sl, 'pass_sliding': pass_sl,
        'V_bearing': V_bear, 'x_resultant': x_R,
        'eccentricity': e, 'B_eff': B_eff,
        'q_Ed': q_Ed, 'q_Rd': q_Rd,
        'UR_bearing': UR_bear, 'pass_bearing': pass_bear,
        'pass_eccentricity': pass_ecc,
    }


# ─────────────────────────────────────────────────────────────────────────────
# EC2 section design (bending + shear, per unit width)
# ─────────────────────────────────────────────────────────────────────────────

def _ec2_section(name: str, M_Ed: float, V_Ed: float,
                 h_mm: float, cover_mm: float, dia_mm: float,
                 f_ck: float, f_yk: float, tension_face: str) -> dict:
    """
    M_Ed  kNm/m  |  V_Ed  kN/m  |  h_mm  thickness in mm
    f_ck  MPa    |  f_yk  MPa   |  cover_mm nominal cover (mm)
    """
    pf = PF["STR"]
    f_cd = pf['acc'] * f_ck / pf['gc']          # MPa
    f_yd = f_yk / pf['gs']                       # MPa

    b  = 1000.0                                  # mm (per metre)
    d  = max(h_mm - cover_mm - dia_mm / 2.0, 10.0)   # mm effective depth

    M_Nmm = abs(M_Ed) * 1.0e6     # kNm/m → N·mm per 1000 mm width

    K_lim = 0.167   # EN 1992-1-1 Cl. 3.1.7 (ε_cu2 = 0.0035, balanced)

    if M_Nmm > 0.0:
        K = M_Nmm / (b * d ** 2 * f_ck)
        K_use = min(K, K_lim)    # if K > K_lim, compression steel needed
        z = d * (0.5 + math.sqrt(max(0.25 - K_use / 1.134, 0.0)))
        z = min(z, 0.95 * d)
        As_req = M_Nmm / (f_yd * z)     # mm²/m
    else:
        K = 0.0
        z = 0.95 * d
        As_req = 0.0

    # Minimum reinforcement — EN 1992-1-1 Cl. 9.2.1.1
    f_ctm = (0.30 * f_ck ** (2.0 / 3.0)) if f_ck <= 50 else (2.12 * math.log(1.0 + (f_ck + 8.0) / 10.0))
    As_min = max(0.26 * (f_ctm / f_yk) * b * d, 0.0013 * b * d)   # mm²/m
    As_max = 0.04 * b * h_mm                                         # mm²/m

    As_design = max(As_req, As_min)

    # Shear without links — EN 1992-1-1 Cl. 6.2.2
    rho_l  = min(As_design / (b * d), 0.02)
    k_v    = min(1.0 + math.sqrt(200.0 / d), 2.0)
    CRd_c  = 0.18 / pf['gc']
    v_min  = 0.035 * k_v ** 1.5 * math.sqrt(f_ck)                         # MPa
    VRd_c1 = CRd_c * k_v * (100.0 * rho_l * f_ck) ** (1.0 / 3.0) * b * d  # N/m
    VRd_c2 = v_min * b * d                                                   # N/m
    VRd_c  = max(VRd_c1, VRd_c2) / 1000.0                                   # kN/m

    UR_bend  = K / K_lim if K_lim > 0 else 999.0
    UR_shear = abs(V_Ed) / VRd_c if VRd_c > 0 else 999.0
    pass_bend  = K <= K_lim
    pass_shear = abs(V_Ed) <= VRd_c

    return {
        'name': name,
        'M_Ed': M_Ed, 'V_Ed': V_Ed,
        'h_mm': h_mm, 'd_mm': d,
        'K': K, 'K_lim': K_lim,
        'z_mm': z,
        'As_req': As_req, 'As_min': As_min, 'As_max': As_max,
        'As_design': As_design,
        'f_cd': f_cd, 'f_yd': f_yd,
        'VRd_c': VRd_c,
        'UR_bend': UR_bend, 'pass_bend': pass_bend,
        'UR_shear': UR_shear, 'pass_shear': pass_shear,
        'tension_face': tension_face,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STR structural checks (stem, heel, toe)
# ─────────────────────────────────────────────────────────────────────────────

def _structural(phi_k, gamma_r, q_k, gamma_conc,
                H_stem, t_stem, L_base, L_toe, t_base, h_wt,
                f_ck, f_yk, cover_nom, bar_stem, bar_base) -> dict:

    pf  = PF["STR"]
    gG  = pf['gG_unf']    # 1.35
    gQ  = pf['gQ']        # 1.50

    L_heel = L_base - L_toe - t_stem
    H      = H_stem + t_base

    # For STR: φ_d = φ_k (M1, gphi=1.0) → Ka at characteristic angle
    Ka = _Ka(phi_k)

    # ── Stem at base — vertical cantilever ───────────────────────────────
    q_fac  = gQ * q_k
    gr_fac = gG * gamma_r

    F_q_s = Ka * q_fac  * H_stem
    F_s_s = Ka * gr_fac * H_stem ** 2 / 2.0
    M_stem_Ed = F_q_s * H_stem / 2.0 + F_s_s * H_stem / 3.0   # kNm/m
    V_stem_Ed = F_q_s + F_s_s                                   # kN/m

    sec_stem = _ec2_section(
        "Stem (at base)", M_stem_Ed, V_stem_Ed,
        h_mm=t_stem * 1000.0, cover_mm=cover_nom,
        dia_mm=bar_stem, f_ck=f_ck, f_yk=f_yk,
        tension_face='back (retained soil) face',
    )

    # ── Factored STR bearing pressure distribution ───────────────────────
    gr_eff   = _gamma_r_eff(gamma_r, H_stem, h_wt)
    W_stem_k = gamma_conc * t_stem * H_stem
    x_stem_k = L_toe + t_stem / 2.0
    W_base_k = gamma_conc * L_base * t_base
    x_base_k = L_base / 2.0
    W_soil_k = gr_eff * L_heel * H_stem
    x_soil_k = L_toe + t_stem + L_heel / 2.0
    W_q_k    = q_k * L_heel
    x_q_k    = x_soil_k
    U_k      = _uplift(H_stem, t_base, L_base, h_wt)
    x_U      = L_base / 2.0

    F_a_str, M_a_str = _active(
        Ka=Ka, gr_fac=gG * gamma_r, q_fac=gQ * q_k, H=H, h_wt=h_wt,
    )

    V_str = gG * (W_stem_k + W_base_k + W_soil_k) + gQ * W_q_k - U_k
    M_stb = (
        gG * (W_stem_k * x_stem_k + W_base_k * x_base_k + W_soil_k * x_soil_k)
        + gQ * W_q_k * x_q_k
        - U_k * x_U
    )
    x_R_str = (M_stb - M_a_str) / V_str if V_str > 0 else L_base / 2.0

    q_toe_str, q_heel_str = _bearing_dist(V_str, x_R_str, L_base)

    def q_at(x: float) -> float:
        return q_toe_str + (q_heel_str - q_toe_str) * x / L_base

    # ── Heel slab — horizontal cantilever (fixed at stem face, free at heel end) ─
    if L_heel > 1e-3:
        x_hroot = L_toe + t_stem   # root position from toe
        q_h1 = q_at(x_hroot)      # bearing pressure at root
        q_h2 = q_at(L_base)       # bearing pressure at heel end (free end)

        # Net pressure (upward +) at root and free end
        w_down_heel = gG * (gr_eff * H_stem + gamma_conc * t_base) + gQ * q_k
        p_h1 = q_h1 - w_down_heel
        p_h2 = q_h2 - w_down_heel

        # Moment at root (cantilever): M = L²/6 × (p_root + 2×p_free)
        M_heel_Ed = L_heel ** 2 / 6.0 * (p_h1 + 2.0 * p_h2)   # kNm/m
        V_heel_Ed = L_heel * (p_h1 + p_h2) / 2.0               # kN/m

        # Positive M_heel_Ed → net upward cantilever → tension in TOP face
        tf_heel = 'top face' if M_heel_Ed > 0 else 'bottom face'
        sec_heel = _ec2_section(
            "Heel slab (at stem face)", M_heel_Ed, V_heel_Ed,
            h_mm=t_base * 1000.0, cover_mm=cover_nom,
            dia_mm=bar_base, f_ck=f_ck, f_yk=f_yk,
            tension_face=tf_heel,
        )
    else:
        sec_heel = None
        M_heel_Ed = V_heel_Ed = 0.0
        q_h1 = q_h2 = 0.0

    # ── Toe slab — horizontal cantilever (fixed at stem face, free at toe end) ──
    if L_toe > 1e-3:
        q_t1 = q_at(L_toe)   # bearing at root (stem face, toe side)
        q_t2 = q_at(0.0)     # bearing at toe end (free end)

        # Downward: only base slab self-weight on toe
        w_down_toe = gG * gamma_conc * t_base
        p_t1 = q_t1 - w_down_toe
        p_t2 = q_t2 - w_down_toe

        M_toe_Ed = L_toe ** 2 / 6.0 * (p_t1 + 2.0 * p_t2)   # kNm/m
        V_toe_Ed = L_toe * (p_t1 + p_t2) / 2.0               # kN/m

        tf_toe = 'top face' if M_toe_Ed > 0 else 'bottom face'
        sec_toe = _ec2_section(
            "Toe slab (at stem face)", M_toe_Ed, V_toe_Ed,
            h_mm=t_base * 1000.0, cover_mm=cover_nom,
            dia_mm=bar_base, f_ck=f_ck, f_yk=f_yk,
            tension_face=tf_toe,
        )
    else:
        sec_toe = None
        M_toe_Ed = V_toe_Ed = 0.0
        q_t1 = q_t2 = 0.0

    return {
        'sec_stem': sec_stem, 'sec_heel': sec_heel, 'sec_toe': sec_toe,
        'q_toe_str': q_toe_str, 'q_heel_str': q_heel_str,
        'x_R_str': x_R_str, 'V_str': V_str,
        'F_a_str': F_a_str, 'M_a_str': M_a_str,
        'M_stem_Ed': M_stem_Ed, 'V_stem_Ed': V_stem_Ed,
        'M_heel_Ed': M_heel_Ed if L_heel > 1e-3 else 0.0,
        'V_heel_Ed': V_heel_Ed if L_heel > 1e-3 else 0.0,
        'M_toe_Ed':  M_toe_Ed  if L_toe  > 1e-3 else 0.0,
        'V_toe_Ed':  V_toe_Ed  if L_toe  > 1e-3 else 0.0,
        'q_h1': q_h1, 'q_h2': q_h2,
        'q_t1': q_t1 if L_toe > 1e-3 else 0.0,
        'q_t2': q_t2 if L_toe > 1e-3 else 0.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Matplotlib diagrams
# ─────────────────────────────────────────────────────────────────────────────

def _wall_diagram(H_stem, t_stem, L_base, L_toe, t_base, h_wt, q_k,
                  geo_results, str_data):
    L_heel = L_base - L_toe - t_stem
    H_total = H_stem + t_base
    pad = max(L_base * 0.18, 0.3)

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.set_aspect('equal')
    ax.set_facecolor('#f5f5f2')

    concrete_col = '#8d9eae'
    soil_col     = '#c4a96a'
    fdn_col      = '#a89060'

    # Foundation soil
    ax.add_patch(patches.Rectangle((-pad, -0.35), L_base + 2 * pad, 0.35,
                                    facecolor=fdn_col, alpha=0.35, linewidth=0))

    # Base slab
    ax.add_patch(patches.Rectangle((0, 0), L_base, t_base,
                                    linewidth=1.5, edgecolor='#2c3e50',
                                    facecolor=concrete_col, alpha=0.85))

    # Stem
    ax.add_patch(patches.Rectangle((L_toe, t_base), t_stem, H_stem,
                                    linewidth=1.5, edgecolor='#2c3e50',
                                    facecolor=concrete_col, alpha=0.85))

    # Retained fill
    ax.add_patch(patches.Rectangle((L_toe + t_stem, t_base), L_heel, H_stem,
                                    linewidth=0, facecolor=soil_col, alpha=0.50))

    # Hatching on retained fill
    ax.add_patch(patches.Rectangle((L_toe + t_stem, t_base), L_heel, H_stem,
                                    linewidth=0, facecolor='none',
                                    hatch='////', edgecolor=soil_col, alpha=0.3))

    # Water table
    y_gl = t_base + H_stem
    if h_wt < H_stem:
        y_wt = t_base + H_stem - h_wt
        ax.plot([L_toe + t_stem + 0.02, L_base + pad * 0.7],
                [y_wt, y_wt], color='#2980b9', lw=1.8, ls='--')
        ax.text(L_base + pad * 0.65, y_wt + 0.05, 'WT',
                color='#2980b9', fontsize=8, ha='right', va='bottom')

    # Ground level
    ax.plot([L_toe + t_stem, L_base + pad * 0.6], [y_gl, y_gl], 'k-', lw=1.2)
    ax.text(L_base + pad * 0.55, y_gl + 0.04, 'GL', fontsize=8, ha='right')

    # Surcharge arrows
    if q_k > 0:
        for xq in [L_toe + t_stem + L_heel * 0.2,
                   L_toe + t_stem + L_heel * 0.5,
                   L_toe + t_stem + L_heel * 0.8]:
            ax.annotate('', xy=(xq, y_gl), xytext=(xq, y_gl + 0.25),
                        arrowprops=dict(arrowstyle='->', color='#e67e22', lw=1.5))
        ax.text(L_base - 0.02, y_gl + 0.28,
                f'q_k = {q_k:.0f} kPa', color='#e67e22', fontsize=8, ha='right')

    # Bearing pressure diagram (STR)
    if str_data is not None:
        q_t = str_data['q_toe_str']
        q_h = str_data['q_heel_str']
        scale = 0.30 / max(q_t, q_h, 1.0)
        xs = [0, L_base]
        qs = [q_t * scale, q_h * scale]
        ax.fill([0, L_base, L_base, 0], [-qs[1] - 0.01, -qs[1] - 0.01, -0.01, -0.01],
                alpha=0.0)
        ax.fill_betweenx([-0.01, -0.01], [0, L_base],
                         alpha=0.0)
        # Draw below base slab
        y_bot = 0.0
        ax.fill([0, L_base, L_base, 0],
                [y_bot - q_t * scale, y_bot - q_h * scale, y_bot, y_bot],
                facecolor='#e74c3c', alpha=0.30, linewidth=0)
        ax.plot([0, L_base], [y_bot - q_t * scale, y_bot - q_h * scale],
                color='#e74c3c', lw=1.5, label=f'ULS bearing')
        ax.text(0, y_bot - q_t * scale - 0.03,
                f'{q_t:.0f}', color='#e74c3c', fontsize=7, ha='center', va='top')
        ax.text(L_base, y_bot - q_h * scale - 0.03,
                f'{q_h:.0f}', color='#e74c3c', fontsize=7, ha='center', va='top')
        ax.text(L_base / 2, y_bot - max(q_t, q_h) * scale / 2,
                'kPa', color='#e74c3c', fontsize=7, ha='center')

    # Dimension lines
    dim_y = -0.25
    ax.annotate('', xy=(0, dim_y), xytext=(L_base, dim_y),
                arrowprops=dict(arrowstyle='<->', color='#444', lw=0.9))
    ax.text(L_base / 2, dim_y - 0.07,
            f'L_base = {L_base:.2f} m', ha='center', fontsize=8, color='#444')

    dim_x = -pad + 0.05
    ax.annotate('', xy=(dim_x, t_base), xytext=(dim_x, t_base + H_stem),
                arrowprops=dict(arrowstyle='<->', color='#444', lw=0.9))
    ax.text(dim_x - 0.04, t_base + H_stem / 2,
            f'H = {H_stem:.2f} m', ha='right', fontsize=8, color='#444', rotation=90, va='center')

    ax.text(L_toe / 2, -0.08,
            f'L_toe\n{L_toe:.2f}m', ha='center', fontsize=7.5, color='#2c3e50')
    ax.text(L_toe + t_stem + L_heel / 2, -0.08,
            f'L_heel\n{L_heel:.2f}m', ha='center', fontsize=7.5, color='#2c3e50')

    # Labels
    ax.text(L_toe + t_stem / 2, t_base + H_stem / 2,
            'STEM', ha='center', va='center', fontsize=7.5,
            color='#2c3e50', fontweight='bold', rotation=90)
    ax.text(L_toe + t_stem + L_heel / 2, t_base + H_stem / 2,
            'RETAINED\nFILL', ha='center', va='center', fontsize=7.5,
            color='#6b4c1e', alpha=0.85)

    ax.set_xlim(-pad, L_base + pad)
    ax.set_ylim(-0.55, H_total + 0.55)
    ax.set_xlabel('Distance from toe (m)', fontsize=9)
    ax.set_ylabel('Height above base (m)', fontsize=9)
    ax.set_title('L-Shape Retaining Wall — Cross Section', fontsize=10, fontweight='bold')
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def _pressure_diagram(phi_k, gamma_r, q_k, H_stem, t_base, h_wt,
                      geo_results, str_data):
    H = H_stem + t_base
    Ka_char = _Ka(phi_k)

    # Build characteristic pressure profile (no partial factors)
    n = 200
    z_arr = [H * i / n for i in range(n + 1)]
    p_char = []
    for z in z_arr:
        if z <= h_wt:
            p = Ka_char * (q_k + gamma_r * z)
        else:
            d_w = z - h_wt
            p = Ka_char * (q_k + gamma_r * h_wt + (gamma_r - GAMMA_W) * d_w) + GAMMA_W * d_w
        p_char.append(p)

    y_arr = [H - z for z in z_arr]   # height above base

    # C2 design pressure (worst factored Ka)
    r_c2 = geo_results.get('C2', {})
    Ka_c2 = r_c2.get('Ka', Ka_char)
    gG_c2 = PF['C2']['gG_unf']
    gQ_c2 = PF['C2']['gQ']
    p_c2  = []
    for z in z_arr:
        if z <= h_wt:
            p = Ka_c2 * (gQ_c2 * q_k + gG_c2 * gamma_r * z)
        else:
            d_w = z - h_wt
            p = Ka_c2 * (gQ_c2 * q_k + gG_c2 * (gamma_r * h_wt + (gamma_r - GAMMA_W) * d_w)) + GAMMA_W * d_w
        p_c2.append(p)

    fig, ax = plt.subplots(figsize=(5, 6))
    ax.plot(p_char, y_arr, 'b-', lw=2, label=f'Characteristic (Ka={Ka_char:.3f})')
    ax.fill_betweenx(y_arr, p_char, alpha=0.10, color='blue')
    ax.plot(p_c2, y_arr, 'r--', lw=1.5, label=f'C2 design (Ka={Ka_c2:.3f})')
    ax.fill_betweenx(y_arr, p_c2, alpha=0.07, color='red')

    if h_wt < H:
        y_wt_diag = H - h_wt
        ax.axhline(y_wt_diag, color='#2980b9', lw=1.2, ls=':', alpha=0.7)
        ax.text(max(p_char) * 0.95, y_wt_diag + 0.05, 'WT',
                color='#2980b9', fontsize=8, ha='right')

    ax.set_xlabel('Horizontal pressure (kPa)', fontsize=9)
    ax.set_ylabel('Height above base (m)', fontsize=9)
    ax.set_title(f'Active Earth Pressure\n(φ\'_k = {phi_k:.0f}°, q_k = {q_k:.0f} kPa)',
                 fontsize=9, fontweight='bold')
    ax.legend(fontsize=7.5)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, H + 0.1)
    ax.set_xlim(left=0)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Streamlit helper: UR cell with colour
# ─────────────────────────────────────────────────────────────────────────────

def _ur_badge(ur: float, passed: bool) -> str:
    colour = "#27ae60" if passed else "#e74c3c"
    label  = "PASS" if passed else "FAIL"
    return f'<span style="color:{colour};font-weight:bold">{ur:.3f} {label}</span>'


def _status(passed: bool) -> str:
    return "✅" if passed else "❌"


# ─────────────────────────────────────────────────────────────────────────────
# Main Streamlit render — called from app.py
# ─────────────────────────────────────────────────────────────────────────────

def render():
    st.title("L-Shape Retaining Wall — Design Checker")
    st.caption(
        "BS EN 1997-1:2004 (EC7 Design Approach 1 — C1 & C2) + UK NA  ·  "
        "BS EN 1992-1-1:2004 (EC2) + UK NA  ·  Per unit length of wall"
    )

    # ── Inputs ──────────────────────────────────────────────────────────────
    with st.expander("Geometry & Material Inputs", expanded=True):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("##### Geometry (m)")
            H_stem   = st.number_input("Stem height H (m)",       0.5,  15.0,  4.0,  0.1,  "%.2f", key="rw_H")
            t_stem   = st.number_input("Stem thickness t_s (m)",  0.1,   2.0,  0.40, 0.05, "%.3f", key="rw_ts")
            L_base   = st.number_input("Base length L_base (m)",  0.5,  20.0,  3.20, 0.05, "%.2f", key="rw_Lb")
            L_toe    = st.number_input("Toe length L_toe (m)",    0.0,  10.0,  0.50, 0.05, "%.2f", key="rw_Lt")
            t_base   = st.number_input("Base thickness t_b (m)",  0.1,   2.0,  0.45, 0.05, "%.3f", key="rw_tb")

        with c2:
            st.markdown("##### Retained Soil")
            phi_k    = st.number_input("φ'_k (°)",              15.0,  45.0,  30.0, 1.0,  "%.1f", key="rw_phi")
            gamma_r  = st.number_input("γ_soil (kN/m³)",        14.0,  23.0,  18.0, 0.5,          key="rw_gr")
            q_k      = st.number_input("Surcharge q_k (kPa)",    0.0, 100.0,  10.0, 1.0,  "%.1f", key="rw_qk",
                                        help="Variable surcharge on retained side (e.g. LM1 equivalent)")
            h_wt     = st.number_input("Water table depth (m)",   0.0, 200.0,  99.0, 0.5,  "%.1f", key="rw_wt",
                                        help="Depth below top of retained fill. Set large (e.g. 99) for fully dry.")
            st.markdown("##### Foundation")
            phi_f_k  = st.number_input("φ'_fnd (°)",            15.0,  45.0,  28.0, 1.0,  "%.1f", key="rw_phif")
            q_Rd     = st.number_input("q_Rd (kPa)",            50.0,5000.0, 250.0,10.0,          key="rw_qRd",
                                        help="Design bearing resistance (from ground investigation)")

        with c3:
            st.markdown("##### Concrete (EC2)")
            gamma_conc = st.number_input("γ_c (kN/m³)",        20.0, 26.0,  25.0,  0.5,          key="rw_gconc")
            f_ck       = st.number_input("f_ck (MPa)",         20.0, 60.0,  32.0,  2.0,          key="rw_fck")
            f_yk       = st.number_input("f_yk (MPa)",        400.0,600.0, 500.0, 10.0,          key="rw_fyk")
            cover_nom  = st.number_input("Nominal cover (mm)", 25.0, 75.0,  50.0,  5.0,          key="rw_cov",
                                          help="Includes Δc_dev per EN 1992-1-1 Cl 4.4.1.3")
            bar_stem   = st.number_input("Stem bar ⌀ (mm)",   10.0, 40.0,  20.0,  2.0,          key="rw_bstem")
            bar_base   = st.number_input("Base bar ⌀ (mm)",   10.0, 40.0,  20.0,  2.0,          key="rw_bbase")

    # ── Derived / validation ─────────────────────────────────────────────────
    L_heel = L_base - L_toe - t_stem
    H_total = H_stem + t_base

    if L_heel < 0.05:
        st.error(f"Heel length = {L_heel:.3f} m (must be ≥ 0.05 m). "
                 "Increase L_base or reduce L_toe / t_stem.")
        return

    col_info = st.columns(4)
    col_info[0].metric("Heel length", f"{L_heel:.2f} m")
    col_info[1].metric("Total height", f"{H_total:.2f} m")
    col_info[2].metric("Ka (char.)", f"{_Ka(phi_k):.3f}")
    col_info[3].metric("Ka C2 design", f"{_Ka(_phi_d(phi_k, 1.25)):.3f}")

    # ── Calculations ─────────────────────────────────────────────────────────
    geo_results = {
        combo: _geo_check(
            combo=combo, pf=PF[combo],
            phi_k=phi_k, gamma_r=gamma_r, q_k=q_k,
            gamma_conc=gamma_conc, phi_f_k=phi_f_k, q_Rd=q_Rd,
            H_stem=H_stem, t_stem=t_stem, L_base=L_base,
            L_toe=L_toe, t_base=t_base, h_wt=h_wt,
        )
        for combo in ("EQU", "C1", "C2")
    }

    str_data = _structural(
        phi_k=phi_k, gamma_r=gamma_r, q_k=q_k,
        gamma_conc=gamma_conc,
        H_stem=H_stem, t_stem=t_stem, L_base=L_base,
        L_toe=L_toe, t_base=t_base, h_wt=h_wt,
        f_ck=f_ck, f_yk=f_yk, cover_nom=cover_nom,
        bar_stem=bar_stem, bar_base=bar_base,
    )

    # ── Overall status banner ────────────────────────────────────────────────
    geo_ok = all(
        r['pass_overturning'] and r['pass_sliding'] and
        r['pass_bearing'] and r['pass_eccentricity']
        for r in geo_results.values()
    )
    str_secs = [s for s in [str_data['sec_stem'],
                             str_data['sec_heel'],
                             str_data['sec_toe']] if s is not None]
    str_ok = all(s['pass_bend'] and s['pass_shear'] for s in str_secs)

    if geo_ok and str_ok:
        st.success("All checks PASS (EC7 geotechnical + EC2 structural)")
    else:
        msgs = []
        if not geo_ok:
            msgs.append("One or more EC7 geotechnical checks FAIL")
        if not str_ok:
            msgs.append("One or more EC2 structural checks FAIL — review reinforcement / section")
        st.error("  ·  ".join(msgs))

    # ── Diagrams ─────────────────────────────────────────────────────────────
    dcol1, dcol2 = st.columns([3, 2])
    with dcol1:
        st.pyplot(_wall_diagram(H_stem, t_stem, L_base, L_toe, t_base,
                                h_wt, q_k, geo_results, str_data),
                  use_container_width=True)
    with dcol2:
        st.pyplot(_pressure_diagram(phi_k, gamma_r, q_k, H_stem, t_base,
                                    h_wt, geo_results, str_data),
                  use_container_width=True)

    # ── EC7 Geotechnical Results ─────────────────────────────────────────────
    with st.expander("EC7 — Geotechnical Stability (Design Approach 1)", expanded=True):
        _render_geo(geo_results)

    # ── EC2 Structural Results ───────────────────────────────────────────────
    with st.expander("EC2 — Structural Design (STR combination)", expanded=True):
        _render_str(str_data)

    # ── Detailed Calculations ────────────────────────────────────────────────
    with st.expander("Detailed Calculations", expanded=False):
        _render_detail(geo_results, str_data, H_stem, t_stem, L_base, L_toe, t_base, L_heel)


# ─────────────────────────────────────────────────────────────────────────────
# Render helpers
# ─────────────────────────────────────────────────────────────────────────────

def _render_geo(geo_results: dict):
    st.markdown(
        "EQU governs overturning · C1 & C2 govern sliding & bearing · "
        "Passive resistance on toe **neglected** (conservative)"
    )

    rows = []
    for combo, r in geo_results.items():
        rows.append({
            "Combination": combo,
            "φ_d (°)":  f"{r['phi_d']:.2f}",
            "Ka":        f"{r['Ka']:.4f}",
            "F_active (kN/m)": f"{r['F_active']:.2f}",
            "OT: M_drv / M_stb": f"{r['M_drv_ot']:.1f} / {r['M_stb_ot']:.1f}",
            "UR_OT":    f"{r['UR_overturning']:.3f}",
            "OT":       _status(r['pass_overturning']),
            "UR_Slide": f"{r['UR_sliding']:.3f}",
            "Slide":    _status(r['pass_sliding']),
            "q_Ed (kPa) / q_Rd": f"{r['q_Ed']:.1f} / {r['q_Rd']:.0f}",
            "UR_Bear":  f"{r['UR_bearing']:.3f}",
            "Bear":     _status(r['pass_bearing']),
            "e (m)":    f"{r['eccentricity']:.3f}",
            "B' (m)":   f"{r['B_eff']:.3f}",
            "Ecc OK":   _status(r['pass_eccentricity']),
        })

    df = pd.DataFrame(rows).set_index("Combination")
    st.dataframe(df, use_container_width=True)

    # Colour-coded UR summary cards
    st.markdown("---")
    cards = st.columns(3)
    checks = [
        ("Overturning (EQU)", geo_results['EQU']['UR_overturning'], geo_results['EQU']['pass_overturning']),
        ("Sliding (worst C1/C2)",
         max(geo_results['C1']['UR_sliding'], geo_results['C2']['UR_sliding']),
         geo_results['C1']['pass_sliding'] and geo_results['C2']['pass_sliding']),
        ("Bearing (worst C1/C2)",
         max(geo_results['C1']['UR_bearing'], geo_results['C2']['UR_bearing']),
         geo_results['C1']['pass_bearing'] and geo_results['C2']['pass_bearing']),
    ]
    for col, (label, ur, ok) in zip(cards, checks):
        colour = "#27ae60" if ok else "#e74c3c"
        col.markdown(
            f"<div style='border:2px solid {colour};border-radius:6px;padding:8px;text-align:center'>"
            f"<b>{label}</b><br>"
            f"<span style='font-size:1.4em;color:{colour}'>{ur:.3f}</span><br>"
            f"<b style='color:{colour}'>{'PASS' if ok else 'FAIL'}</b></div>",
            unsafe_allow_html=True,
        )


def _render_str(str_data: dict):
    secs = [s for s in [str_data['sec_stem'],
                         str_data['sec_heel'],
                         str_data['sec_toe']] if s is not None]
    if not secs:
        st.info("No structural sections to display.")
        return

    st.markdown(
        "STR combination: γ_G = 1.35, γ_Q = 1.50  ·  "
        "f_cd = 0.85 f_ck / 1.50  ·  f_yd = f_yk / 1.15  ·  "
        "Shear check per EC2 Cl 6.2.2 (no shear links)"
    )

    rows = []
    for s in secs:
        rows.append({
            "Section":          s['name'],
            "M_Ed (kNm/m)":     f"{s['M_Ed']:.2f}",
            "V_Ed (kN/m)":      f"{s['V_Ed']:.2f}",
            "h / d (mm)":       f"{s['h_mm']:.0f} / {s['d_mm']:.0f}",
            "K":                f"{s['K']:.4f}",
            "K_lim":            f"{s['K_lim']:.3f}",
            "z (mm)":           f"{s['z_mm']:.1f}",
            "As_req (mm²/m)":   f"{s['As_req']:.0f}",
            "As_min (mm²/m)":   f"{s['As_min']:.0f}",
            "As_design (mm²/m)":f"{s['As_design']:.0f}",
            "UR_bend (K/K_lim)":f"{s['UR_bend']:.3f}",
            "Bend":             _status(s['pass_bend']),
            "VRd,c (kN/m)":     f"{s['VRd_c']:.2f}",
            "UR_shear":         f"{s['UR_shear']:.3f}",
            "Shear":            _status(s['pass_shear']),
            "Tension face":     s['tension_face'],
        })

    df = pd.DataFrame(rows).set_index("Section")
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    cols = st.columns(len(secs))
    for col, s in zip(cols, secs):
        b_ok = s['pass_bend']
        s_ok = s['pass_shear']
        ok   = b_ok and s_ok
        colour = "#27ae60" if ok else "#e74c3c"
        issues = []
        if not b_ok:
            issues.append(f"K={s['K']:.3f} > K_lim — need compression steel or increase section")
        if not s_ok:
            issues.append(f"V_Ed={s['V_Ed']:.1f} > VRd,c={s['VRd_c']:.1f} — shear links required")
        note = "<br>".join(issues) if issues else "OK"
        col.markdown(
            f"<div style='border:2px solid {colour};border-radius:6px;padding:8px'>"
            f"<b>{s['name']}</b><br>"
            f"As_design = <b>{s['As_design']:.0f} mm²/m</b><br>"
            f"Tension: {s['tension_face']}<br>"
            f"<span style='color:{colour}'><b>{'PASS' if ok else 'FAIL'}</b></span>"
            f"{'<br><small>' + note + '</small>' if not ok else ''}"
            f"</div>",
            unsafe_allow_html=True,
        )


def _render_detail(geo_results, str_data,
                   H_stem, t_stem, L_base, L_toe, t_base, L_heel):
    H = H_stem + t_base

    tab_equ, tab_c1, tab_c2, tab_str = st.tabs(["EQU", "GEO C1", "GEO C2", "STR (EC2)"])

    for tab, combo in [(tab_equ, "EQU"), (tab_c1, "C1"), (tab_c2, "C2")]:
        with tab:
            r = geo_results[combo]
            pf = PF[combo]
            if combo == "EQU":
                gG_d = pf['gG_dst']; gG_s = pf['gG_stb']; gQ = pf['gQ']
            else:
                gG_d = pf['gG_unf']; gG_s = pf['gG_fav']; gQ = pf['gQ']

            st.markdown(f"**Partial factors** — γ_G,dst/unf = {gG_d}, γ_G,stb/fav = {gG_s}, γ_Q = {gQ}, γ_φ = {pf['gphi']}")
            st.markdown(f"**Design angle** φ'_d = {r['phi_d']:.2f}° → Ka = {r['Ka']:.4f}")
            st.markdown(f"**Active force** F_a = {r['F_active']:.2f} kN/m at moment arm giving M_a = {r['M_active']:.2f} kNm/m (about toe)")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**OVERTURNING (about toe)**")
                st.markdown(f"""
| Item | Value |
|------|-------|
| M_driving (active) | {r['M_drv_ot']:.2f} kNm/m |
| M_stab (perm. favourable) | {r['M_stb_ot']:.2f} kNm/m |
| W_stem = {r['W_stem']:.2f} kN/m × x = {r['x_stem']:.3f} m | {r['W_stem']*r['x_stem']:.2f} kNm/m |
| W_base = {r['W_base']:.2f} kN/m × x = {r['x_base']:.3f} m | {r['W_base']*r['x_base']:.2f} kNm/m |
| W_soil = {r['W_soil']:.2f} kN/m × x = {r['x_soil']:.3f} m | {r['W_soil']*r['x_soil']:.2f} kNm/m |
| Uplift U_k = {r['U_k']:.2f} kN/m | unfavourable |
| **UR = M_drv / M_stb** | **{r['UR_overturning']:.3f} {'✅' if r['pass_overturning'] else '❌'}** |
""")

            with col2:
                st.markdown("**SLIDING**")
                st.markdown(f"""
| Item | Value |
|------|-------|
| F_driving = | {r['F_active']:.2f} kN/m |
| V_resist = γ_stb×(W_stem+W_base+W_soil)−U | {r['V_resist']:.2f} kN/m |
| δ_d = φ'_fnd,d | {r['phi_f_d']:.2f}° |
| R_sliding = V × tan(δ_d) | {r['R_sliding']:.2f} kN/m |
| Passive on toe | Neglected |
| **UR = F_drv / R** | **{r['UR_sliding']:.3f} {'✅' if r['pass_sliding'] else '❌'}** |
""")

            with col3:
                st.markdown("**BEARING**")
                st.markdown(f"""
| Item | Value |
|------|-------|
| V_Ed = | {r['V_bearing']:.2f} kN/m |
| Resultant x_R from toe | {r['x_resultant']:.3f} m |
| Eccentricity e | {r['eccentricity']:.3f} m |
| B' = L_base − 2e | {r['B_eff']:.3f} m |
| q_Ed = V / B' | {r['q_Ed']:.2f} kPa |
| q_Rd | {r['q_Rd']:.0f} kPa |
| **UR = q_Ed / q_Rd** | **{r['UR_bearing']:.3f} {'✅' if r['pass_bearing'] else '❌'}** |
| Eccentricity check | {'✅' if r['pass_eccentricity'] else '❌ Resultant outside base'} |
""")

    with tab_str:
        sd = str_data
        st.markdown(f"**STR factors** — γ_G = 1.35, γ_Q = 1.50, γ_c = 1.50, γ_s = 1.15, α_cc = 0.85")
        st.markdown(f"**Bearing pressure (STR)** — q_toe = {sd['q_toe_str']:.2f} kPa · q_heel = {sd['q_heel_str']:.2f} kPa "
                    f"(resultant at x={sd['x_R_str']:.3f} m from toe)")
        st.markdown(f"**Total factored V (STR)** = {sd['V_str']:.2f} kN/m")

        for sec in [sd['sec_stem'], sd['sec_heel'], sd['sec_toe']]:
            if sec is None:
                continue
            st.markdown(f"---\n**{sec['name']}**")
            st.markdown(f"""
| Parameter | Value |
|-----------|-------|
| M_Ed | {sec['M_Ed']:.3f} kNm/m |
| V_Ed | {sec['V_Ed']:.3f} kN/m |
| Section h / d | {sec['h_mm']:.0f} / {sec['d_mm']:.1f} mm |
| f_ck / f_cd | {sec['f_cd']*PF['STR']['gc']/PF['STR']['acc']:.0f} / {sec['f_cd']:.2f} MPa |
| f_yk / f_yd | {sec['f_yd']*PF['STR']['gs']:.0f} / {sec['f_yd']:.2f} MPa |
| K = M/(bd²f_ck) | {sec['K']:.5f} |
| K_lim | {sec['K_lim']:.3f} |
| z (lever arm) | {sec['z_mm']:.1f} mm |
| As_req | {sec['As_req']:.0f} mm²/m |
| As_min (Cl. 9.2.1.1) | {sec['As_min']:.0f} mm²/m |
| **As_design** | **{sec['As_design']:.0f} mm²/m** |
| VRd,c (no links) | {sec['VRd_c']:.2f} kN/m |
| UR_bending (K/K_lim) | {sec['UR_bend']:.3f} {'✅' if sec['pass_bend'] else '❌'} |
| UR_shear | {sec['UR_shear']:.3f} {'✅' if sec['pass_shear'] else '❌'} |
| Tension face | {sec['tension_face']} |
""")
