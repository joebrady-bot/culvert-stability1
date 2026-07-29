import base64
import io

import streamlit as st
from PIL import Image

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
    {
        "page": "beam_analysis.py",
        "icon": "📏",
        "title": "Beam Analysis",
        "description": (
            "First-principles shear force and bending moment diagrams for beams on any number "
            "of simple supports, under any combination of point loads and UDLs — single spans "
            "solved by statics, continuous beams by the three-moment theorem."
        ),
    },
]


@st.cache_data
def _logo_data_uri():
    img = Image.open("assets/logo.png").convert("RGBA")
    img.thumbnail((160, 160), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _bridge_svg():
    """Cable-stayed bridge line-art, generated so cable spacing stays tidy if tweaked."""
    pylon_x, pylon_top, deck_y = 600, 55, 330
    deck_x0, deck_x1 = 70, 1130
    cables = []
    # upper fan (from the pylon top) and a lower cross-fan (from partway down), both sides
    for anchor_y, step, opacity in [(pylon_top, 46, 0.55), (150, 40, 0.30)]:
        for side in (-1, 1):
            for i in range(1, 12):
                x = pylon_x + side * i * step
                if deck_x0 + 20 < x < deck_x1 - 20:
                    cables.append(
                        f'<line x1="{pylon_x}" y1="{anchor_y}" x2="{x}" y2="{deck_y}" '
                        f'stroke="url(#cableGrad)" stroke-width="1.6" opacity="{opacity}"/>'
                    )
    cables_svg = "".join(cables)

    return f"""
    <svg viewBox="0 0 1200 400" width="1200" height="400" preserveAspectRatio="xMidYMax meet"
         xmlns="http://www.w3.org/2000/svg" class="bridge-svg">
      <defs>
        <linearGradient id="cableGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#F2A93B"/>
          <stop offset="100%" stop-color="#F2A93B" stop-opacity="0.15"/>
        </linearGradient>
        <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#3A7CA5" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="#3A7CA5" stop-opacity="0"/>
        </linearGradient>
        <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="5" result="blur"/>
          <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <rect x="0" y="{deck_y + 26}" width="1200" height="90" fill="url(#waterGrad)"/>

      {cables_svg}

      <line x1="{pylon_x}" y1="{pylon_top}" x2="{pylon_x}" y2="{deck_y}" stroke="#EDEFF4" stroke-width="7" filter="url(#glow)"/>
      <line x1="{deck_x0}" y1="{deck_y}" x2="{deck_x1}" y2="{deck_y}" stroke="#EDEFF4" stroke-width="5"/>
      <rect x="{deck_x0 - 14}" y="{deck_y}" width="14" height="46" fill="#EDEFF4" opacity="0.85"/>
      <rect x="{deck_x1}" y="{deck_y}" width="14" height="46" fill="#EDEFF4" opacity="0.85"/>
      <circle cx="{pylon_x}" cy="{pylon_top}" r="5" fill="#F2A93B" filter="url(#glow)"/>
    </svg>
    """


def _hero():
    html = f"""
        <style>
        .hero {{
            position: relative;
            overflow: hidden;
            border-radius: 18px;
            background: radial-gradient(ellipse at 50% 20%, #1b2740 0%, #0b1220 70%);
            padding: 2.6rem 2rem 2.2rem 2rem;
            margin-bottom: 1.8rem;
            text-align: center;
        }}
        .hero-brand {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            position: absolute;
            top: 1.2rem;
            left: 1.6rem;
            z-index: 2;
        }}
        .hero-brand img {{ width: 34px; height: 34px; border-radius: 8px; }}
        .hero-brand span {{
            color: #EDEFF4;
            font-weight: 700;
            letter-spacing: 0.02em;
            font-size: 0.95rem;
        }}
        .bridge-svg {{
            position: absolute;
            left: 0; right: 0; bottom: -10px;
            width: 100%; height: auto;
            opacity: 0.9;
            pointer-events: none;
            z-index: 1;
            display: block;
        }}
        .hero-kicker {{
            position: relative;
            z-index: 2;
            color: #F2A93B;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-top: 1.6rem;
        }}
        .hero-title {{
            position: relative;
            z-index: 2;
            color: #F5F6FA;
            font-size: 2.6rem;
            font-weight: 800;
            line-height: 1.15;
            margin: 0.6rem 0 0.7rem 0;
        }}
        .hero-sub {{
            position: relative;
            z-index: 2;
            color: #A9B2C3;
            font-size: 1.02rem;
            max-width: 640px;
            margin: 0 auto 1.6rem auto;
        }}
        .hero-cta {{
            position: relative;
            z-index: 2;
            display: inline-block;
            background: #F2A93B;
            color: #1b1400 !important;
            font-weight: 700;
            padding: 0.6rem 1.4rem;
            border-radius: 999px;
            text-decoration: none !important;
            font-size: 0.92rem;
        }}
        .hero-cta:hover {{ background: #ffbd52; }}
        .hero-spacer {{ height: 170px; }}
        </style>

        <div class="hero">
            <div class="hero-brand">
                <img src="{_logo_data_uri()}"/>
                <span>JOEES</span>
            </div>
            <div class="hero-kicker">Structural calculation sheets</div>
            <div class="hero-title">Engineered to<br/>carry the load</div>
            <div class="hero-sub">
                PD 6694-1, Eurocode 7 &amp; Eurocode 2 calculations for culverts, wing walls and
                beams — built from first principles, checked against the source.
            </div>
            <a class="hero-cta" href="#sheets">Explore the calculation sheets ↓</a>
            {_bridge_svg()}
            <div class="hero-spacer"></div>
        </div>
        """
    # Strip leading whitespace AND blank lines from the whole block. Leading spaces risk being
    # read as a markdown code block; blank lines are worse — CommonMark ends a raw-HTML block at
    # the first blank line, silently dropping everything after it (which was swallowing the SVG
    # content past </defs>).
    flat_html = "\n".join(line.strip() for line in html.split("\n") if line.strip())
    st.markdown(flat_html, unsafe_allow_html=True)


_hero()

st.markdown('<div id="sheets"></div>', unsafe_allow_html=True)
st.subheader("Calculation Sheets")
st.caption("Choose a calculation sheet to open.")

cols = st.columns(3)
for i, tile in enumerate(TILES):
    with cols[i % 3]:
        with st.container(border=True):
            st.subheader(f"{tile['icon']} {tile['title']}")
            st.write(tile["description"])
            st.page_link(tile["page"], label="Open", icon="➡️")
