import streamlit as st


def render():
    """Render all user input widgets and return a dict of values keyed by symbol."""
    inputs = {}

    st.subheader("Wall Geometry")
    st.caption("Cantilever L-shape wing wall, per 1.0 m length. Retained fill sits on the heel side.")
    c1, c2, c3 = st.columns(3)
    with c1:
        inputs["H_stem"] = st.number_input("Stem Height, H_stem (m)", min_value=0.1, value=3.0, step=0.1)
        inputs["t_stem"] = st.number_input("Stem Thickness, t_stem (m)", min_value=0.1, value=0.3, step=0.05)
    with c2:
        inputs["L_toe"] = st.number_input("Toe Length, L_toe (m)", min_value=0.0, value=0.8, step=0.1)
        inputs["L_heel"] = st.number_input("Heel Length, L_heel (m)", min_value=0.1, value=1.8, step=0.1)
    with c3:
        inputs["t_base"] = st.number_input("Base Thickness, t_base (m)", min_value=0.1, value=0.4, step=0.05)
        inputs["D_emb"] = st.number_input(
            "Embedment in front of toe, D_emb (m)", min_value=0.0, value=0.5, step=0.1,
            help="Depth of ground level in front of the wall above the underside of the base slab — "
            "provides the founding overburden pressure for the bearing check.",
        )

    st.subheader("Water Table")
    inputs["h_wt"] = st.number_input(
        "Water Table, h_wt (m) — height relative to underside of base slab",
        min_value=0.0, value=0.0, step=0.1,
    )

    st.subheader("Surcharge")
    inputs["q_surcharge"] = st.number_input(
        "Live Load Surcharge, q_surcharge (kPa)", min_value=0.0, value=10.0, step=1.0,
        help="Simple uniform highway surcharge behind the wall (UK convention, BD 30/87 Cl. 3.4 = 10 kN/m²).",
    )

    st.subheader("Soil Properties")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Retained (backfill)**")
        inputs["phi_backfill"] = st.number_input(
            "Friction Angle, phi_backfill (deg)", min_value=0.0, max_value=45.0, value=35.0, step=1.0
        )
        inputs["gamma_backfill"] = st.number_input(
            "Unit Weight, gamma_backfill (kN/m3)", min_value=0.0, value=19.0, step=0.5
        )
    with c2:
        st.markdown("**Founding**")
        inputs["phi_founding"] = st.number_input(
            "Friction Angle, phi_founding (deg)", min_value=0.0, max_value=45.0, value=30.0, step=1.0
        )
        inputs["gamma_founding"] = st.number_input(
            "Unit Weight, gamma_founding (kN/m3)", min_value=0.0, value=19.0, step=0.5
        )
        inputs["c_founding"] = st.number_input(
            "Cohesion, c_founding (kPa)", min_value=0.0, value=0.0, step=1.0
        )

    st.subheader("Concrete & Reinforcement")
    c1, c2 = st.columns(2)
    with c1:
        inputs["gamma_concrete"] = st.number_input(
            "Concrete Unit Weight, gamma_concrete (kN/m3)", min_value=0.0, value=25.0, step=0.5
        )
        inputs["f_ck"] = st.number_input("Concrete Strength, f_ck (MPa)", min_value=20.0, value=32.0, step=2.0)
        inputs["f_yk"] = st.number_input("Steel Yield Strength, f_yk (MPa)", min_value=400.0, value=500.0, step=25.0)
        inputs["cover"] = st.number_input("Nominal Cover, cover (mm)", min_value=20.0, value=50.0, step=5.0)
    with c2:
        st.markdown("**Reinforcement provided (bar diameter / spacing)**")
        s1, s2 = st.columns(2)
        with s1:
            inputs["stem_bar_dia"] = st.number_input("Stem bar dia. (mm)", min_value=8.0, value=20.0, step=2.0)
            inputs["heel_bar_dia"] = st.number_input("Heel bar dia. (mm)", min_value=8.0, value=16.0, step=2.0)
            inputs["toe_bar_dia"] = st.number_input("Toe bar dia. (mm)", min_value=8.0, value=16.0, step=2.0)
        with s2:
            inputs["stem_bar_spacing"] = st.number_input("Stem spacing (mm)", min_value=50.0, value=150.0, step=25.0)
            inputs["heel_bar_spacing"] = st.number_input("Heel spacing (mm)", min_value=50.0, value=150.0, step=25.0)
            inputs["toe_bar_spacing"] = st.number_input("Toe spacing (mm)", min_value=50.0, value=150.0, step=25.0)

    return inputs
