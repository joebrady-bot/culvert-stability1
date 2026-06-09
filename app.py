import streamlit as st
import math
import matplotlib.pyplot
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches


st.set_page_config(page_title="Box Culvert Stability", layout="wide")

st.title("Buried Box Culvert — Stability Checker")
st.caption("Per-unit-length · PD6694-1 Annex B Tables B.4, B.5, B.6 · BS EN 1997-1 · No traffic loading")

# ── PD6694-1 Annex B ──────────────────────────────────────────────────────────
# Ka  : design active coefficient — Tables B.4/B.5/B.6 (includes γM · γSd;K = 1.2)
# Kmax: design max coefficient for restrained side — Tables B.4/B.5 (includes γM · γSd;K)
# Kr  : Rankine passive for B.6 sliding resistance — computed from design φ (not tabulated)
#
# EC7 partial factors
#   gG_u / gG_f: unfavourable / favourable on permanent actions
#   g_phi / g_c: on shear strength parameters (resistance side)
LS = {
    "SLS":        {"Ka": 0.33, "Kmax": 0.60, "gG_u": 1.00, "gG_f": 1.00, "g_phi": 1.00, "g_c": 1.00},
    "EQU":        {"Ka": 0.44, "Kmax": 0.60, "gG_u": 1.10, "gG_f": 0.90, "g_phi": 1.25, "g_c": 1.25},
    "STR/GEO C1": {"Ka": 0.40, "Kmax": 0.72, "gG_u": 1.35, "gG_f": 1.00, "g_phi": 1.00, "g_c": 1.00},
    "STR/GEO C2": {"Ka": 0.49, "Kmax": 0.84, "gG_u": 1.00, "gG_f": 1.00, "g_phi": 1.25, "g_c": 1.25},
}
LS_NAMES = list(LS.keys())

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Geometry")
    B   = st.number_input("Internal Width, B (m)",    0.1, 20.0, 2.0,  0.1,  "%.2f")
    H   = st.number_input("Internal Height, H (m)",   0.1, 10.0, 1.5,  0.1,  "%.2f")
    LL  = st.number_input("Overall Length, LL (m)",   0.5, 50.0, 6.0,  0.5,  "%.1f",
                           help="Longitudinal barrel length — used for load dispersion and braking reduction factor η.")
    t_w = st.number_input("Wall Thickness, t_w (m)",  0.05, 2.0, 0.25, 0.05, "%.2f")
    t_s = st.number_input("Slab Thickness, t_s (m)",  0.05, 2.0, 0.30, 0.05, "%.2f")

    st.header("Cover Layers (top to bottom)")
    st.markdown("**Road construction**")
    t_road  = st.number_input("Thickness (m)",       0.0, 2.0,  0.10, 0.01, "%.3f", key="t_road")
    γ_road  = st.number_input("Unit Weight (kN/m³)", 10.0, 30.0, 24.0, 0.5,         key="g_road")
    st.markdown("**Subbase**")
    t_sub   = st.number_input("Thickness (m)",       0.0, 2.0,  0.25, 0.05, "%.3f", key="t_sub")
    γ_sub   = st.number_input("Unit Weight (kN/m³)", 10.0, 25.0, 20.0, 0.5,         key="g_sub")
    st.markdown("**Fill**")
    t_fill  = st.number_input("Thickness (m)",       0.0, 20.0, 0.65, 0.05, "%.3f", key="t_fill")
    γ_fill  = st.number_input("Unit Weight (kN/m³)", 10.0, 25.0, 18.0, 0.5,         key="g_fill")

    st.header("Backfill Properties")
    st.caption("Used for passive (Kr) resistance on culvert walls")
    φ_fill_deg = st.number_input("Friction Angle φ'_fill (°)", 0.0, 45.0, 35.0, 1.0, key="phi_fill")
    c_fill     = st.number_input("Cohesion c'_fill (kPa)",     0.0, 200.0,  0.0, 1.0, key="c_fill")

    st.header("Founding Layer Properties")
    st.caption("Used for base sliding resistance and bearing")
    φ_fnd_deg = st.number_input("Friction Angle φ'_fnd (°)", 0.0, 45.0, 28.0, 1.0, key="phi_fnd")
    c_fnd     = st.number_input("Cohesion c'_fnd (kPa)",     0.0, 200.0,  0.0, 1.0, key="c_fnd")
    q_Rd      = st.number_input(
        "Bearing Resistance q_Rd (kPa)", 50.0, 5000.0, 300.0, 10.0,
        help="Design bearing resistance from ground model (applied uniformly across limit states).")

    st.header("Road Geometry")
    st.caption("Road runs transversely across the culvert (vehicles travel in B_ext direction)")
    cw_width   = st.number_input("Carriageway Width (m)", 1.0, 30.0, 7.30, 0.05, "%.2f", key="cw_width",
                                  help="Total width between kerbs, centred on barrel length LL")
    lane_width = st.number_input("Lane Width (m)",        1.0, 5.0,  3.65, 0.05, "%.2f", key="lane_width",
                                  help="Individual lane width")

    st.header("Water Table")
    h_wt = st.number_input("Depth below GL (m)", 0.0, 30.0, 5.0, 0.1, key="h_wt",
                            help="Set below diagram to hide. Shown as informational only — not yet included in stability calculations.")

    st.header("Material")
    γ_c = st.number_input("Concrete Unit Weight γ_c (kN/m³)", 20.0, 26.0, 24.0, 0.5)

