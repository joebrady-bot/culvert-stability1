import contextlib
import datetime
import io
import re

import matplotlib
import pandas as pd
import streamlit as st
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, Image as RLImage, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

import assumptions
import box_culvert
import lm1_calculations
import lm3_calculations
import summary
import table_b4
import table_b5
import table_b6

MAX_IMG_WIDTH = 160 * mm
MAX_IMG_HEIGHT = 230 * mm

# (inputs dict key, PDF label, format spec) — mirrors the widgets in user_inputs.py
INPUT_FIELDS = [
    ("B", "Internal Width, B (m)", "{:.2f}"),
    ("H", "Internal Height, H (m)", "{:.2f}"),
    ("t_w", "Wall Thickness, t_w (m)", "{:.2f}"),
    ("t_s", "Slab Thickness, t_s (m)", "{:.2f}"),
    ("L_L", "Overall Length, L_L (m)", "{:.1f}"),
    ("gamma_concrete", "Concrete Density, gamma_concrete (kN/m3)", "{:.1f}"),
    ("h_wt", "Water Table, h_wt (m) — height relative to bottom of culvert", "{:.2f}"),
    ("w_C", "Carriageway Width, w_C (m)", "{:.2f}"),
    ("w_L", "Lane Width, w_L (m)", "{:.2f}"),
    ("phi_backfill", "Backfill Friction Angle, phi_backfill (deg)", "{:.1f}"),
    ("gamma_backfill", "Backfill Density, gamma_backfill (kN/m3)", "{:.1f}"),
    ("H_ob", "Overburden Depth, H_ob (m)", "{:.2f}"),
    ("phi_founding", "Founding Friction Angle, phi_founding (deg)", "{:.1f}"),
    ("gamma_founding", "Founding Density, gamma_founding (kN/m3)", "{:.1f}"),
    ("sv_vehicle", "LM3 SV Vehicle", "{}"),
]


class _FakeColumn:
    """Stand-in for a Streamlit DeltaGenerator column — supports `with col:` and `col.metric(...)`,
    both of which just forward to the same recorder so content ends up in one flat block list."""

    def __init__(self, recorder):
        self._recorder = recorder

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def metric(self, label, value, *args, **kwargs):
        self._recorder.blocks.append(("metric", (label, value)))

    def write(self, text, *args, **kwargs):
        self._recorder.write(text)

    def markdown(self, text, *args, **kwargs):
        self._recorder.markdown(text)

    def image(self, image, *args, **kwargs):
        self._recorder.image(image)


class _Recorder:
    """Drop-in replacement for the handful of `st.*` functions the calc modules call, recording
    each call as a block instead of drawing it — so the same render() functions used for the live
    app can be re-run to build a PDF, with no changes to any calculation module."""

    def __init__(self):
        self.blocks = []

    def write(self, text, *args, **kwargs):
        self.blocks.append(("write", str(text)))

    def markdown(self, text, *args, **kwargs):
        self.blocks.append(("markdown", str(text)))

    def subheader(self, text, *args, **kwargs):
        self.blocks.append(("subheader", str(text)))

    def caption(self, text, *args, **kwargs):
        self.blocks.append(("caption", str(text)))

    def divider(self, *args, **kwargs):
        self.blocks.append(("divider", None))

    def image(self, image, *args, **kwargs):
        self.blocks.append(("image", image))

    def table(self, data, *args, **kwargs):
        self.blocks.append(("table", data))

    def pyplot(self, fig=None, *args, **kwargs):
        target = fig if fig is not None else matplotlib.pyplot.gcf()
        buf = io.BytesIO()
        target.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        self.blocks.append(("image_bytes", buf.getvalue()))

    def columns(self, spec, *args, **kwargs):
        n = len(spec) if isinstance(spec, (list, tuple)) else spec
        return tuple(_FakeColumn(self) for _ in range(n))


_PATCHED = ["write", "markdown", "subheader", "caption", "divider", "image", "table", "pyplot", "columns"]


@contextlib.contextmanager
def _capture():
    recorder = _Recorder()
    originals = {name: getattr(st, name) for name in _PATCHED}
    for name in _PATCHED:
        setattr(st, name, getattr(recorder, name))
    try:
        yield recorder
    finally:
        for name, fn in originals.items():
            setattr(st, name, fn)


def _register_fonts():
    if "DejaVuSans" in pdfmetrics.getRegisteredFontNames():
        return
    base = matplotlib.get_data_path() + "/fonts/ttf"
    pdfmetrics.registerFont(TTFont("DejaVuSans", f"{base}/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", f"{base}/DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", f"{base}/DejaVuSans-Oblique.ttf"))


def _styles():
    return {
        "Title": ParagraphStyle("Title", fontName="DejaVuSans-Bold", fontSize=18, leading=22, spaceAfter=10),
        "Caption": ParagraphStyle(
            "Caption", fontName="DejaVuSans-Oblique", fontSize=8, leading=11,
            textColor=colors.grey, spaceAfter=6,
        ),
        "Heading2": ParagraphStyle(
            "Heading2", fontName="DejaVuSans-Bold", fontSize=14, leading=18, spaceBefore=14, spaceAfter=8,
        ),
        "Heading3": ParagraphStyle(
            "Heading3", fontName="DejaVuSans-Bold", fontSize=11.5, leading=15, spaceBefore=10, spaceAfter=6,
        ),
        "Bold": ParagraphStyle("Bold", fontName="DejaVuSans-Bold", fontSize=9.5, leading=13, spaceAfter=4),
        "Body": ParagraphStyle("Body", fontName="DejaVuSans", fontSize=9.5, leading=13, spaceAfter=4),
        "Bullet": ParagraphStyle(
            "Bullet", fontName="DejaVuSans", fontSize=9.5, leading=13, spaceAfter=2, leftIndent=10,
        ),
        "TableHeader": ParagraphStyle("TableHeader", fontName="DejaVuSans-Bold", fontSize=8, leading=10),
        "TableCell": ParagraphStyle("TableCell", fontName="DejaVuSans", fontSize=8, leading=10),
    }


