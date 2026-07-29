import pandas as pd
import streamlit as st


def _utilisation(demand, capacity):
    if capacity <= 0:
        return float("inf")
    return max(0.0, demand) / capacity * 100


def _worst_case(table_results):
    """Scan every combo/model in a stability table's results and return the governing
    (highest-utilisation) case for sliding and for overturning, across all four limit states."""
    worst_sliding = worst_ot = None
    for combo, combo_result in table_results["sliding"].items():
        for model in ("LM1", "LM3"):
            r = combo_result[model]
            ur_sliding = _utilisation(r["friction_required"], r["max_Rd"])
            if worst_sliding is None or ur_sliding > worst_sliding["utilisation"]:
                worst_sliding = {"combo": combo, "model": model, "utilisation": ur_sliding, "ok": r["ok"]}
            ur_ot = _utilisation(r["M_driving"], r["M_stabilizing"])
            if worst_ot is None or ur_ot > worst_ot["utilisation"]:
                worst_ot = {"combo": combo, "model": model, "utilisation": ur_ot, "ok": r["ot_ok"]}
    return worst_sliding, worst_ot


def render(box_culvert_results, table_b4_results, table_b5_results, table_b6_results):
    """Quick-glance summary of geometry and governing stability results — lets a user change an
    input above and immediately see whether anything fails, without opening each table's tab."""
    st.subheader("Summary")
    st.caption("Governing (highest-utilisation) result across all four limit states, per table.")

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
            "Utilisation": f"{worst_sliding['utilisation']:.0f}%",
            "Status": "OK" if worst_sliding["ok"] else "Review required",
        })
        rows.append({
            "Check": f"{label} — Overturning",
            "Governing Case": f"{worst_ot['combo']} / {worst_ot['model']}",
            "Utilisation": f"{worst_ot['utilisation']:.0f}%",
            "Status": "OK" if worst_ot["ok"] else "Review required",
        })

    st.table(pd.DataFrame(rows).set_index("Check"))