# ── Derived geometry ───────────────────────────────────────────────────────────
B_ext  = B + 2 * t_w
H_ext  = H + 2 * t_s
H_c    = t_road + t_sub + t_fill   # total cover depth to crown
H_inv  = H_c + H_ext

# Road geometry — notional lanes
n_lanes = max(1, int(cw_width / lane_width))

A_conc = B_ext * H_ext - B * H
W_conc = A_conc * γ_c
# Overburden weight: sum of each layer (characteristic, not factored)
W_road = γ_road * t_road * B_ext
W_sub  = γ_sub  * t_sub  * B_ext
W_fill = γ_fill * t_fill * B_ext
W_soil = W_road + W_sub + W_fill
N_v_k  = W_conc + W_soil

φ_fill_k = math.radians(φ_fill_deg)   # backfill — governs Kr passive resistance
φ_fnd_k  = math.radians(φ_fnd_deg)   # founding layer — governs base sliding resistance

γ_w = 9.81  # kN/m³

# Total vertical stresses at crown and invert
σ_top = γ_road * t_road + γ_sub * t_sub + γ_fill * t_fill
σ_bot = σ_top + γ_fill * H_ext

# Pore water pressures at crown and invert (zero above water table)
u_top = γ_w * max(0.0, H_c   - h_wt)
u_bot = γ_w * max(0.0, H_inv - h_wt)

# Effective vertical stresses (used for K·σ'v horizontal earth pressure)
σ_eff_top = max(0.0, σ_top - u_top)
σ_eff_bot = max(0.0, σ_bot - u_bot)

# Characteristic uplift on base per unit length
U_k = u_bot * B_ext

def trapz_resultant(K, σ_t, σ_b, h):
    """Resultant of trapezoidal horizontal pressure K·σ over height h."""
    F   = 0.5 * K * (σ_t + σ_b) * h
    arm = h * (2*σ_t + σ_b) / (3*(σ_t + σ_b)) if (σ_t + σ_b) > 0 else h/3
    return F, arm

