import math

import streamlit as st

# BS EN 1991-2 Table 4.2 characteristic values (fixed by the code, not the UK NA)
LANE_Q_TS_CHAR = {1: 300.0, 2: 200.0, 3: 100.0}   # kN, tandem axle load per lane
LANE_Q_UDL_CHAR = {1: 9.0, 2: 2.5, 3: 2.5}        # kN/m^2, characteristic UDL per lane

# UK NA adjustment factors alpha_qi (matches the D. Childs worked example). Lane 3+ assumed
# equal to the "remaining area" factor alpha_qr — not shown in the worked example, confirm if
# a 3rd lane is ever loaded (current default carriageway width only loads 2 lanes).
LANE_ALPHA_Q_UDL = {1: 0.61, 2: 2.2, 3: 2.2}
REMAINING_ALPHA_QR = 2.2
REMAINING_QRK = 2.5

NOTIONAL_LANE_WIDTH = 3.0   # m, BS EN 1991-2 4.2.3 standard notional lane width
WHEEL_SPACING = 2.0         # m, transverse wheel-to-wheel spacing within one TS axle (L_L direction)
CONTACT_PATCH = 400.0       # mm, standard square wheel contact patch (400x400)
TAN_30 = math.tan(math.radians(30))


def render(inputs, box_culvert_results):
    """Render BS EN 1991-2 / PD6694-1 LM1 traffic loading calculations and return computed values."""
    results = {}

    st.subheader("Vertical Load on Top of Culvert")

    w_C = inputs["w_C"]
    H_c = box_culvert_results["H_c"]   # m, reuse the cover depth already computed in Global Calculations

    st.markdown("**Notional Lanes**")
    n1 = int(w_C // NOTIONAL_LANE_WIDTH)
    remaining_width = w_C - n1 * NOTIONAL_LANE_WIDTH
    st.write(f"Number of notional lanes = n1 = Int(w_C / 3) = Int({w_C:.2f} / 3) = **{n1}**")
    st.write(f"Notional Lane Width = **{NOTIONAL_LANE_WIDTH:.1f} m**")
    st.write(
        f"Width of remaining area = w_C − n1 × 3.0 = {w_C:.2f} − {n1} × 3.0 = **{remaining_width:.2f} m**"
    )

    st.markdown("**UDL & TS per Lane**")
    lane_udls = {}
    lane_ts = {}
    for i in range(1, n1 + 1):
        if i in LANE_ALPHA_Q_UDL:
            alpha, qk, alpha_sym = LANE_ALPHA_Q_UDL[i], LANE_Q_UDL_CHAR[i], f"alpha_q{i}"
        else:
            alpha, qk, alpha_sym = REMAINING_ALPHA_QR, REMAINING_QRK, "alpha_qr"
        udl = alpha * qk
        lane_udls[i] = udl
        st.write(f"UDL in Lane {i} = {alpha_sym} × q{i}k = {alpha:.2f} × {qk:.1f} = **{udl:.2f} kN/m²**")

    for i in range(1, n1 + 1):
        Qk = LANE_Q_TS_CHAR.get(i, 0.0)
        lane_ts[i] = Qk
        st.write(f"TS in Lane {i} = Q{i}k = **{Qk:.0f} kN**")

    st.markdown("**Contact Patch & Dispersal Through Fill**")
    st.write(f"Contact patch area = {CONTACT_PATCH:.0f} × {CONTACT_PATCH:.0f} mm")
    H_c_mm = H_c * 1000
    disp_mm = CONTACT_PATCH + 2 * H_c_mm * TAN_30
    st.write(
        f"Dispersed area on top of box = {CONTACT_PATCH:.0f} + 2 × {H_c_mm:.0f} × tan30° "
        f"= {CONTACT_PATCH:.0f} + 2 × {H_c_mm:.0f} × {TAN_30:.4f} = **{disp_mm:.0f} × {disp_mm:.0f} mm**"
    )
    disp_m = disp_mm / 1000.0

    st.markdown("**Transverse Dispersal**")
    if n1 >= 2:
        W1 = lane_ts[1] / 2.0
        W2 = lane_ts[2] / 2.0
        gap_12 = NOTIONAL_LANE_WIDTH - WHEEL_SPACING
        a_overlap = max(disp_m - gap_12, 0.0)
        F_transverse_1m = 1.0 * W1 / disp_m + a_overlap * W2 / disp_m
        st.write(
            f"Load per metre where dispersion zones overlap = b·W1/L1 + a·W2/L2 = 1 × {W1:.0f}/{disp_m:.3f} "
            f"+ ({disp_m:.3f} − {gap_12:.1f}) × {W2:.0f}/{disp_m:.3f} = **{F_transverse_1m:.1f} kN/m**"
        )
    else:
        W1 = lane_ts.get(1, 0.0) / 2.0
        F_transverse_1m = W1 / disp_m if disp_m > 0 else 0.0
        st.write(
            f"Only one lane loaded — no adjacent-lane overlap. Load per metre = W1/L1 = {W1:.0f}/{disp_m:.3f} "
            f"= **{F_transverse_1m:.1f} kN/m**"
        )

    st.markdown("**Longitudinal Dispersal**")
    st.write(f"Dispersal zone width for each axle = **{disp_m:.3f} m**")
    patch_load = F_transverse_1m / disp_m if disp_m > 0 else 0.0
    st.write(
        f"Patch load for each axle = {F_transverse_1m:.1f} / {disp_m:.3f} = **{patch_load:.1f} kN/m**"
    )

    results["n1"] = n1
    results["remaining_width"] = remaining_width
    results["lane_udls"] = lane_udls
    results["lane_ts"] = lane_ts
    results["disp_m"] = disp_m
    results["F_transverse_1m"] = F_transverse_1m
    results["patch_load"] = patch_load

    return results
