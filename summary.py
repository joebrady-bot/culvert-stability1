import pandas as pd
import streamlit as st


def _worst_case(table_results):
    """Scan every combo/model in a stability table's results and return the governing
    (smallest-margin) case for sliding and for overturning, across all four limit states."""
    worst_sliding = worst_ot = None
    for combo, combo_result in table_results["sliding"].items():
        for model in ("LM1", "LM3"):
            r = combo_result[model]
            if worst_sliding is None or r["margin"] < worst_sliding["margin"]:
                worst_sliding = {"combo": combo, "model": model, "margin": r["margin"], "ok": r["ok"]}
            if worst_ot is None or r["ot_margin"] < worst_ot["margin"]:
                worst_ot = {"combo": combo, "model": model, "margin": r["ot_margin"], "ok": r["ot_ok"]}
    return worst_sliding, worst_ot


def render(box_culvert_results, table_b4_results, table_b5_results, table_b6_results):
    """Quick-glance summary of geometry and governing stability results — lets a user change an
    input above and immediately see whether anything fails, without opening each table's tab."""
    st.subheader("Summary")
    st.caption("Governing (worst-case) result across all four limit states, per table.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("B_ext (m)", f"{box_culvert_results['B_ext']:.2f}")
    c2.metric("H_ext (m)", f"{box_culvert_results['H_ext']:.2f}")
    c3.metric("W_box (kN/m)", f"{box_culvert_results['W_box']:.1f}")
    c4.metric("Total cover UDL (kN/m)", f"{box_culvert_results['UDL_total']:.1f}")

    rows = []
    for label, results in [
        ("Table B.4", table_b4_results),
        ("Table B.5", table_b5_results),
        ("Table B.6", table_b6_results),
    ]:
        worst_sliding, worst_ot = _worst_case(results)
        rows.append({
            "Check": f"{label} — Sliding",
            "Governing Case": f"{worst_sliding['combo']} / {worst_sliding['model']}",
            "Margin": f"{worst_sliding['margin']:.1f} kN",
            "Status": "OK" if worst_sliding["ok"] else "Review required",
        })
        rows.append({
            "Check": f"{label} — Overturning",
            "Governing Case": f"{worst_ot['combo']} / {worst_ot['model']}",
            "Margin": f"{worst_ot['margin']:.1f} kNm",
            "Status": "OK" if worst_ot["ok"] else "Review required",
        })

    st.table(pd.DataFrame(rows).set_index("Check"))
