from reportlab.platypus import Paragraph, Spacer

import beam_assumptions
import beam_diagram
import pdf_export
import rc_beam_design


def _inputs_story(inputs, rc_inputs, styles_dict):
    story = [Paragraph("Inputs", styles_dict["Heading2"])]
    supports = inputs["supports"]

    rows = [["Parameter", "Value"]]
    rows.append(["Number of spans", str(len(supports) - 1)])
    for i, length in enumerate(inputs["span_lengths"], start=1):
        rows.append([f"Span {i} length (m)", f"{length:.2f}"])
    rows.append(["Total length (m)", f"{supports[-1]:.2f}"])
    rows.append(["Support positions (m)", ", ".join(f"{s:.2f}" for s in supports)])
    for i, (x, p) in enumerate(inputs["point_loads"], start=1):
        rows.append([f"Point load {i}", f"{p:.2f} kN, downward, at x = {x:.2f} m"])
    for i, (s, e, w) in enumerate(inputs["udls"], start=1):
        rows.append([f"UDL {i}", f"{w:.2f} kN/m, downward, from x = {s:.2f} to {e:.2f} m"])
    story.append(pdf_export.table_flowable(rows, styles_dict))
    story.append(Spacer(1, 10))

    story.append(Paragraph("RC Beam Design Inputs", styles_dict["Heading2"]))
    rc_rows = [
        ["Parameter", "Value"],
        ["Width, b (mm)", f"{rc_inputs['b']:.0f}"],
        ["Overall depth, h (mm)", f"{rc_inputs['h']:.0f}"],
        ["Cover (mm)", f"{rc_inputs['cover']:.0f}"],
        ["Main bar diameter (mm)", f"{rc_inputs['bar_dia']:.0f}"],
        ["Link diameter (mm)", f"{rc_inputs['link_dia']:.0f}"],
        ["Number of link legs", f"{rc_inputs['n_legs']:.0f}"],
        ["Concrete strength, f_ck (MPa)", f"{rc_inputs['fck']:.0f}"],
        ["Steel strength, f_yk (MPa)", f"{rc_inputs['fyk']:.0f}"],
        ["Redistribution ratio, δ", f"{rc_inputs['delta']:.2f}"],
        ["M_Ed, sagging (kNm)", f"{rc_inputs['M_sag']:.2f}"],
        ["M_Ed, hogging (kNm)", f"{rc_inputs['M_hog']:.2f}"],
        ["V_Ed (kN)", f"{rc_inputs['V_Ed']:.2f}"],
    ]
    story.append(pdf_export.table_flowable(rc_rows, styles_dict))
    story.append(Spacer(1, 10))
    return story


def generate(inputs, rc_inputs):
    """Re-run the beam diagram/results, RC design and assumptions under a Streamlit-call
    recorder, then lay the captured narrative out as a PDF. Mirrors beam_analysis.py's own call
    sequence exactly, so the PDF matches what's on screen without duplicating any calc logic."""
    pdf_export.register_fonts()
    styles_dict = pdf_export.styles()

    with pdf_export.capture() as rec:
        beam_diagram.render(inputs)
        rc_beam_design.render(rc_inputs)
        beam_assumptions.render()

    return pdf_export.build(
        title="Beam Analysis — Calculation Report",
        subtitle_story=_inputs_story(inputs, rc_inputs, styles_dict),
        blocks=rec.blocks,
        doc_title="Beam Analysis - Calculation Report",
    )


def render_button(inputs, rc_inputs):
    pdf_export.render_button(
        generate_fn=lambda: generate(inputs, rc_inputs),
        file_name="beam_analysis_report.pdf",
        session_key="beam_pdf_report_bytes",
    )
