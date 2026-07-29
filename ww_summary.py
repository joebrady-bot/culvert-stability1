import pandas as pd
import streamlit as st


def _worst_case(stability_results, key_ur, key_ok):
    worst = None
    for combo, r in stability_results.items():
        if worst is None or r[key_ur] > worst["ur"]:
            worst = {"combo": combo, "ur": r[key_ur], "ok": r[key_ok]}
    return worst


def render(geometry_results, stability_results, structural_results):
    """Quick-glance summary of geometry and governing results — global stability across all four
    limit states, plus the structural capacity checks at STR/GEO Comb1."""
    st.subheader("Summary")
    st.caption("Governing (highest-utilisation) result across all four limit states.")

    c1, c2 = st.columns(2)
    c1.metric("L_base (m)", f"{geometry_results['L_base']:.2f}")
    c2.metric("H_total (m)", f"{geometry_results['H_total']:.2f}")

    rows = []
    for label, key_ur, key_ok in [
        ("Sliding", "ur_sliding", "ok_sliding"),
        ("Overturning", "ur_overturning", "ok_overturning"),
        ("Bearing", "ur_bearing", "ok_bearing"),
    ]:
        worst = _worst_case(stability_results, key_ur, key_ok)
        rows.append({
            "Check": label,
            "Governing Combo": worst["combo"],
            "Utilisation": f"{worst['ur'] * 100:.0f}%",
            "Status": "OK" if worst["ok"] else "Review required",
        })
    st.table(pd.DataFrame(rows).set_index("Check"))

    st.markdown("**Structural (EC2, STR/GEO Comb1)**")
    rows2 = []
    for label, key in [("Stem", "stem"), ("Heel", "heel"), ("Toe", "toe")]:
        sec = structural_results[key]
        rows2.append({
            "Section": label,
            "UR Bending": f"{sec['UR_bend'] * 100:.0f}%",
            "Bending": "OK" if sec["ok_bend"] else "Review required",
            "UR Shear": f"{sec['UR_shear'] * 100:.0f}%",
            "Shear": "OK" if sec["ok_shear"] else "Review required",
        })
    st.table(pd.DataFrame(rows2).set_index("Section"))
