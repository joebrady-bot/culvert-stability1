import streamlit as st


def render():
    """Render all user input widgets and return a dict of values."""
    inputs = {}

    st.subheader("Spans")
    st.caption("The beam is continuous over all supports — no overhangs beyond the first/last support.")
    n_spans = st.number_input("Number of spans", min_value=1, max_value=6, value=1, step=1)

    span_lengths = []
    cols = st.columns(int(n_spans))
    for i, col in enumerate(cols, start=1):
        with col:
            span_lengths.append(
                st.number_input(f"Span {i} length (m)", min_value=0.1, value=5.0, step=0.5, key=f"span_{i}")
            )
    inputs["span_lengths"] = span_lengths

    supports = [0.0]
    for length in span_lengths:
        supports.append(supports[-1] + length)
    inputs["supports"] = supports
    total_length = supports[-1]
    st.write(f"Total length = **{total_length:.2f} m**, supports at: {', '.join(f'{s:.2f}' for s in supports)} m")

    st.subheader("Point Loads")
    n_point_loads = st.number_input("Number of point loads", min_value=0, max_value=6, value=1, step=1)
    point_loads = []
    if n_point_loads:
        cols = st.columns(int(n_point_loads))
        for i, col in enumerate(cols, start=1):
            with col:
                st.markdown(f"**Load {i}**")
                x = st.number_input(
                    f"Position (m)", min_value=0.0, max_value=total_length,
                    value=min(total_length / 2, total_length), step=0.1, key=f"pl_x_{i}",
                )
                p = st.number_input(f"Magnitude, downward (kN)", value=10.0, step=1.0, key=f"pl_p_{i}")
                point_loads.append((x, p))
    inputs["point_loads"] = point_loads

    st.subheader("UDLs")
    n_udls = st.number_input("Number of UDLs", min_value=0, max_value=4, value=0, step=1)
    udls = []
    if n_udls:
        cols = st.columns(int(n_udls))
        for i, col in enumerate(cols, start=1):
            with col:
                st.markdown(f"**UDL {i}**")
                s = st.number_input(f"Start (m)", min_value=0.0, max_value=total_length, value=0.0, step=0.1, key=f"udl_s_{i}")
                e = st.number_input(f"End (m)", min_value=0.0, max_value=total_length, value=total_length, step=0.1, key=f"udl_e_{i}")
                w = st.number_input(f"Intensity, downward (kN/m)", value=5.0, step=0.5, key=f"udl_w_{i}")
                udls.append((min(s, e), max(s, e), w))
    inputs["udls"] = udls

    return inputs