# ── Per-limit-state calculations ───────────────────────────────────────────────
def run(p):
    Ka, Kmax   = p["Ka"],   p["Kmax"]
    gG_u, gG_f = p["gG_u"], p["gG_f"]
    g_phi, g_c = p["g_phi"],p["g_c"]

    # Design soil parameters
    φ_fill_d = math.atan(math.tan(φ_fill_k) / g_phi)
    c_fill_d = c_fill / g_c
    φ_fnd_d  = math.atan(math.tan(φ_fnd_k)  / g_phi)
    c_fnd_d  = c_fnd  / g_c
    Kp       = math.tan(math.pi/4 + φ_fill_d/2) ** 2

    # ── B.4 / B.5 — total stresses, no water table effect ───────────────────
    V_u = gG_u * N_v_k
    V_f = gG_f * N_v_k

    F_Ka,   arm_Ka   = trapz_resultant(Ka,   σ_top, σ_bot, H_ext)
    F_Kmax, arm_Kmax = trapz_resultant(Kmax, σ_top, σ_bot, H_ext)
    F_net    = F_Kmax - F_Ka
    M_net_B4 = F_Kmax * arm_Kmax - F_Ka * arm_Ka
    R_fric   = math.tan(φ_fnd_d) * V_f + c_fnd_d * B_ext
    M_stb    = V_f * B_ext / 2

    q_B4       = V_u / B_ext
    UR_B4_bear = q_B4 / q_Rd if q_Rd > 0 else float("inf")
    UR_B4_ov   = M_net_B4 / M_stb if M_stb > 0 else float("inf")
    UR_B4_sl   = F_net / R_fric if R_fric > 0 else float("inf")

    q_B5       = V_f / B_ext
    UR_B5_bear = q_B5 / q_Rd if q_Rd > 0 else float("inf")
    UR_B5_ov   = UR_B4_ov
    UR_B5_sl   = UR_B4_sl

    # ── B.6 — effective stresses and uplift from water table ─────────────────
    V_u_B6 = max(gG_u * N_v_k - gG_f * U_k, 0.0)
    V_f_B6 = max(gG_f * N_v_k - gG_u * U_k, 0.0)

    F_Ka_B6,   arm_Ka_B6 = trapz_resultant(Ka, σ_eff_top, σ_eff_bot, H_ext)
    F_Kr,      arm_Kr     = trapz_resultant(Kp, σ_eff_top, σ_eff_bot, H_ext)
    R_fric_B6  = math.tan(φ_fnd_d) * V_f_B6 + c_fnd_d * B_ext
    M_stb_B6   = V_f_B6 * B_ext / 2
    M_net_B6   = max(0.0, F_Ka_B6 * arm_Ka_B6 - F_Kr * arm_Kr)
    R_B6       = F_Kr + R_fric_B6

    q_B6       = V_f_B6 / B_ext
    UR_B6_bear = q_B6  / q_Rd if q_Rd > 0 else float("inf")
    UR_B6_ov   = M_net_B6 / M_stb_B6 if M_stb_B6 > 0 else float("inf")
    UR_B6_sl   = F_Ka_B6 / R_B6 if R_B6 > 0 else float("inf")

    return dict(
        Ka=Ka, Kmax=Kmax, gG_u=gG_u, gG_f=gG_f, g_phi=g_phi, g_c=g_c,
        V_u=V_u, V_f=V_f, V_u_B6=V_u_B6, V_f_B6=V_f_B6, U_k=U_k,
        u_top=u_top, u_bot=u_bot, σ_eff_top=σ_eff_top, σ_eff_bot=σ_eff_bot,
        φ_fill_d_deg=math.degrees(φ_fill_d), c_fill_d=c_fill_d,
        φ_fnd_d_deg=math.degrees(φ_fnd_d),   c_fnd_d=c_fnd_d,
        F_Ka=F_Ka, F_Ka_B6=F_Ka_B6, F_Kmax=F_Kmax, F_net=F_net,
        arm_Ka=arm_Ka, arm_Ka_B6=arm_Ka_B6, arm_Kmax=arm_Kmax, arm_Kr=arm_Kr,
        Kp=Kp, F_Kr=F_Kr, R_fric=R_fric, R_fric_B6=R_fric_B6, R_B6=R_B6,
        q_B4=q_B4, q_B5=q_B5, q_B6=q_B6,
        M_stb=M_stb, M_stb_B6=M_stb_B6, M_net_B4=M_net_B4, M_net_B6=M_net_B6,
        UR_B4_bear=UR_B4_bear, UR_B4_ov=UR_B4_ov, UR_B4_sl=UR_B4_sl,
        UR_B5_bear=UR_B5_bear, UR_B5_ov=UR_B5_ov, UR_B5_sl=UR_B5_sl,
        UR_B6_bear=UR_B6_bear, UR_B6_ov=UR_B6_ov, UR_B6_sl=UR_B6_sl,
    )

res = {n: run(LS[n]) for n in LS_NAMES}

# ── Shared drawing helper ──────────────────────────────────────────────────────
def dim_arrow(ax, x, y0, y1, label, side="r", fontsize=6.5):
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=0.9))
    dx = 0.08 if side == "r" else -0.08
    ax.text(x + dx, (y0 + y1) / 2, label, fontsize=fontsize, va="center",
            ha="left" if side == "r" else "right")

def h_dim_arrow(ax, x0, x1, y, label, fontsize=6.5):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", color="black", lw=0.9))
    ax.text((x0 + x1) / 2, y + 0.06, label, fontsize=fontsize,
            ha="center", va="bottom")

legend_patches = []
if t_road > 0:
    legend_patches.append(patches.Patch(fc="#404040", label=f"Road ({t_road*1000:.0f} mm)"))
if t_sub > 0:
    legend_patches.append(patches.Patch(fc="#B0B0B0", label=f"Subbase ({t_sub*1000:.0f} mm)"))