def _escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(text):
    text = _escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    return text


def _scaled_image_flowable(source):
    try:
        if isinstance(source, (bytes, bytearray)):
            pil = PILImage.open(io.BytesIO(source))
            reader = io.BytesIO(source)
        else:
            pil = PILImage.open(source)
            reader = source
        w_px, h_px = pil.size
    except Exception:
        return None

    aspect = h_px / w_px
    width, height = MAX_IMG_WIDTH, MAX_IMG_WIDTH * aspect
    if height > MAX_IMG_HEIGHT:
        height = MAX_IMG_HEIGHT
        width = height / aspect
    return RLImage(reader, width=width, height=height)


def _table_flowable(data, styles):
    if isinstance(data, pd.DataFrame):  # as produced by st.table(df) calls
        header = [str(data.index.name or "")] + [str(c) for c in data.columns]
        raw_rows = [header] + [[str(idx)] + [str(v) for v in row.tolist()] for idx, row in data.iterrows()]
    else:
        raw_rows = data

    n_cols = len(raw_rows[0])
    avail_width = A4[0] - 32 * mm
    first_col_width = avail_width * 0.34 if n_cols > 1 else avail_width
    other_width = (avail_width - first_col_width) / max(n_cols - 1, 1)
    col_widths = [first_col_width] + [other_width] * (n_cols - 1)

    rows = []
    for i, row in enumerate(raw_rows):
        style = styles["TableHeader"] if i == 0 else styles["TableCell"]
        rows.append([Paragraph(_escape(v), style) for v in row])

    table = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def _blocks_to_story(blocks, styles):
    story = []
    for kind, content in blocks:
        if kind == "subheader":
            story.append(Paragraph(_inline(content), styles["Heading2"]))
        elif kind == "markdown":
            stripped = content.strip()
            if stripped == "---":
                story.append(Spacer(1, 4))
                story.append(HRFlowable(width="100%", color=colors.lightgrey, thickness=0.75))
                story.append(Spacer(1, 4))
            elif stripped.startswith("#### "):
                story.append(Paragraph(_inline(stripped[5:]), styles["Heading3"]))
            elif stripped.startswith("- "):
                story.append(Paragraph("• " + _inline(stripped[2:]), styles["Bullet"]))
            elif stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
                story.append(Paragraph(_inline(stripped), styles["Bold"]))
            else:
                story.append(Paragraph(_inline(stripped), styles["Body"]))
        elif kind == "write":
            story.append(Paragraph(_inline(content), styles["Body"]))
        elif kind == "caption":
            story.append(Paragraph(_inline(content), styles["Caption"]))
        elif kind == "divider":
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", color=colors.grey, thickness=1))
            story.append(Spacer(1, 6))
        elif kind in ("image", "image_bytes"):
            flow = _scaled_image_flowable(content)
            if flow is not None:
                story.append(flow)
                story.append(Spacer(1, 8))
        elif kind == "table":
            story.append(_table_flowable(content, styles))
            story.append(Spacer(1, 8))
        elif kind == "metric":
            label, value = content
            story.append(Paragraph(f"<b>{_escape(label)}:</b> {_escape(value)}", styles["Body"]))
    return story


def _inputs_story(inputs, styles):
    story = [Paragraph("Inputs", styles["Heading2"])]
    rows = [["Parameter", "Value"]]
    for key, label, fmt in INPUT_FIELDS:
        if key in inputs:
            rows.append([label, fmt.format(inputs[key])])
    for i, layer in enumerate(inputs.get("cover_layers", []), start=1):
        rows.append([f"Cover Layer {i} — thickness / unit weight", f"{layer['t']:.0f} mm / {layer['gamma']:.1f} kN/m3"])
    story.append(_table_flowable(rows, styles))
    story.append(Spacer(1, 10))
    return story


def generate(inputs):
    """Re-run every calculation module under a Streamlit-call recorder, then lay the captured
    narrative out as a PDF. Mirrors app.py's own call sequence exactly, so the PDF matches what's
    on screen without duplicating any calculation logic."""
    _register_fonts()
    styles = _styles()

    with _capture() as rec:
        box = box_culvert.render(inputs)
        lm1 = lm1_calculations.render(inputs, box)
        lm3 = lm3_calculations.render(inputs, box)
        b4 = table_b4.render(inputs, box, lm1, lm3)
        b5 = table_b5.render(inputs, box, lm1, lm3)
        b6 = table_b6.render(inputs, box, lm1, lm3)
        summary.render(box, b4, b5, b6)
        assumptions.render()

    story = [
        Paragraph("Culvert Stability — Calculation Report", styles["Title"]),
        Paragraph(f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M}", styles["Caption"]),
        Spacer(1, 6),
    ]
    story.extend(_inputs_story(inputs, styles))
    story.append(PageBreak())
    story.extend(_blocks_to_story(rec.blocks, styles))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
        title="Culvert Stability - Calculation Report",
    )
    doc.build(story)
    return buf.getvalue()


def render_button(inputs):
    st.subheader("Export")
    if st.button("Generate PDF Report"):
        with st.spinner("Building PDF report..."):
            st.session_state["pdf_report_bytes"] = generate(inputs)

    if "pdf_report_bytes" in st.session_state:
        st.download_button(
            "Download PDF Report",
            data=st.session_state["pdf_report_bytes"],
            file_name="culvert_stability_report.pdf",
            mime="application/pdf",
        )
