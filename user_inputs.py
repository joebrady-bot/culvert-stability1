import streamlit as st


def render():
    """Render all user input widgets and return a dict of values keyed by nomenclature symbol (see nomenclature.md)."""
    inputs = {}

    st.subheader("Culvert Geometry")
    c1, c2, c3 = st.columns(3)
    with c1:
        inputs["B"] = st.number_input("Internal Width, B (m)", min_value=0.0, value=2.5, step=0.1)
        inputs["t_w"] = st.number_input("Wall Thickness, t_w (m)", min_value=0.0, value=0.3, step=0.05)
    with c2:
        inputs["H"] = st.number_input("Internal Height, H (m)", min_value=0.0, value=2.0, step=0.1)
        inputs["t_s"] = st.number_input("Slab Thickness, t_s (m)", min_value=0.0, value=0.3, step=0.05)
    with c3:
        inputs["L_L"] = st.number_input("Overall Length, L_L (m)", min_value=0.0, value=10.0, step=0.5)
        inputs["gamma_concrete"] = st.number_input(
            "Concrete Density, gamma_concrete (kN/m3)", min_value=0.0, value=25.0, step=0.5
        )

    st.subheader("Water Table")
    inputs["h_wt"] = st.number_input(
        "Water Table, h_wt (m) — height relative to bottom of culvert", min_value=0.0, value=0.0, step=0.1
    )

    st.subheader("Road Geometry")
    c1, c2 = st.columns(2)
    with c1:
        inputs["w_C"] = st.number_input("Carriageway Width, w_C (m)", min_value=0.0, value=7.3, step=0.1)
    with c2:
        inputs["w_L"] = st.number_input("Lane Width, w_L (m)", min_value=0.0, value=3.65, step=0.1)

    st.subheader("Cover Details")
    n_layers = st.number_input("Number of cover layers", min_value=1, max_value=3, value=1, step=1)
    cover_layers = []
    cols = st.columns(int(n_layers))
    for i, col in enumerate(cols, start=1):
        with col:
            st.markdown(f"**Layer {i}**")
            t_i = st.number_input(f"Thickness, t_{i} (mm)", min_value=0.0, value=100.0, step=10.0, key=f"t_{i}")
            gamma_i = st.number_input(
                f"Unit Weight, gamma_{i} (kN/m3)", min_value=0.0, value=19.0, step=0.5, key=f"gamma_{i}"
            )
            cover_layers.append({"t": t_i, "gamma": gamma_i})
    inputs["cover_layers"] = cover_layers

    st.subheader("Soil Properties")
    c1, c2 = st.columns(2)
    with c1:
        inputs["phi_backfill"] = st.number_input(
            "Backfill Friction Angle, phi_backfill (deg)", min_value=0.0, max_value=45.0, value=30.0, step=1.0
        )
        inputs["gamma_backfill"] = st.number_input(
            "Backfill Density, gamma_backfill (kN/m3)", min_value=0.0, value=19.0, step=0.5
        )
        inputs["H_ob"] = st.number_input("Overburden Depth, H_ob (m)", min_value=0.0, value=0.6, step=0.1)
    with c2:
        inputs["phi_founding"] = st.number_input(
            "Founding Friction Angle, phi_founding (deg)", min_value=0.0, max_value=45.0, value=30.0, step=1.0
        )
        inputs["gamma_founding"] = st.number_input(
            "Founding Density, gamma_founding (kN/m3)", min_value=0.0, value=19.0, step=0.5
        )

    st.subheader("LM3 Vehicle Type")
    inputs["sv_vehicle"] = st.selectbox("SV Vehicle", ["SV80", "SV100", "SV196"])

    return inputs