legend_patches.append(patches.Patch(fc="#C8A86E", label=f"Fill ({t_fill:.2f} m)"))
legend_patches.append(patches.Patch(fc="#8B7355", label="Founding layer"))

fnd_depth = 0.5   # founding layer depth shown below invert in both diagrams

# ── Layout: diagrams row ───────────────────────────────────────────────────────
col_xs, col_elev = st.columns(2)

# ── Cross-section diagram ──────────────────────────────────────────────────────
with col_xs:
    st.subheader("Cross-Section")
    pad  = max(B_ext * 0.6, 0.8)
    xlim = (-B_ext/2 - pad, B_ext/2 + pad)
    ylim = (-(H_inv + fnd_depth + 0.2), 0.4)

    fig, ax = plt.subplots(figsize=(4, 5))
    ax.set_facecolor("white")

    # Founding layer — sits at base, below invert
    ax.add_patch(patches.Rectangle(
        (xlim[0], -(H_inv + fnd_depth)), xlim[1]-xlim[0], fnd_depth,
        fc="#8A8278", ec="none", zorder=0))
    ax.text(0, -(H_inv + fnd_depth/2), "Founding Layer",
            ha="center", va="center", fontsize=6.5, color="white", fontweight="bold")

    # Fill layer — from invert level up to GL (alongside culvert walls and above)
    ax.add_patch(patches.Rectangle(
        (xlim[0], -H_inv), xlim[1]-xlim[0], H_inv,
        fc="#C8A86E", ec="none", zorder=1))

    # Subbase layer (overwrites fill above)
    if t_sub > 0:
        ax.add_patch(patches.Rectangle(
            (xlim[0], -(t_road + t_sub)), xlim[1]-xlim[0], t_sub,
            fc="#B0B0B0", ec="none", zorder=1))

    # Road construction layer
    if t_road > 0:
        ax.add_patch(patches.Rectangle(
            (xlim[0], -t_road), xlim[1]-xlim[0], t_road,
            fc="#404040", ec="none", zorder=1))

    # Culvert concrete box
    ax.add_patch(patches.Rectangle(
        (-B_ext/2, -H_inv), B_ext, H_ext, fc="#BBBBBB", ec="#333333", lw=2, zorder=3))
    # Internal void
    ax.add_patch(patches.Rectangle(
        (-B/2, -H_inv+t_s), B, H, fc="#F0F8FF", ec="#777777", lw=1, zorder=4))
    ax.axhline(0, color="#3E1E00", lw=2.5, zorder=5)
    ax.text(xlim[1]-0.05, 0.08, "GL", color="#3E1E00", fontsize=8,
            ha="right", va="bottom", fontweight="bold")

    # Water table
    if ylim[0] < -h_wt < ylim[1]:
        ax.axhline(-h_wt, color="#1A6EBD", lw=1.2, ls="--", zorder=6)
        ax.text(xlim[0] + 0.05, -h_wt + 0.05, "▼ WT",
                color="#1A6EBD", fontsize=6.5, va="bottom", fontweight="bold")

    xr = B_ext/2 + 0.22
    xl = -B_ext/2 - 0.22
    if H_c > 0:
        dim_arrow(ax, xr, -H_c, 0, f"Hc={H_c:.2f} m")
    dim_arrow(ax, xr, -H_inv, -H_c, f"Hext={H_ext:.2f} m")
    dim_arrow(ax, xl, -H_inv, 0, f"Hinv={H_inv:.2f} m", "l")
    ax.annotate("", xy=(B_ext/2, -H_inv-0.32), xytext=(-B_ext/2, -H_inv-0.32),
                arrowprops=dict(arrowstyle="<->", color="black", lw=0.9))
    ax.text(0, -H_inv-0.50, f"Bext = {B_ext:.2f} m", ha="center", fontsize=6.5)

    ax.set_xlim(xlim); ax.set_ylim(ylim); ax.set_aspect("equal")
    ax.set_xlabel("(m)", fontsize=8); ax.set_ylabel("Depth below GL (m)", fontsize=8)
    ax.tick_params(labelsize=7); fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()

