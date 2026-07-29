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

MAX_IMG_WIDTH = 160 * mm
MAX_IMG_HEIGHT = 230 * mm


class FakeColumn:
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


class Recorder:
    """Drop-in replacement for the handful of `st.*` functions a calc module calls, recording each
    call as a block instead of drawing it — so the same render() functions used for the live app
    can be re-run to build a PDF, with no changes to any calculation module."""

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
        return tuple(FakeColumn(self) for _ in range(n))


_PATCHED = ["write", "markdown", "subheader", "caption", "divider", "image", "table", "pyplot", "columns"]


@contextlib.contextmanager
def capture():
    recorder = Recorder()
    originals = {name: getattr(st, name) for name in _PATCHED}
    for name in _PATCHED:
        setattr(st, name, getattr(recorder, name))
    try:
        yield recorder
    finally:
        for name, fn in originals.items():
            setattr(st, name, fn)


def register_fonts():
    if "DejaVuSans" in pdfmetrics.getRegisteredFontNames():
        return
    base = matplotlib.get_data_path() + "/fonts/ttf"
    pdfmetrics.registerFont(TTFont("DejaVuSans", f"{base}/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", f"{base}/DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", f"{base}/DejaVuSans-Oblique.ttf"))


def styles():
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


def escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text):
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    return text


def scaled_image_flowable(source):
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


def table_flowable(data, styles_dict):
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
        style = styles_dict["TableHeader"] if i == 0 else styles_dict["TableCell"]
        rows.append([Paragraph(escape(v), style) for v in row])

    table = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def blocks_to_story(blocks, styles_dict):
    story = []
    for kind, content in blocks:
        if kind == "subheader":
            story.append(Paragraph(inline(content), styles_dict["Heading2"]))
        elif kind == "markdown":
            stripped = content.strip()
            if stripped == "---":
                story.append(Spacer(1, 4))
                story.append(HRFlowable(width="100%", color=colors.lightgrey, thickness=0.75))
                story.append(Spacer(1, 4))
            elif stripped.startswith("#### "):
                story.append(Paragraph(inline(stripped[5:]), styles_dict["Heading3"]))
            elif stripped.startswith("- "):
                story.append(Paragraph("• " + inline(stripped[2:]), styles_dict["Bullet"]))
            elif stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
                story.append(Paragraph(inline(stripped), styles_dict["Bold"]))
            else:
                story.append(Paragraph(inline(stripped), styles_dict["Body"]))
        elif kind == "write":
            story.append(Paragraph(inline(content), styles_dict["Body"]))
        elif kind == "caption":
            story.append(Paragraph(inline(content), styles_dict["Caption"]))
        elif kind == "divider":
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", color=colors.grey, thickness=1))
            story.append(Spacer(1, 6))
        elif kind in ("image", "image_bytes"):
            flow = scaled_image_flowable(content)
            if flow is not None:
                story.append(flow)
                story.append(Spacer(1, 8))
        elif kind == "table":
            story.append(table_flowable(content, styles_dict))
            story.append(Spacer(1, 8))
        elif kind == "metric":
            label, value = content
            story.append(Paragraph(f"<b>{escape(label)}:</b> {escape(value)}", styles_dict["Body"]))
    return story


def build(title, subtitle_story, blocks, doc_title):
    """Assemble a full PDF: title heading + generated-timestamp caption, then `subtitle_story`
    (e.g. an inputs table), a page break, then the captured `blocks`."""
    styles_dict = styles()
    story = [
        Paragraph(title, styles_dict["Title"]),
        Paragraph(f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M}", styles_dict["Caption"]),
        Spacer(1, 6),
    ]
    story.extend(subtitle_story)
    story.append(PageBreak())
    story.extend(blocks_to_story(blocks, styles_dict))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
        title=doc_title,
    )
    doc.build(story)
    return buf.getvalue()


def render_button(generate_fn, file_name, session_key,
                   button_label="Generate PDF Report", download_label="Download PDF Report"):
    st.subheader("Export")
    if st.button(button_label, key=f"{session_key}_generate_btn"):
        with st.spinner("Building PDF report..."):
            st.session_state[session_key] = generate_fn()

    if session_key in st.session_state:
        st.download_button(
            download_label,
            data=st.session_state[session_key],
            file_name=file_name,
            mime="application/pdf",
            key=f"{session_key}_download_btn",
        )
