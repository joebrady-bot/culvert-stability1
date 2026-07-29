import streamlit as st

header_logo, header_title = st.columns([1, 6], vertical_alignment="center")
with header_logo:
    st.image("assets/logo.png", width=220)
with header_title:
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
    {
        "page": "wing_wall.py",
        "icon": "🧱",
        "title": "Wing Wall Design",
        "description": (
            "BS EN 1997-1 (EC7) global stability — sliding, overturning and bearing, with an "
            "optional water table — plus BS EN 1992-1-1 (EC2) capacity checks for the stem, heel "
            "and toe of a cantilever wing wall, per UK NA."
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