# ── Longitudinal elevation diagram ────────────────────────────────────────────
with col_elev:
    st.subheader("Longitudinal Section")

    fig_e, ax_e = plt.subplots(figsize=(5, 4))
    ax_e.set_facecolor("white")

    # Founding layer — greyed warm tone, distinct from engineered fill above
    ax_e.add_patch(patches.Rectangle(
        (0, -(H_inv + fnd_depth)), LL, fnd_depth,
        fc="#8A8278", ec="#4A4240", lw=0.8, zorder=0))
    ax_e.text(LL / 2, -(H_inv + fnd_depth / 2), "Founding Layer",
              ha="center", va="center", fontsize=6.5, color="white", fontweight="bold")

    # Fill (full width, from invert up to GL)
    ax_e.add_patch(patches.Rectangle(
        (0, -H_inv), LL, H_inv, fc="#C8A86E", ec="none", zorder=1))

    # Subbase
    if t_sub > 0:
        ax_e.add_patch(patches.Rectangle(
            (0, -(t_road + t_sub)), LL, t_sub, fc="#B0B0B0", ec="none", zorder=2))

    # Road construction
    if t_road > 0:
        ax_e.add_patch(patches.Rectangle(
            (0, -t_road), LL, t_road, fc="#404040", ec="none", zorder=2))

    # Culvert box (top and bottom slab + side walls visible in section)
    # Top slab
    ax_e.add_patch(patches.Rectangle(
        (0, -H_c), LL, t_s, fc="#BBBBBB", ec="#333333", lw=1.2, zorder=3))
    # Bottom slab
    ax_e.add_patch(patches.Rectangle(
        (0, -H_inv), LL, t_s, fc="#BBBBBB", ec="#333333", lw=1.2, zorder=3))
    # Left headwall hint
    ax_e.add_patch(patches.Rectangle(
        (0, -H_inv), t_w, H_ext, fc="#AAAAAA", ec="#333333", lw=1.2, zorder=3))
    # Right headwall hint
    ax_e.add_patch(patches.Rectangle(
        (LL - t_w, -H_inv), t_w, H_ext, fc="#AAAAAA", ec="#333333", lw=1.2, zorder=3))
    # Interior void
    ax_e.add_patch(patches.Rectangle(
        (t_w, -H_inv + t_s), LL - 2*t_w, H, fc="#F0F8FF", ec="#777777", lw=0.8, zorder=4))

    # Carriageway — centred on LL, width = cw_width
    cw_x0    = LL / 2 - cw_width / 2
    cw_x1    = LL / 2 + cw_width / 2
    cw_y_top = 0.22
    kerb_w   = max(0.05, cw_width * 0.015)

    # Road surface
    ax_e.add_patch(patches.Rectangle(
        (cw_x0, 0), cw_width, cw_y_top, fc="#3A3A3A", ec="none", zorder=5))

    # Dashed lane dividers
    for i in range(1, n_lanes):
        x_div = cw_x0 + i * lane_width
        if cw_x0 < x_div < cw_x1:
            ax_e.plot([x_div, x_div], [0, cw_y_top], color="white", lw=0.7, ls="--", zorder=6)

    # Lane labels
    for i in range(n_lanes):
        x_mid = cw_x0 + (i + 0.5) * lane_width
        if cw_x0 < x_mid < cw_x1:
            ax_e.text(x_mid, cw_y_top / 2, f"L{i+1}",
                      ha="center", va="center", fontsize=5, color="white")

    # Kerbs — full height of carriageway strip, at each edge
    for kx in [cw_x0 - kerb_w, cw_x1]:
        ax_e.add_patch(patches.Rectangle(
            (kx, 0), kerb_w, cw_y_top, fc="#888888", ec="#444444", lw=0.5, zorder=7))

    # Width annotation
    ax_e.annotate("", xy=(cw_x1, cw_y_top + 0.07), xytext=(cw_x0, cw_y_top + 0.07),
                  arrowprops=dict(arrowstyle="<->", color="#CCCCCC", lw=0.9))
    ax_e.text(LL / 2, cw_y_top + 0.13,
              f"CW={cw_width:.2f}m  {n_lanes}ln  lw={lane_width:.2f}m",
              ha="center", fontsize=5.5, color="#CCCCCC")

    # GL
    ax_e.axhline(0, color="#3E1E00", lw=2, zorder=5)
    ax_e.text(LL + 0.05, 0.04, "GL", color="#3E1E00", fontsize=7,
              ha="left", va="bottom", fontweight="bold")

    # Water table
    elev_ylim_bot = -(H_inv + fnd_depth + 0.35)
    if elev_ylim_bot < -h_wt < 0.45:
        ax_e.axhline(-h_wt, color="#1A6EBD", lw=1.2, ls="--", zorder=6)
        ax_e.text(-0.05, -h_wt + 0.03, "▼ WT",
                  color="#1A6EBD", fontsize=6, va="bottom", ha="right", fontweight="bold")

    # Dimensions
    xr_e = LL + 0.15
    if H_c > 0:
        dim_arrow(ax_e, xr_e, -H_c, 0,      f"Hc={H_c:.2f}m")
    dim_arrow(ax_e, xr_e, -H_inv, -H_c,     f"Hext={H_ext:.2f}m")
    dim_arrow(ax_e, -0.15, -H_inv, 0,        f"Hinv={H_inv:.2f}m", "l")
    h_dim_arrow(ax_e, 0, LL, -(H_inv + fnd_depth + 0.15), f"LL = {LL:.1f} m")

    ax_e.set_xlim(-0.5, LL + 0.55)
    ax_e.set_ylim(-(H_inv + fnd_depth + 0.35), 0.65)
    ax_e.set_xlabel("Length (m)", fontsize=8)
    ax_e.set_ylabel("Depth below GL (m)", fontsize=8)
    ax_e.tick_params(labelsize=7)
    fig_e.tight_layout()
    st.pyplot(fig_e, use_container_width=True)
    plt.close()

