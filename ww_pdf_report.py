from reportlab.platypus import Paragraph, Spacer

import pdf_export
import ww_assumptions
import ww_geometry
import ww_stability
import ww_structural
import ww_summary

# (inputs dict key, PDF label, format spec) — mirrors the widgets in ww_inputs.py
INPUT_FIELDS = [
    ("H_stem", "Stem Height, H_stem (m)", "{:.2f}"),
    ("t_stem", "Stem Thickness, t_stem (m)", "{:.2f}"),
    ("t_base", "Base Thickness, t_base (m)", "{:.2f}"),
    ("L_toe", "Toe Length, L_toe (m)", "{:.2f}"),
    ("L_heel", "Heel Length, L_heel (m)", "{:.2f}"),
    ("D_emb", "Embedment in front of toe, D_emb (m)", "{:.2f}"),
    ("h_wt", "Water Table, h_wt (m) — height relative to underside of base slab", "{:.2f}"),
    ("q_surcharge", "Live Load Surcharge, q_surcharge (kPa)", "{:.1f}"),
    ("P_h", "Additional Horizontal Point Load, P_h (kN/m)", "{:.2f}"),
    ("h_P", "Point Load Height above base, h_P (m)", "{:.2f}"),
    ("phi_backfill", "Backfill Friction Angle, phi_backfill (deg)", "{:.1f}"),
    ("gamma_backfill", "Backfill Unit Weight, gamma_backfill (kN/m3)", "{:.1f}"),
    ("beta", "Backfill Slope, beta (deg)", "{:.1f}"),
    ("phi_founding", "Founding Friction Angle, phi_founding (deg)", "{:.1f}"),
    ("gamma_founding", "Founding Unit Weight, gamma_founding (kN/m3)", "{:.1f}"),
    ("c_founding", "Founding Cohesion, c_founding (kPa)", "{:.1f}"),
    ("gamma_concrete", "Concrete Unit Weight, gamma_concrete (kN/m3)", "{:.1f}"),
    ("f_ck", "Concrete Strength, f_ck (MPa)", "{:.0f}"),
    ("f_yk", "Steel Yield Strength, f_yk (MPa)", "{:.0f}"),
    ("cover", "Nominal Cover, cover (mm)", "{:.0f}"),
    ("stem_bar_dia", "Stem bar diameter (mm)", "{:.0f}"),
    ("stem_bar_spacing", "Stem bar spacing (mm)", "{:.0f}"),
    ("heel_bar_dia", "Heel bar diameter (mm)", "{:.0f}"),
    ("heel_bar_spacing", "Heel bar spacing (mm)", "{:.0f}"),
    ("toe_bar_dia", "Toe bar diameter (mm)", "{:.0f}"),
    ("toe_bar_spacing", "Toe bar spacing (mm)", "{:.0f}"),
]


def _inputs_story(inputs, styles_dict):
    story = [Paragraph("Inputs", styles_dict["Heading2"])]
    rows = [["Parameter", "Value"]]
    for key, label, fmt in INPUT_FIELDS:
        if key in inputs:
            rows.append([label, fmt.format(inputs[key])])
    story.append(pdf_export.table_flowable(rows, styles_dict))
    story.append(Spacer(1, 10))
    return story


def generate(inputs):
    """Re-run every calculation module under a Streamlit-call recorder, then lay the captured
    narrative out as a PDF. Mirrors wing_wall.py's own call sequence exactly, so the PDF matches
    what's on screen without duplicating any calculation logic."""
    pdf_export.register_fonts()
    styles_dict = pdf_export.styles()

    with pdf_export.capture() as rec:
        geom = ww_geometry.render(inputs)
        stab = ww_stability.render(inputs, geom)
        struct = ww_structural.render(inputs, geom)
        ww_summary.render(geom, stab, struct)
        ww_assumptions.render()

    return pdf_export.build(
        title="Wing Wall Design — Calculation Report",
        subtitle_story=_inputs_story(inputs, styles_dict),
        blocks=rec.blocks,
        doc_title="Wing Wall Design - Calculation Report",
    )


def render_button(inputs):
    pdf_export.render_button(
        generate_fn=lambda: generate(inputs),
        file_name="wing_wall_design_report.pdf",
        session_key="ww_pdf_report_bytes",
    )
