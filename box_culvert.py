import streamlit as st


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
    layer_weights = []
    W_layers_total = 0.0
    for i, layer in enumerate(cover_layers, start=1):
        t_i = layer["t"]
        gamma_i = layer["gamma"]
        W_i = gamma_i * (t_i / 1000.0) * B_ext
        W_layers_total += W_i
        layer_weights.append(W_i)
        st.write(
            f"Layer {i}: W_{i} = gamma_{i} × (t_{i} / 1000) × B_ext "
            f"= {gamma_i:.2f} × ({t_i:.1f} / 1000) × {B_ext:.3f} = **{W_i:.2f} kN/m**"
        )

    results["layer_weights"] = layer_weights
    results["W_layers_total"] = W_layers_total

    st.write(f"**Total self-weight (box + cover layers) = {W_box + W_layers_total:.2f} kN/m**")

    return results
