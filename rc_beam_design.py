"""RC beam design for bending and shear to BS EN 1992-1-1 (Eurocode 2), UK NA.

Follows the procedure in "How to Design Concrete Structures using Eurocode 2: 4. Beams"
(Moss & Brooker, The Concrete Centre) — Figure 2 (flexure) and Figure 5 (vertical shear,
strut inclination method). This is a DESIGN tool (solves for required As / Asw), the
reverse of the capacity checks used in the wing wall sheet (which checked a given As).

`render_inputs()` collects the section/material widgets (call once from the live page —
not safe to replay under pdf_export.capture()). `render()` is pure calculation + st.write
narrative (safe to replay for the PDF export), taking the dict `render_inputs()` returns.
"""

import math

import streamlit as st

ALPHA_CC = 0.85  # UK NA — coefficient for long-term effects on concrete compressive strength
GAMMA_C = 1.5
GAMMA_S = 1.15


def _fctm(fck):
    return 0.30 * fck ** (2.0 / 3.0) if fck <= 50 else 2.12 * math.log(1.0 + (fck + 8.0) / 10.0)


def _v_rd_max(fck, theta_deg):
    """EC2 Cl. 6.2.3 concrete strut capacity (stress) at a given strut angle."""
    return 0.20 * fck * (1.0 - fck / 250.0) * math.sin(2.0 * math.radians(theta_deg))


def _flexure_design(label, M_Ed, b, d, h, fck, fyk, delta, d2):
    """Figure 2 procedure. M_Ed in kNm, b/d/h/d2 in mm, fck/fyk in MPa."""
    st.markdown(f"**{label}**")

    if M_Ed <= 0:
        As_min = max(0.26 * _fctm(fck) * b * d / fyk, 0.0013 * b * d)
        st.write(f"M_Ed = 0 — no flexural reinforcement required from this check. As,min = **{As_min:.0f} mm²**")
        return {"As_req": As_min, "As2_req": 0.0, "compression_steel": False, "ok": True}

    fyd = fyk / GAMMA_S
    K = (M_Ed * 1.0e6) / (b * d ** 2 * fck)
    K_prime = 0.60 * delta - 0.18 * delta ** 2 - 0.21

    st.write(f"K = M_Ed / (b·d²·f_ck) = ({M_Ed:.2f}×10⁶) / ({b:.0f}×{d:.0f}²×{fck:.0f}) = **{K:.4f}**")
    st.write(f"K' = 0.60δ − 0.18δ² − 0.21, δ = {delta:.2f} → K' = **{K_prime:.4f}**")

    if K <= K_prime:
        st.write("K ≤ K' ∴ no compression reinforcement required.")
        z = min(d / 2.0 * (1.0 + math.sqrt(max(1.0 - 3.53 * K, 0.0))), 0.95 * d)
        st.write(f"z = (d/2)[1+√(1−3.53K)] = **{z:.1f} mm** (≤ 0.95d = {0.95 * d:.1f}mm)")
        As_req = (M_Ed * 1.0e6) / (fyd * z)
        st.write(f"As,req = M_Ed / (f_yd·z) = ({M_Ed:.2f}×10⁶) / ({fyd:.1f}×{z:.1f}) = **{As_req:.0f} mm²**")
        As2_req = 0.0
        compression_steel = False
    else:
        st.write("K > K' ∴ compression reinforcement required.")
        z = d / 2.0 * (1.0 + math.sqrt(max(1.0 - 3.53 * K_prime, 0.0)))
        x = (d - z) / 0.4
        st.write(f"z = (d/2)[1+√(1−3.53K')] = **{z:.1f} mm**, x = (d−z)/0.4 = **{x:.1f} mm**")
        fsc = min(700.0 * (x - d2) / x, fyd)
        st.write(f"f_sc = min(700(x−d₂)/x, f_yd) = **{fsc:.1f} MPa**")
        As2_req = (K - K_prime) * fck * b * d ** 2 / (fsc * (d - d2))
        As_req = K_prime * fck * b * d ** 2 / (fyd * z) + As2_req * fsc / fyd
        st.write(f"As2,req (compression) = **{As2_req:.0f} mm²**")
        st.write(f"As,req (tension) = **{As_req:.0f} mm²**")
        compression_steel = True

    As_min = max(0.26 * _fctm(fck) * b * d / fyk, 0.0013 * b * d)
    As_max = 0.04 * b * h
    As_final = max(As_req, As_min)
    st.write(f"As,min = **{As_min:.0f} mm²**, As,max = 0.04·A_c = **{As_max:.0f} mm²**")

    ok = As_final <= As_max
    st.write(
        f"Adopt As = **{As_final:.0f} mm²** {'∴ **OK**.' if ok else '∴ **NOT OK** — exceeds As,max, increase section.'}"
    )
    return {"As_req": As_final, "As2_req": As2_req, "compression_steel": compression_steel, "ok": ok}


