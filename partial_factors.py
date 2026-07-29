import pandas as pd
import streamlit as st

# NA to BS EN 1990:2002+A1:2005 partial factors (gamma_F). Shared reference values for use across
# LM1 and LM3 calculations. Row keys map to symbols: self_weight/superimposed/water_pressure -> gamma_G;
# road_traffic/thermal -> gamma_Q; material_phi -> gamma_M.
UNFAVOURABLE = {
    "Self weight of structure & backfill, gamma_G;sup": {
        "SLS": 1.00, "EQU": 1.05, "STR/GEO Comb1": 1.35, "STR/GEO Comb2": 1.00,
    },
    "Superimposed permanent load, gamma_G;sup": {
        "SLS": 1.00, "EQU": 1.05, "STR/GEO Comb1": 1.20, "STR/GEO Comb2": 1.00,
    },
    "Road traffic action on box, gamma_Q;sup": {
        "SLS": 1.00, "EQU": 1.35, "STR/GEO Comb1": 1.35, "STR/GEO Comb2": 1.15,
    },
    "Variable/traffic surcharge action, gamma_Q;sup": {
        "SLS": 1.00, "EQU": 1.35, "STR/GEO Comb1": 1.35, "STR/GEO Comb2": 1.15,
    },
    "Thermal actions, gamma_Q;sup": {
        "SLS": 1.00, "EQU": 1.55, "STR/GEO Comb1": 1.55, "STR/GEO Comb2": 1.30,
    },
    "Material factor to phi', gamma_M": {
        "SLS": 1.00, "EQU": 1.10, "STR/GEO Comb1": 1.00, "STR/GEO Comb2": 1.25,
    },
    "Vertical and horizontal water pressures, gamma_G;sup": {
        "SLS": 0.00, "EQU": 1.00, "STR/GEO Comb1": 1.00, "STR/GEO Comb2": 1.00,
    },
}

FAVOURABLE = {
    "Self weight of structure & backfill, gamma_G;inf": {
        "SLS": 1.00, "EQU": 0.95, "STR/GEO Comb1": 0.95, "STR/GEO Comb2": 1.00,
    },
    "Superimposed permanent load, gamma_G;inf": {
        "SLS": 1.00, "EQU": 0.95, "STR/GEO Comb1": 0.95, "STR/GEO Comb2": 1.00,
    },
}

# UK NA to BS EN 1991-1-1 Table NA.1 Cl. 5.2.3(3): road construction thickness deviation
ROAD_CONSTRUCTION_DEVIATION = {"unfavourable": 1.55, "favourable": 0.60}   # +55% / -40%


def render():
    st.markdown("**Partial Factors γF** (From NA to BS EN 1990:2002+A1:2005)")
    st.write("For SLS factors see Clause NA.2.3.9")
    st.write("For EQU factors see Table NA.A2.4(A)")
    st.write("For STR/GEO Comb1 factors see Table NA.A2.4(B)")
    st.write("For STR/GEO Comb2 factors see Table NA.A2.4(C)")

    st.write(
        "Allow for deviation of road construction thickness to UK NA 1991-1-1 Table NA.1 Cl. 5.2.3(3) "
        "= +55% or −40%."
    )

    st.markdown("*Unfavourable*")
    st.table(pd.DataFrame(UNFAVOURABLE).T.map(lambda v: f"{v:.2f}"))

    st.markdown("*Favourable*")
    st.table(pd.DataFrame(FAVOURABLE).T.map(lambda v: f"{v:.2f}"))