# ── Tables row ─────────────────────────────────────────────────────────────────
col_tbl_l, col_tbl_r = st.columns(2)

with col_tbl_l:
    # ── K-value parameter table ────────────────────────────────────────────────
    st.subheader("Limit State Parameters — PD6694-1 Annex B")
    param_df = pd.DataFrame({
        "Limit State":  LS_NAMES,
        "Ka (active)":  [LS[n]["Ka"]   for n in LS_NAMES],
        "Kmax (restrained)": [LS[n]["Kmax"] for n in LS_NAMES],
        "γG unfav.":    [LS[n]["gG_u"] for n in LS_NAMES],
        "γG fav.":      [LS[n]["gG_f"] for n in LS_NAMES],
        "γφ (resist.)": [LS[n]["g_phi"] for n in LS_NAMES],
    })
    st.dataframe(param_df, hide_index=True, use_container_width=True)

with col_tbl_r:
    # ── Utilisation ratio summary ──────────────────────────────────────────────
    st.subheader("Utilisation Ratios  Ed / Rd  (≤ 1.00 = PASS)")

    def fmt(ur):
        s = f"{ur:.3f}" if ur < 1e6 else "∞"
        return f"{s} {'✅' if ur <= 1.0 else '❌'}"

    rows = [
        ("Bearing",             "B.4 (max V)",   "UR_B4_bear"),
        ("Overturning",         "B.4 / B.5",     "UR_B4_ov"),
        ("Sliding (fric only)", "B.4 / B.5",     "UR_B4_sl"),
        ("Bearing",             "B.5 (min V)",   "UR_B5_bear"),
        ("Bearing",             "B.6 (min V)",   "UR_B6_bear"),
        ("Overturning",         "B.6",           "UR_B6_ov"),
        ("Sliding (fric+Kr)",   "B.6",           "UR_B6_sl"),
    ]
    summary_data = {
        "Check":     [r[0] for r in rows],
        "Case":      [r[1] for r in rows],
        **{n: [fmt(res[n][r[2]]) for r in rows] for n in LS_NAMES},
    }
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)

    # Overall verdict
    all_keys = ("UR_B4_bear", "UR_B4_ov", "UR_B4_sl",
                "UR_B5_bear", "UR_B6_bear", "UR_B6_ov", "UR_B6_sl")
    all_urs = [res[n][k] for n in LS_NAMES for k in all_keys]
    if all(u <= 1.0 for u in all_urs if u < 1e6):
        st.success("**PASS** — All checks satisfied across all four limit states.")
    else:
        fails = []
        check_map = [("Bearing B.4",    "UR_B4_bear"), ("Overturning B.4/B.5", "UR_B4_ov"),
                     ("Sliding B.4/B.5","UR_B4_sl"),   ("Bearing B.5",         "UR_B5_bear"),
                     ("Bearing B.6",    "UR_B6_bear"), ("Overturning B.6",     "UR_B6_ov"),
                     ("Sliding B.6",   "UR_B6_sl")]
        for n in LS_NAMES:
            for label, key in check_map:
                if res[n][key] > 1.0:
                    fails.append(f"{label} [{n}]")
        st.error("**FAIL** — " + " · ".join(fails))