def _shear_design(V_Ed, bw, d, fck, fyk):
    """Figure 5 procedure (strut inclination method). V_Ed in kN, bw/d in mm, fck/fyk in MPa."""
    st.markdown("**Vertical shear**")

    z = 0.9 * d
    v_Ed = (V_Ed * 1.0e3) / (bw * z)
    st.write(f"v_Ed = V_Ed / (b_w·z) = V_Ed / (0.9·b_w·d) = ({V_Ed:.2f}×10³) / ({bw:.0f}×{z:.1f}) = **{v_Ed:.3f} MPa**")

    v_rd_max_25 = _v_rd_max(fck, 21.8)  # cotθ = 2.5
    v_rd_max_10 = _v_rd_max(fck, 45.0)  # cotθ = 1.0
    st.write(
        f"v_Rd,max (cotθ=2.5) = 0.20·f_ck·(1−f_ck/250)·sin(2×21.8°) = **{v_rd_max_25:.2f} MPa**; "
        f"v_Rd,max (cotθ=1.0) = **{v_rd_max_10:.2f} MPa**"
    )

    if v_Ed <= v_rd_max_25:
        theta_deg = 21.8
        st.write(f"v_Ed ≤ v_Rd,max(cotθ=2.5) ∴ use the minimum strut angle, θ = **{theta_deg:.1f}°** (cotθ = 2.5).")
        redesign = False
    elif v_Ed <= v_rd_max_10:
        theta_deg = math.degrees(0.5 * math.asin(v_Ed / (0.20 * fck * (1.0 - fck / 250.0))))
        st.write(f"θ = 0.5·sin⁻¹[v_Ed / (0.20·f_ck·(1−f_ck/250))] = **{theta_deg:.1f}°**")
        redesign = False
    else:
        theta_deg = 45.0
        st.write(
            f"v_Ed = {v_Ed:.2f}MPa **exceeds** v_Rd,max(cotθ=1.0) = {v_rd_max_10:.2f}MPa "
            "∴ **section too small for shear — redesign (increase b_w or d).**"
        )
        redesign = True

    cot_theta = 1.0 / math.tan(math.radians(theta_deg))
    fywd = fyk / GAMMA_S
    Asw_s = (v_Ed * bw) / (fywd * cot_theta)  # mm2/mm
    st.write(f"Asw/s = v_Ed·b_w / (f_ywd·cotθ) = **{Asw_s * 1000:.0f} mm²/m**")

    Asw_s_min = 0.08 * math.sqrt(fck) * bw / fyk  # EC2 Cl. 9.2.2, minimum shear reinforcement ratio
    st.write(f"Asw,min/s (Cl. 9.2.2, ρw,min = 0.08√f_ck/f_yk) = **{Asw_s_min * 1000:.0f} mm²/m**")

    Asw_s_final = max(Asw_s, Asw_s_min)
    s_max = 0.75 * d
    st.write(f"Adopt Asw/s = **{Asw_s_final * 1000:.0f} mm²/m**. Maximum spacing s_l,max = 0.75d = **{s_max:.0f} mm**")

    return {"Asw_s": Asw_s_final, "s_max": s_max, "theta_deg": theta_deg, "redesign": redesign}


def _link_spacing(Asw_s, n_legs, link_dia, s_max):
    Asw_per_set = n_legs * math.pi / 4.0 * link_dia ** 2
    s_strength = Asw_per_set / Asw_s if Asw_s > 0 else s_max
    return min(s_strength, s_max)


