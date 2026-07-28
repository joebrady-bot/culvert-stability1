import matplotlib.pyplot as plt
import streamlit as st
from matplotlib import patches

LAYER_COLORS = ["#D9C8A5", "#C2B280", "#A9906B"]


def _draw_section(B, H, t_w, t_s, cover_layers):
    """Cross-section (transverse cut) of the box culvert with cover layers stacked on top."""
    B_ext = B + 2 * t_w
    H_ext = H + 2 * t_s

    # Figure size is derived from the actual data extent (at a fixed inches-per-metre scale) rather
    # than a hardcoded value, so thick/uneven cover layers can't throw off the aspect ratio and make
    # the fixed-size annotation text collide (see: layers of very unequal thickness squashing labels).
    y_probe = H_ext
    for layer in cover_layers:
        y_probe += layer["t"] / 1000.0
    data_width = (B_ext + 2.6) - (-1.2)
    data_height = (y_probe + 0.3 + len(cover_layers) * 0.3) - (-0.8)

    scale = 1.1  # inches per metre of data
    fig_w, fig_h = data_width * scale, data_height * scale
    longest = max(fig_w, fig_h)
    if longest > 7.5:
        f = 7.5 / longest
        fig_w, fig_h = fig_w * f, fig_h * f
    elif longest < 3.5:
        f = 3.5 / longest
        fig_w, fig_h = fig_w * f, fig_h * f

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor("white")

    # Concrete box: outer profile minus internal void
    ax.add_patch(patches.Rectangle((0, 0), B_ext, H_ext, fc="#BBBBBB", ec="#333333", lw=1.5, zorder=2))
    ax.add_patch(patches.Rectangle((t_w, t_s), B, H, fc="white", ec="#777777", lw=1, zorder=3))

    # Cover layers stacked above the box, drawn to scale (mm -> m)
    y = H_ext
    centers = []
    for layer in cover_layers:
        t_m = layer["t"] / 1000.0
        centers.append((y, t_m))
        y += t_m
    top_of_layers = y

    # Labels get a minimum vertical slot each so thin layers don't collide; connect with a leader line.
    min_label_gap = 0.3
    label_ys = []
    prev = None
    for layer_y, t_m in centers:
        true_center = layer_y + t_m / 2
        label_y = true_center if prev is None else max(true_center, prev + min_label_gap)
        label_ys.append(label_y)
        prev = label_y

    for i, ((layer_y, t_m), label_y) in enumerate(zip(centers, label_ys)):
        ax.add_patch(
            patches.Rectangle((0, layer_y), B_ext, t_m, fc=LAYER_COLORS[i % len(LAYER_COLORS)], ec="#555555", lw=0.8, zorder=2)
        )
        true_center = layer_y + t_m / 2
        ax.plot([B_ext, B_ext + 0.15], [true_center, label_y], color="#999999", lw=0.6, zorder=1)
        ax.annotate(
            f"Layer {i + 1}: t={cover_layers[i]['t']:.0f}mm, γ={cover_layers[i]['gamma']:.1f} kN/m³",
            xy=(B_ext + 0.2, label_y),
            fontsize=7,
            va="center",
            ha="left",
            color="#333333",
        )

    top_of_labels = label_ys[-1] if label_ys else top_of_layers

    # Overall dimensions
    ax.annotate("", xy=(B_ext, -0.25), xytext=(0, -0.25), arrowprops=dict(arrowstyle="<->", color="#333333"))
    ax.text(B_ext / 2, -0.4, f"B_ext = {B_ext:.2f} m", ha="center", fontsize=8, color="#333333")

    ax.annotate("", xy=(-0.25, H_ext), xytext=(-0.25, 0), arrowprops=dict(arrowstyle="<->", color="#333333"))
    ax.text(-0.4, H_ext / 2, f"H_ext = {H_ext:.2f} m", ha="center", va="center", fontsize=8, rotation=90, color="#333333")

    ax.set_xlim(-1.2, B_ext + 2.6)
    ax.set_ylim(-0.8, max(top_of_layers, top_of_labels) + 0.3)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    return fig


def render(inputs):
    """Render box culvert stability calculations and return a dict of computed values."""
    results = {}

    st.subheader("Self-weights")

    B = inputs["B"]
    H = inputs["H"]
    t_w = inputs["t_w"]
    t_s = inputs["t_s"]
    gamma_concrete = inputs["gamma_concrete"]
    cover_layers = inputs["cover_layers"]

    B_ext = B + 2 * t_w
    H_ext = H + 2 * t_s
    A_conc = B_ext * H_ext - B * H
    W_box = A_conc * gamma_concrete

    results["B_ext"] = B_ext
    results["H_ext"] = H_ext
    results["A_conc"] = A_conc
    results["W_box"] = W_box

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Box culvert (per 1 m length)**")
        c1, c2, c3 = st.columns(3)
        c1.metric("B_ext (m)", f"{B_ext:.3f}")
        c2.metric("H_ext (m)", f"{H_ext:.3f}")
        c3.metric("A_conc (m²)", f"{A_conc:.3f}")
        st.write(
            f"A_conc = B_ext × H_ext − B × H = {B_ext:.3f} × {H_ext:.3f} − {B:.3f} × {H:.3f} "
            f"= **{A_conc:.3f} m²**"
        )
        st.write(
            f"W_box = A_conc × gamma_concrete = {A_conc:.3f} × {gamma_concrete:.2f} "
            f"= **{W_box:.2f} kN/m**"
        )

        st.markdown("**Cover layer self-weights (per 1 m length)**")
        layer_udls = []
        for i, layer in enumerate(cover_layers, start=1):
            t_i = layer["t"]
            gamma_i = layer["gamma"]
            UDL_i = gamma_i * (t_i / 1000.0)
            layer_udls.append(UDL_i)
            st.write(
                f"Layer {i}: UDL_{i} = gamma_{i} × (t_{i} / 1000) "
                f"= {gamma_i:.2f} × ({t_i:.1f} / 1000) = **{UDL_i:.2f} kN/m**"
            )

        results["layer_udls"] = layer_udls
        results["UDL_total"] = sum(layer_udls)

        st.write(f"**Total cover UDL = {results['UDL_total']:.2f} kN/m**")
    with right:
        section_fig = _draw_section(B, H, t_w, t_s, cover_layers)
        st.pyplot(section_fig, use_container_width=False)
        plt.close(section_fig)

    st.divider()
    st.subheader("Horizontal Surcharge Model for LM1, LM2 & LM3")

    left2, right2 = st.columns([1, 1])
    with right2:
        st.image("assets/pd6694_table6_surcharge_model.png", use_container_width=True)
        st.image("assets/pd6694_figure2_surcharge_model.png", use_container_width=True)

    return results
