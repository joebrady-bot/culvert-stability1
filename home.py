import streamlit as st

st.title("Calculation Sheets")
st.caption("Choose a calculation sheet to open.")

TILES = [
    {
        "page": "culvert_stability.py",
        "icon": "🌉",
        "title": "Culvert Stability",
        "description": (
            "PD 6694-1 Annex B stability checks (sliding, overturning) for buried box culverts "
            "under BS EN 1991-2 LM1 and LM3 traffic loading, including Table B.4/B.5/B.6 water "
            "table cases."
        ),
    },
]

cols = st.columns(3)
for i, tile in enumerate(TILES):
    with cols[i % 3]:
        with st.container(border=True):
            st.subheader(f"{tile['icon']} {tile['title']}")
            st.write(tile["description"])
            st.page_link(tile["page"], label="Open", icon="➡️")
