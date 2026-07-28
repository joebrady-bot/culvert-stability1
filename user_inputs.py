import streamlit as st

import _dev_cache  # TEMP (build/setup phase only) — remove this import + the two call sites below to drop persistence


def render():
    """Render all user input widgets and return a dict of values keyed by nomenclature symbol (see nomenclature.md)."""
    inputs = {}
    _cached = _dev_cache.load()  # TEMP — re-read every rerun; Streamlit keeps the process alive across page refreshes

    st.subheader("Culvert Geometry")
    c1, c2, c3 = st.columns(3)
    with c1:
        inputs["B"] = st.number_input("Internal Width, B (m)", min_value=0.0, value=_cached.get("B", 2.5), step=0.1)
        inputs["t_w"] = st.number_input("Wall Thickness, t_w (m)", min_value=0.0, value=_cached.get("t_w", 0.3), step=0.05)
    with c2:
        inputs["H"] = st.number_input("Internal Height, H (m)", min_value=0.0, value=_cached.get("H", 2.0), step=0.1)
        inputs["t_s"] = st.number_input("Slab Thickness, t_s (m)", min_value=0.0, value=_cached.get("t_s", 0.3), step=0.05)
    with c3:
        inputs["L_L"] = st.number_input("Overall Length, L_L (m)", min_value=0.0, value=_cached.get("L_L", 10.0), step=0.5)
        inputs["gamma_concrete"] = st.number_input(
            "Concrete Density, gamma_concrete (kN/m3)", min_value=0.0, value=_cached.get("gamma_concrete", 25.0), step=0.5
        )

    st.subheader("Water Table")
    inputs["h_wt"] = st.number_input(
        "Water Table, h_wt (m) — height relative to bottom of culvert",
        min_value=0.0, value=_cached.get("h_wt", 0.0), step=0.1
    )

    st.subheader("Road Geometry")
    c1, c2 = st.columns(2)
    with c1:
        inputs["w_C"] = st.number_input("Carriageway Width, w_C (m)", min_value=0.0, value=_cached.get("w_C", 7.3), step=0.1)
    with c2:
        inputs["w_L"] = st.number_input("Lane Width, w_L (m)", min_value=0.0, value=_cached.get("w_L", 3.65), step=0.1)

    st.subheader("Cover Details")
    cached_layers = _cached.get("cover_layers", [])
    n_layers = st.number_input(
        "Number of cover layers", min_value=1, max_value=3,
        value=_cached.get("n_layers", max(len(cached_layers), 1)), step=1
    )
    cover_layers = []
    cols = st.columns(int(n_layers))
    for i, col in enumerate(cols, start=1):
        with col:
            st.markdown(f"**Layer {i}**")
            cached_layer = cached_layers[i - 1] if i - 1 < len(cached_layers) else {}
            t_i = st.number_input(
                f"Thickness, t_{i} (mm)", min_value=0.0, value=cached_layer.get("t", 100.0), step=10.0, key=f"t_{i}"
            )
            gamma_i = st.number_input(
                f"Unit Weight, gamma_{i} (kN/m3)", min_value=0.0, value=cached_layer.get("gamma", 19.0), step=0.5, key=f"gamma_{i}"
            )
            cover_layers.append({"t": t_i, "gamma": gamma_i})
    inputs["cover_layers"] = cover_layers

    st.subheader("Soil Properties")
    c1, c2 = st.columns(2)
    with c1:
        inputs["phi_backfill"] = st.number_input(
            "Backfill Friction Angle, phi_backfill (deg)", min_value=0.0, max_value=45.0,
            value=_cached.get("phi_backfill", 30.0), step=1.0
        )
        inputs["gamma_backfill"] = st.number_input(
            "Backfill Density, gamma_backfill (kN/m3)", min_value=0.0, value=_cached.get("gamma_backfill", 19.0), step=0.5
        )
        inputs["H_ob"] = st.number_input("Overburden Depth, H_ob (m)", min_value=0.0, value=_cached.get("H_ob", 0.6), step=0.1)
    with c2:
        inputs["phi_founding"] = st.number_input(
            "Founding Friction Angle, phi_founding (deg)", min_value=0.0, max_value=45.0,
            value=_cached.get("phi_founding", 30.0), step=1.0
        )
        inputs["gamma_founding"] = st.number_input(
            "Founding Density, gamma_founding (kN/m3)", min_value=0.0, value=_cached.get("gamma_founding", 19.0), step=0.5
        )

    st.subheader("LM3 Vehicle Type")
    sv_options = ["SV80", "SV100", "SV196"]
    cached_sv = _cached.get("sv_vehicle", "SV80")
    inputs["sv_vehicle"] = st.selectbox(
        "SV Vehicle", sv_options, index=sv_options.index(cached_sv) if cached_sv in sv_options else 0
    )

    _dev_cache.save({**inputs, "n_layers": int(n_layers)})  # TEMP

    return inputs