# ── Detailed calculations per limit state ──────────────────────────────────────
st.subheader("Detailed Calculations")
tabs = st.tabs(LS_NAMES)
for tab, name in zip(tabs, LS_NAMES):
    r = res[name]
    with tab:
        st.markdown(f"""
**Limit state parameters** · Ka = {r['Ka']} · Kmax = {r['Kmax']} · γG_u = {r['gG_u']:.2f} · γG_f = {r['gG_f']:.2f} · γφ = {r['g_phi']:.2f}

**Vertical loads** (characteristic N_v_k = {N_v_k:.2f} kN/m)
- V_d unfav. = {r['gG_u']:.2f} × {N_v_k:.2f} = **{r['V_u']:.2f} kN/m**
- V_d fav.   = {r['gG_f']:.2f} × {N_v_k:.2f} = **{r['V_f']:.2f} kN/m**

**Horizontal forces** (σ_top = {σ_top:.2f} kPa · σ_bot = {σ_bot:.2f} kPa)
- F_Ka   = ½ × {r['Ka']} × ({σ_top:.2f}+{σ_bot:.2f}) × {H_ext:.3f} = **{r['F_Ka']:.2f} kN/m** (active side)
- F_Kmax = ½ × {r['Kmax']} × ({σ_top:.2f}+{σ_bot:.2f}) × {H_ext:.3f} = **{r['F_Kmax']:.2f} kN/m** (restrained side)
- **F_net = F_Kmax − F_Ka = {r['F_net']:.2f} kN/m** (B.4/B.5 net driving force)
""")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
**Table B.4 — Max vertical load**

*Bearing*
- q = V_u/B_ext = {r['V_u']:.2f}/{B_ext:.3f} = **{r['q_B4']:.2f} kPa**
- q_Rd = {q_Rd:.1f} kPa → **UR = {r['UR_B4_bear']:.3f}** {"✅" if r["UR_B4_bear"] <= 1.0 else "❌"}

*Overturning*
- M_dst = {r['M_net_B4']:.2f} kN·m/m *(net Kmax−Ka)*
- M_stb = V_f×B/2 = **{r['M_stb']:.2f} kN·m/m**
- **UR = {r['UR_B4_ov']:.3f}** {"✅" if r["UR_B4_ov"] <= 1.0 else "❌"}

*Sliding (friction only)*
- Driving F_net = **{r['F_net']:.2f} kN/m**
- φ_fnd_d = **{r['φ_fnd_d_deg']:.2f}°** · c_fnd_d = **{r['c_fnd_d']:.2f} kPa**
- R_fric = **{r['R_fric']:.2f} kN/m**
- **UR = {r['UR_B4_sl']:.3f}** {"✅" if r["UR_B4_sl"] <= 1.0 else "❌"}
""")

        with c2:
            st.markdown(f"""
**Table B.5 — Min vertical load**

*Bearing*
- q = V_f/B_ext = {r['V_f']:.2f}/{B_ext:.3f} = **{r['q_B5']:.2f} kPa**
- q_Rd = {q_Rd:.1f} kPa → **UR = {r['UR_B5_bear']:.3f}** {"✅" if r["UR_B5_bear"] <= 1.0 else "❌"}

*Overturning*
- M_dst = {r['M_net_B4']:.2f} kN·m/m *(same K as B.4)*
- M_stb = **{r['M_stb']:.2f} kN·m/m**
- **UR = {r['UR_B5_ov']:.3f}** {"✅" if r["UR_B5_ov"] <= 1.0 else "❌"}

*Sliding (friction only)*
- Driving F_net = **{r['F_net']:.2f} kN/m**
- R_fric = **{r['R_fric']:.2f} kN/m**
- **UR = {r['UR_B5_sl']:.3f}** {"✅" if r["UR_B5_sl"] <= 1.0 else "❌"}
""")

        with c3:
            st.markdown(f"""
**Table B.6 — Ka driving / Kr passive (WT: {h_wt:.2f} m BGL)**

*Eff. stresses:* σ'top={r['σ_eff_top']:.2f} kPa, σ'bot={r['σ_eff_bot']:.2f} kPa · Uplift Uk={r['U_k']:.2f} kN/m

*Bearing (min V with uplift)*
- Vf B6 = {r['gG_f']:.2f}×{N_v_k:.2f} − {r['gG_u']:.2f}×{r['U_k']:.2f} = **{r['V_f_B6']:.2f} kN/m**
- q = Vf B6 / Bext = **{r['q_B6']:.2f} kPa** → **UR = {r['UR_B6_bear']:.3f}** {"✅" if r["UR_B6_bear"] <= 1.0 else "❌"}

