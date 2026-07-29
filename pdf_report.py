from reportlab.platypus import Paragraph, Spacer

import assumptions
import box_culvert
import lm1_calculations
import lm3_calculations
import pdf_export
import summary
import table_b4
import table_b5
import table_b6

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


def _inputs_story(inputs, styles_dict):
    story = [Paragraph("Inputs", styles_dict["Heading2"])]
    rows = [["Parameter", "Value"]]
    for key, label, fmt in INPUT_FIELDS:
        if key in inputs:
            rows.append([label, fmt.format(inputs[key])])
    for i, layer in enumerate(inputs.get("cover_layers", []), start=1):
        rows.append([f"Cover Layer {i} — thickness / unit weight", f"{layer['t']:.0f} mm / {layer['gamma']:.1f} kN/m3"])
    story.append(pdf_export.table_flowable(rows, styles_dict))
    story.append(Spacer(1, 10))
    return story


def generate(inputs):
    """Re-run every calculation module under a Streamlit-call recorder, then lay the captured
    narrative out as a PDF. Mirrors app.py's own call sequence exactly, so the PDF matches what's
    on screen without duplicating any calculation logic."""
    pdf_export.register_fonts()
    styles_dict = pdf_export.styles()

    with pdf_export.capture() as rec:
        box = box_culvert.render(inputs)
        lm1 = lm1_calculations.render(inputs, box)
        lm3 = lm3_calculations.render(inputs, box)
        b4 = table_b4.render(inputs, box, lm1, lm3)
        b5 = table_b5.render(inputs, box, lm1, lm3)
        b6 = table_b6.render(inputs, box, lm1, lm3)
        summary.render(box, b4, b5, b6)
        assumptions.render()

    return pdf_export.build(
        title="Culvert Stability — Calculation Report",
        subtitle_story=_inputs_story(inputs, styles_dict),
        blocks=rec.blocks,
        doc_title="Culvert Stability - Calculation Report",
    )


def render_button(inputs):
    pdf_export.render_button(
        generate_fn=lambda: generate(inputs),
        file_name="culvert_stability_report.pdf",
        session_key="pdf_report_bytes",
    )
