import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib import patches

import beam_solver


def _draw_schematic(ax, supports, point_loads, udls, total_length):
    pad = max(total_length * 0.06, 0.2)
    tri_h = max(total_length * 0.035, 0.1)
    tri_w = tri_h * 1.4
    arrow_h = max(total_length * 0.12, 0.3)

    ax.axhline(0, color="#333333", lw=2.5, zorder=3)

    for s in supports:
        ax.add_patch(patches.Polygon(
            [(s - tri_w / 2, -tri_h), (s + tri_w / 2, -tri_h), (s, 0)],
            closed=True, fc="#8899AA", ec="#333333", lw=1, zorder=3,
        ))

    for x, p in point_loads:
        ax.annotate(
            "", xy=(x, 0.02), xytext=(x, arrow_h),
            arrowprops=dict(arrowstyle="-|>", color="#C0392B", lw=1.8),
            zorder=4,
        )
        ax.text(x, arrow_h + 0.03 * total_length, f"{p:.1f} kN", ha="center", va="bottom",
                fontsize=8, color="#C0392B")

    for s, e, w in udls:
        udl_h = arrow_h * 0.6
        ax.add_patch(patches.Rectangle(
            (s, 0), e - s, udl_h, fc="#C0392B", alpha=0.15, ec="#C0392B", lw=1, zorder=2,
        ))
        n_arrows = max(int((e - s) / max(total_length * 0.08, 0.3)), 2)
        for xa in [s + (e - s) * k / (n_arrows - 1) for k in range(n_arrows)]:
            ax.annotate(
                "", xy=(xa, 0.02), xytext=(xa, udl_h),
                arrowprops=dict(arrowstyle="-|>", color="#C0392B", lw=1.2),
                zorder=2,
            )
        ax.text((s + e) / 2, udl_h + 0.03 * total_length, f"{w:.2f} kN/m", ha="center", va="bottom",
                fontsize=8, color="#C0392B")

    ax.set_xlim(-pad, total_length + pad)
    ax.set_ylim(-tri_h * 2.5, arrow_h * 1.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Beam, Supports & Loads", fontsize=10, fontweight="bold")


def _plot_sfd_bmd(x, V, M, total_length):
    fig, (ax_v, ax_m) = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)

    ax_v.axhline(0, color="#333", lw=1)
    ax_v.fill_between(x, V, 0, color="#2E86C1", alpha=0.25)
    ax_v.plot(x, V, color="#2E86C1", lw=1.5)
    ax_v.set_ylabel("Shear V (kN)")
    ax_v.set_title("Shear Force Diagram", fontsize=10, fontweight="bold")
    ax_v.grid(alpha=0.3)

    ax_m.axhline(0, color="#333", lw=1)
    ax_m.fill_between(x, M, 0, color="#CB4335", alpha=0.25)
    ax_m.plot(x, M, color="#CB4335", lw=1.5)
    ax_m.invert_yaxis()  # sagging (positive) plotted downward — matches convention in the reference tables
    ax_m.set_ylabel("Moment M (kNm)")
    ax_m.set_xlabel("Distance along beam, x (m)")
    ax_m.set_title("Bending Moment Diagram (sagging plotted downward)", fontsize=10, fontweight="bold")
    ax_m.grid(alpha=0.3)

    fig.tight_layout()
    return fig


def render(inputs):
    """Solve the beam and render the schematic, SFD/BMD, and a results table."""
    results = {}

    supports = inputs["supports"]
    point_loads = inputs["point_loads"]
    udls = inputs["udls"]
    total_length = supports[-1]

    if len(supports) < 2 or total_length <= 0:
        st.warning("Add at least one span to analyse the beam.")
        return results

    r = beam_solver.solve_beam(supports, point_loads, udls)
    results.update(r)

    st.subheader("Beam Schematic")
    fig1, ax1 = plt.subplots(figsize=(9, 2.6))
    _draw_schematic(ax1, supports, point_loads, udls, total_length)
    st.pyplot(fig1, use_container_width=True)
    plt.close(fig1)

    st.subheader("Shear Force & Bending Moment Diagrams")
    fig2 = _plot_sfd_bmd(r["x"], r["V"], r["M"], total_length)
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    st.subheader("Results")
    rows = []
    for i, (s, R) in enumerate(zip(supports, r["reactions"]), start=1):
        rows.append({"Support": f"R{i} (at x={s:.2f}m)", "Reaction (kN)": f"{R:.2f}"})
    st.table(pd.DataFrame(rows).set_index("Support"))

    c1, c2, c3 = st.columns(3)
    c1.metric("V_max (kN)", f"{r['V_max']:.2f}")
    c2.metric("M_max, sagging (kNm)", f"{r['M_max']:.2f}", help=f"at x = {r['x_of_Mmax']:.2f} m")
    c3.metric("M_min, hogging (kNm)", f"{r['M_min']:.2f}", help=f"at x = {r['x_of_Mmin']:.2f} m")

    st.write(
        f"Maximum sagging moment = **{r['M_max']:.2f} kNm** at x = {r['x_of_Mmax']:.2f} m. "
        f"Maximum hogging moment = **{r['M_min']:.2f} kNm** at x = {r['x_of_Mmin']:.2f} m. "
        f"Maximum shear = **{r['V_max']:.2f} kN**."
    )

    if len(supports) > 2:
        st.write("Support moments (at each support, sagging positive):")
        st.write(", ".join(f"M{i+1} = {m:.2f} kNm" for i, m in enumerate(r["support_moments"])))

    return results
