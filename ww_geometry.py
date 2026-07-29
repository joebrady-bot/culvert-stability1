import math

import matplotlib.pyplot as plt
import streamlit as st
from matplotlib import patches

GAMMA_W = 9.81  # kN/m3 — unit weight of water


def rankine_ka(phi_deg):
    """Rankine active pressure coefficient — horizontal ground, vertical back of wall."""
    return math.tan(math.radians(45.0 - phi_deg / 2.0)) ** 2


def design_angle(phi_k_deg, gamma_phi):
    return math.degrees(math.atan(math.tan(math.radians(phi_k_deg)) / gamma_phi))


def gamma_eff_backfill(gamma_backfill, H_stem, h_wt_above_stem_base):
    """Average effective (submerged-adjusted) unit weight of the heel soil column, for a water
    table sitting `h_wt_above_stem_base` above the bottom of the stem (top of base slab). The
    submerged zone runs from the bottom of the stem up to the water table; above that, the soil
    is dry."""
    if h_wt_above_stem_base <= 0:
        return gamma_backfill
    h_wet = min(h_wt_above_stem_base, H_stem)
    h_dry = H_stem - h_wet
    return (gamma_backfill * h_dry + (gamma_backfill - GAMMA_W) * h_wet) / H_stem


def active_force_moment(Ka, gamma_soil_fac, q_fac, H, depth_wt):
    """Active horizontal force (kN/m) and moment about the base (kNm/m) of a vertical back plane
    of height H, for a water table `depth_wt` below the top of the retained fill. Below the water
    table, effective (submerged) soil stress is used plus separate hydrostatic pressure — above it,
    total stress. `gamma_soil_fac` and `q_fac` are the already-factored (design) soil unit weight and
    surcharge.
    """
    if depth_wt >= H:
        F_q = Ka * q_fac * H
        F_s = Ka * gamma_soil_fac * H ** 2 / 2.0
        return F_q + F_s, F_q * H / 2.0 + F_s * H / 3.0

    h_dry = depth_wt
    h_wet = H - depth_wt
    gamma_sub = max(gamma_soil_fac - GAMMA_W, 0.0)

    F1 = Ka * q_fac * h_dry
    F2 = Ka * gamma_soil_fac * h_dry ** 2 / 2.0
    M1 = F1 * (h_wet + h_dry / 2.0)
    M2 = F2 * (h_wet + h_dry / 3.0)

    F3 = Ka * (q_fac + gamma_soil_fac * h_dry) * h_wet
    F4 = Ka * gamma_sub * h_wet ** 2 / 2.0
    F5 = GAMMA_W * h_wet ** 2 / 2.0
    M3 = F3 * h_wet / 2.0
    M4 = F4 * h_wet / 3.0
    M5 = F5 * h_wet / 3.0

    return F1 + F2 + F3 + F4 + F5, M1 + M2 + M3 + M4 + M5