def render_inputs(beam_results):
    """Section/material widgets + design actions, pre-filled from the beam solver's governing
    values. Not safe to call under pdf_export.capture() — call once from the live page only."""
    inputs = {}

    M_max_default = beam_results.get("M_max", 0.0) if beam_results else 0.0
    M_min_default = beam_results.get("M_min", 0.0) if beam_results else 0.0
    V_max_default = beam_results.get("V_max", 0.0) if beam_results else 0.0

    st.markdown("#### Section & Materials")
    c1, c2, c3 = st.columns(3)
    with c1:
        inputs["b"] = st.number_input("Width, b (mm)", min_value=100.0, value=300.0, step=25.0)
        inputs["h"] = st.number_input("Overall depth, h (mm)", min_value=150.0, value=500.0, step=25.0)
        inputs["cover"] = st.number_input("Nominal cover (mm)", min_value=15.0, value=30.0, step=5.0)
    with c2:
        inputs["bar_dia"] = st.number_input("Main bar diameter (mm)", min_value=8.0, value=20.0, step=2.0)
        inputs["link_dia"] = st.number_input("Link diameter (mm)", min_value=6.0, value=10.0, step=2.0)
        inputs["n_legs"] = st.number_input("Number of link legs", min_value=2, value=2, step=2)
    with c3:
        inputs["fck"] = st.number_input("Concrete strength, f_ck (MPa)", min_value=20.0, value=30.0, step=2.0)
        inputs["fyk"] = st.number_input("Steel yield strength, f_yk (MPa)", min_value=400.0, value=500.0, step=25.0)
        inputs["delta"] = st.number_input(
            "Redistribution ratio, δ", min_value=0.70, max_value=1.00, value=1.00, step=0.05,
            help="Ratio of the redistributed moment to the elastic bending moment (Table 4). 1.0 = no redistribution.",
        )

    st.markdown("#### Design Actions")
    st.caption("Pre-filled from the Results tab's governing values — edit to check a different section.")
    c1, c2, c3 = st.columns(3)
    with c1:
        inputs["M_sag"] = st.number_input(
            "M_Ed, sagging (kNm) — bottom steel", min_value=0.0, value=max(M_max_default, 0.0), step=1.0
        )
    with c2:
        inputs["M_hog"] = st.number_input(
            "M_Ed, hogging (kNm) — top steel", min_value=0.0, value=max(-M_min_default, 0.0), step=1.0
        )
    with c3:
        inputs["V_Ed"] = st.number_input("V_Ed (kN)", min_value=0.0, value=max(V_max_default, 0.0), step=1.0)

    return inputs


def render(rc_inputs):
    """Pure calculation + narrative display — safe to replay under pdf_export.capture()."""
    st.subheader("RC Beam Design (BS EN 1992-1-1)")
    st.write(
        "Designs a rectangular section for the governing sagging/hogging moments and shear — "
        "flexure per Figure 2, shear per Figure 5 (strut inclination method), in *How to Design "
        "Concrete Structures using Eurocode 2: 4. Beams* (Moss & Brooker, The Concrete Centre)."
    )

    b, h = rc_inputs["b"], rc_inputs["h"]
    cover, bar_dia, link_dia, n_legs = rc_inputs["cover"], rc_inputs["bar_dia"], rc_inputs["link_dia"], rc_inputs["n_legs"]
    fck, fyk, delta = rc_inputs["fck"], rc_inputs["fyk"], rc_inputs["delta"]

    d = h - cover - link_dia - bar_dia / 2.0
    d2 = cover + link_dia + bar_dia / 2.0
    st.write(f"Effective depth, d = h − cover − link⌀ − bar⌀/2 = **{d:.1f} mm**")

    st.divider()
    bottom = _flexure_design("Bottom reinforcement (sagging)", rc_inputs["M_sag"], b, d, h, fck, fyk, delta, d2)
    st.divider()
    top = _flexure_design("Top reinforcement (hogging)", rc_inputs["M_hog"], b, d, h, fck, fyk, delta, d2)
    st.divider()
    shear = _shear_design(rc_inputs["V_Ed"], b, d, fck, fyk)

    st.divider()
    st.markdown("#### Suggested Reinforcement")
    n_bars_bottom = math.ceil(bottom["As_req"] / (math.pi / 4.0 * bar_dia ** 2))
    n_bars_top = math.ceil(top["As_req"] / (math.pi / 4.0 * bar_dia ** 2))
    s_link = _link_spacing(shear["Asw_s"], n_legs, link_dia, shear["s_max"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Bottom bars", f"{n_bars_bottom} x H{bar_dia:.0f}")
    c2.metric("Top bars", f"{n_bars_top} x H{bar_dia:.0f}")
    c3.metric("Links", f"H{link_dia:.0f}, {n_legs:.0f} legs @ {s_link:.0f}mm c/c")

    if shear["redesign"]:
        st.write("**Shear: section too small — increase b_w or d.**")
    if not bottom.get("ok", True) or not top.get("ok", True):
        st.write("**Flexure: As,max exceeded — increase section size.**")

    return {"bottom": bottom, "top": top, "shear": shear, "b": b, "h": h, "d": d}