*Overturning*
- M Ka = {r['F_Ka_B6']:.2f} × {r['arm_Ka_B6']:.3f} = **{r['F_Ka_B6']*r['arm_Ka_B6']:.2f} kNm/m**
- M Kr = {r['F_Kr']:.2f} × {r['arm_Kr']:.3f} = **{r['F_Kr']*r['arm_Kr']:.2f} kNm/m**
- M net = max(0, {r['F_Ka_B6']*r['arm_Ka_B6']:.2f}−{r['F_Kr']*r['arm_Kr']:.2f}) = **{r['M_net_B6']:.2f} kNm/m**
- M stb = {r['V_f_B6']:.2f} × {B_ext/2:.3f} = **{r['M_stb_B6']:.2f} kNm/m**
- **UR = {r['UR_B6_ov']:.3f}** {"✅" if r["UR_B6_ov"] <= 1.0 else "❌"}

*Sliding (friction + passive Kr)*
- F Ka = **{r['F_Ka_B6']:.2f} kN/m** *(eff. stress)*
- φ fill d = **{r['φ_fill_d_deg']:.2f}°** → Kp d = **{r['Kp']:.3f}**
- F Kr = **{r['F_Kr']:.2f} kN/m**
- R fric B6 = tan({r['φ_fnd_d_deg']:.2f}°) × {r['V_f_B6']:.2f} + {r['c_fnd_d']:.2f}×{B_ext:.3f} = **{r['R_fric_B6']:.2f} kN/m**
- R B6 = {r['F_Kr']:.2f}+{r['R_fric_B6']:.2f} = **{r['R_B6']:.2f} kN/m**
- **UR = {r['UR_B6_sl']:.3f}** {"✅" if r["UR_B6_sl"] <= 1.0 else "❌"}
""")

# ── Geometry / assumptions note ────────────────────────────────────────────────
with st.expander("Geometry & assumptions"):
    st.markdown(f"""
| Parameter | Value |
|---|---|
| B_ext | {B:.2f} + 2×{t_w:.2f} = **{B_ext:.3f} m** |
| H_ext | {H:.2f} + 2×{t_s:.2f} = **{H_ext:.3f} m** |
| H_c | {t_road:.3f} + {t_sub:.3f} + {t_fill:.3f} = **{H_c:.3f} m** |
| H_inv | {H_c:.3f} + {H_ext:.3f} = **{H_inv:.3f} m** |
| Concrete area | **{A_conc:.4f} m²/m** |
| W_concrete | **{W_conc:.2f} kN/m** |
| W_road (cover) | {γ_road:.1f} × {t_road:.3f} × {B_ext:.3f} = **{W_road:.2f} kN/m** |
| W_subbase (cover) | {γ_sub:.1f} × {t_sub:.3f} × {B_ext:.3f} = **{W_sub:.2f} kN/m** |
| W_fill (cover) | {γ_fill:.1f} × {t_fill:.3f} × {B_ext:.3f} = **{W_fill:.2f} kN/m** |
| W_soil total | **{W_soil:.2f} kN/m** |
| N_v,k | **{N_v_k:.2f} kN/m** |
| σ_v at crown | {γ_road:.1f}×{t_road:.3f} + {γ_sub:.1f}×{t_sub:.3f} + {γ_fill:.1f}×{t_fill:.3f} = **{σ_top:.2f} kPa** |
| σ_v at invert | {σ_top:.2f} + {γ_fill:.1f}×{H_ext:.3f} = **{σ_bot:.2f} kPa** |

**Load case framework (PD6694-1 Annex B):**
- **B.4** — Maximum vertical load; Ka (active) on one wall, Kmax (restrained) on other → Bearing (primary) + overturning/sliding.
- **B.5** — Minimum vertical load; same Ka/Kmax as B.4 → Overturning and sliding (no traffic: results same as B.4 stability).
- **B.6** — Ka (active) on one wall, Kr (Rankine passive from design φ) on other + base friction → Sliding stability.

**Notes:**
- Ka and Kmax from PD6694-1 Tables B.4/B.5 include γM and γSd;K = 1.2 (Classes 6N/6P backfill assumed).
- Horizontal traffic surcharge omitted (no traffic loading in this analysis).
- Vertical stresses σ_v use characteristic γ (soil unit weight is not a partial-factored load in EC7).
- Kr (passive) computed from design φ_d = arctan(tan φ'_k / γφ); no γSd;K applied to resistance side.
- q_Rd applied uniformly across all limit states — user to verify suitability for each LS.
""")