def _draw_section(inputs, L_base, H_total):
    H_stem, t_stem, t_base = inputs["H_stem"], inputs["t_stem"], inputs["t_base"]
    L_toe, L_heel = inputs["L_toe"], inputs["L_heel"]
    h_wt, D_emb = inputs["h_wt"], inputs["D_emb"]

    pad = max(L_base * 0.35, 0.6)
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.set_facecolor("white")

    # Founding strata below the base (decorative — bearing level is the base underside, y=0)
    ax.add_patch(patches.Rectangle((-pad, -0.4), L_base + 2 * pad, 0.4,
                                    fc="#8A8278", alpha=0.4, ec="none", zorder=0))
    # Embedment soil in front of the toe, from the base underside up to ground level (D_emb)
    if D_emb > 0:
        ax.add_patch(patches.Rectangle((-pad, 0), L_toe + pad, D_emb,
                                        fc="#B08D57", alpha=0.35, ec="none", zorder=0))

    # Base slab
    ax.add_patch(patches.Rectangle((0, 0), L_base, t_base, fc="#BBBBBB", ec="#333333", lw=1.5, zorder=3))
    # Stem
    ax.add_patch(patches.Rectangle((L_toe, t_base), t_stem, H_stem, fc="#BBBBBB", ec="#333333", lw=1.5, zorder=3))
    # Retained fill (hatched)
    ax.add_patch(patches.Rectangle((L_toe + t_stem, t_base), L_heel, H_stem,
                                    fc="#D9C8A5", ec="#999999", lw=0.5, hatch="///", zorder=1))
    # Ground level in front of toe (D_emb above the base underside)
    ax.plot([-pad, L_toe], [D_emb, D_emb], color="#3E1E00", lw=1.5, zorder=2)
    ax.text(-pad + 0.05, D_emb + 0.05, "GL (front)", fontsize=7, color="#3E1E00")

    # Water table
    if 0 < h_wt < H_total + 1.0:
        ax.axhline(h_wt, color="#1A6EBD", lw=1.2, ls="--", zorder=4)
        ax.text(L_base + pad * 0.5, h_wt + 0.05, "▼ WT", color="#1A6EBD", fontsize=7.5, fontweight="bold")

    # Dimensions
    ax.annotate("", xy=(L_base, -0.35), xytext=(0, -0.35), arrowprops=dict(arrowstyle="<->", color="#333"))
    ax.text(L_base / 2, -0.5, f"L_base = {L_base:.2f} m", ha="center", fontsize=8)
    ax.annotate("", xy=(-pad * 0.6, t_base + H_stem), xytext=(-pad * 0.6, t_base),
                arrowprops=dict(arrowstyle="<->", color="#333"))
    ax.text(-pad * 0.7, t_base + H_stem / 2, f"H_stem = {H_stem:.2f} m", ha="center", va="center",
            rotation=90, fontsize=8)

    ax.text(L_toe / 2, t_base / 2, "toe", ha="center", va="center", fontsize=7.5)
    ax.text(L_toe + t_stem + L_heel / 2, t_base / 2, "heel", ha="center", va="center", fontsize=7.5)
    ax.text(L_toe + t_stem / 2, t_base + H_stem / 2, "stem", ha="center", va="center",
            rotation=90, fontsize=7.5)

    ax.set_xlim(-pad, L_base + pad)
    ax.set_ylim(-0.6, H_total + 0.8)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    return fig


def render(inputs):
    """Render wing wall geometry / self-weight calculations and return a dict of computed values."""
    results = {}

    st.subheader("Geometry & Self-Weights")

    H_stem, t_stem, t_base = inputs["H_stem"], inputs["t_stem"], inputs["t_base"]
    L_toe, L_heel = inputs["L_toe"], inputs["L_heel"]
    gamma_concrete = inputs["gamma_concrete"]
    gamma_backfill = inputs["gamma_backfill"]

    L_base = L_toe + t_stem + L_heel
    H_total = H_stem + t_base

    results["L_base"] = L_base
    results["H_total"] = H_total

    left, right = st.columns([1, 1])
    with left:
        st.write(f"L_base = L_toe + t_stem + L_heel = {L_toe:.2f} + {t_stem:.2f} + {L_heel:.2f} = **{L_base:.2f}m**")
        st.write(f"H_total (stem + base, for earth pressure) = {H_stem:.2f} + {t_base:.2f} = **{H_total:.2f}m**")

        W_stem_k = gamma_concrete * t_stem * H_stem
        W_base_k = gamma_concrete * L_base * t_base
        W_soil_k = gamma_backfill * L_heel * H_stem
        st.write(f"W_stem (characteristic) = gamma_concrete × t_stem × H_stem = {gamma_concrete:.1f} × "
                 f"{t_stem:.2f} × {H_stem:.2f} = **{W_stem_k:.2f}kN/m**")
        st.write(f"W_base (characteristic) = gamma_concrete × L_base × t_base = {gamma_concrete:.1f} × "
                 f"{L_base:.2f} × {t_base:.2f} = **{W_base_k:.2f}kN/m**")
        st.write(f"W_soil (characteristic, heel) = gamma_backfill × L_heel × H_stem = {gamma_backfill:.1f} × "
                 f"{L_heel:.2f} × {H_stem:.2f} = **{W_soil_k:.2f}kN/m**")

        Ka_char = rankine_ka(inputs["phi_backfill"])
        st.write(
            f"Ka (Rankine, characteristic) = tan²(45 − {inputs['phi_backfill']:.0f}/2) = **{Ka_char:.3f}**"
        )
        results["Ka_char"] = Ka_char

    with right:
        fig = _draw_section(inputs, L_base, H_total)
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)

    return results
