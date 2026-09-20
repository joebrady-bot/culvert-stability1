"""Generates Culvert_Stability.xlsx — a live-formula Excel replica of the Culvert Stability
Streamlit calc sheet (PD 6694-1 Annex B Tables B.4/B.5/B.6, BS EN 1991-2 LM1/LM3 traffic loading).

Every number the Python app computes via st.write() becomes a labelled row here with a real
Excel formula referencing other cells — editing an Inputs cell recalculates everything
downstream, same as changing an input in the Streamlit app reruns the calculation.

Run: python build_workbook.py  (writes Culvert_Stability.xlsx next to this script)
"""

import re

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

_CELL_REF_RE = re.compile(r"^[A-Za-z]{1,3}[0-9]{1,7}$")


def check_name_collisions(wb):
    """A defined name that LOOKS LIKE a cell reference (e.g. 'n1' == cell N1, 'tan30' == cell
    TAN30) gets silently resolved by Excel's formula parser as that cell instead of the name —
    the name still shows up fine in the Names collection, but every formula using it evaluates
    to 0/blank with no error. Run this after every sheet addition, not just once at the end."""
    bad = []
    for name in wb.defined_names:
        if _CELL_REF_RE.match(name):
            letters = re.match(r"[A-Za-z]+", name).group().upper()
            digits = int(re.search(r"[0-9]+", name).group())
            try:
                col = column_index_from_string(letters)
                if col <= 16384 and digits <= 1048576:
                    bad.append(name)
            except ValueError:
                pass  # letters exceed the max column — not a real ambiguity
    if bad:
        raise ValueError(
            f"Defined name(s) collide with a cell reference and WILL silently break formulas "
            f"that use them: {bad} — rename them (e.g. add a suffix or leading word)."
        )

# ── Styling constants ──────────────────────────────────────────────────────────────
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
HEADER_FILL = PatternFill("solid", fgColor="1F3864")
SECTION_FILL = PatternFill("solid", fgColor="D9E1F2")
OK_FILL = PatternFill("solid", fgColor="C6EFCE")
BAD_FILL = PatternFill("solid", fgColor="FFC7CE")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=12)
SECTION_FONT = Font(bold=True, size=11)
BOLD = Font(bold=True)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

COMBOS = ["SLS", "EQU", "STR_GEO_Comb1", "STR_GEO_Comb2"]
COMBO_LABELS = {"SLS": "SLS", "EQU": "EQU", "STR_GEO_Comb1": "STR/GEO Comb1", "STR_GEO_Comb2": "STR/GEO Comb2"}


def title(ws: Worksheet, row, text, span=6):
    ws.cell(row, 1, text)
    ws.cell(row, 1).font = HEADER_FONT
    ws.cell(row, 1).fill = HEADER_FILL
    for c in range(2, span + 1):
        ws.cell(row, c).fill = HEADER_FILL
    ws.row_dimensions[row].height = 20
    return row + 2


def section(ws: Worksheet, row, text, span=6):
    ws.cell(row, 1, text)
    ws.cell(row, 1).font = SECTION_FONT
    for c in range(1, span + 1):
        ws.cell(row, c).fill = SECTION_FILL
    return row + 1


def label_value(ws: Worksheet, row, label, value_or_formula, name=None, fmt="0.00", input_cell=False, col=2):
    ws.cell(row, 1, label)
    cell = ws.cell(row, col, value_or_formula)
    cell.number_format = fmt
    if input_cell:
        cell.fill = INPUT_FILL
        cell.border = BORDER
    if name:
        ws.parent.defined_names[name] = openpyxl.workbook.defined_name.DefinedName(
            name, attr_text=f"'{ws.title}'!${get_column_letter(col)}${row}"
        )
    return row + 1


def autosize(ws: Worksheet, widths):
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def build_inputs(wb):
    ws = wb.create_sheet("Inputs")
    r = 1
    r = title(ws, r, "Culvert Stability — Inputs")

    r = section(ws, r, "Culvert Geometry")
    r = label_value(ws, r, "Internal Width, B (m)", 2.5, name="B", input_cell=True)
    r = label_value(ws, r, "Internal Height, H (m)", 2.0, name="H", input_cell=True)
    r = label_value(ws, r, "Wall Thickness, t_w (m)", 0.3, name="t_w", input_cell=True)
    r = label_value(ws, r, "Slab Thickness, t_s (m)", 0.3, name="t_s", input_cell=True)
    r = label_value(ws, r, "Overall Length, L_L (m)", 20.6, name="L_L", input_cell=True)
    r = label_value(ws, r, "Concrete Density, gamma_concrete (kN/m3)", 25.0, name="gamma_concrete", input_cell=True)
    r += 1

    r = section(ws, r, "Water Table")
    r = label_value(ws, r, "Water Table, h_wt (m) — height above culvert invert", 0.0, name="h_wt", input_cell=True)
    r += 1

    r = section(ws, r, "Road Geometry")
    r = label_value(ws, r, "Carriageway Width, w_C (m)", 7.3, name="w_C", input_cell=True)
    r = label_value(ws, r, "Lane Width, w_L (m)", 3.65, name="w_L", input_cell=True)
    r += 1

    r = section(ws, r, "Cover Layers (top to bottom, up to 3)")
    r = label_value(ws, r, "Number of cover layers (1-3)", 3, name="n_layers", input_cell=True, fmt="0")
    ws.cell(r, 1, "Layer"); ws.cell(r, 2, "Thickness t_i (mm)"); ws.cell(r, 3, "Unit Weight gamma_i (kN/m3)")
    for c in (1, 2, 3):
        ws.cell(r, c).font = BOLD
    r += 1
    layer_defaults = [(200.0, 24.0), (500.0, 19.0), (300.0, 20.0)]
    layer_first_row = r
    for i, (t_def, g_def) in enumerate(layer_defaults, start=1):
        ws.cell(r, 1, f"Layer {i}")
        tc = ws.cell(r, 2, t_def); tc.fill = INPUT_FILL; tc.border = BORDER; tc.number_format = "0.0"
        gc = ws.cell(r, 3, g_def); gc.fill = INPUT_FILL; gc.border = BORDER; gc.number_format = "0.00"
        wb.defined_names[f"t_{i}"] = openpyxl.workbook.defined_name.DefinedName(f"t_{i}", attr_text=f"Inputs!$B${r}")
        wb.defined_names[f"gamma_{i}"] = openpyxl.workbook.defined_name.DefinedName(f"gamma_{i}", attr_text=f"Inputs!$C${r}")
        r += 1
    layer_last_row = r - 1
    wb.defined_names["layer_t_range"] = openpyxl.workbook.defined_name.DefinedName(
        "layer_t_range", attr_text=f"Inputs!$B${layer_first_row}:$B${layer_last_row}"
    )
    r += 1

    r = section(ws, r, "Soil Properties")
    r = label_value(ws, r, "Backfill Friction Angle, phi_backfill (deg)", 30.0, name="phi_backfill", input_cell=True)
    r = label_value(ws, r, "Backfill Density, gamma_backfill (kN/m3)", 19.0, name="gamma_backfill", input_cell=True)
    r = label_value(ws, r, "Overburden Depth, H_ob (m)", 0.6, name="H_ob", input_cell=True)
    r = label_value(ws, r, "Founding Friction Angle, phi_founding (deg)", 32.0, name="phi_founding", input_cell=True)
    r = label_value(ws, r, "Founding Density, gamma_founding (kN/m3)", 19.0, name="gamma_founding", input_cell=True)
    r += 1

    r = section(ws, r, "LM3 Vehicle Type")
    ws.cell(r, 1, "SV Vehicle (SV80 / SV100 / SV196)")
    vc = ws.cell(r, 2, "SV196")
    vc.fill = INPUT_FILL
    vc.border = BORDER
    wb.defined_names["sv_vehicle"] = openpyxl.workbook.defined_name.DefinedName("sv_vehicle", attr_text=f"Inputs!$B${r}")
    r += 2

    ws.cell(r, 1, "Yellow cells are inputs — edit these. Everything else recalculates automatically.")
    ws.cell(r, 1).font = Font(italic=True, color="808080")

    autosize(ws, {"A": 46, "B": 20, "C": 24})
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"
    return ws


def build_partial_factors(wb):
    ws = wb.create_sheet("PartialFactors")
    r = 1
    r = title(ws, r, "UK NA to BS EN 1990 — Partial Factors gamma_F")

    unfav = {
        "SelfWeight_sup": ("Self weight of structure & backfill, gamma_G;sup", [1.00, 1.05, 1.35, 1.00]),
        "Superimposed_sup": ("Superimposed permanent load, gamma_G;sup", [1.00, 1.05, 1.20, 1.00]),
        "RoadTraffic_sup": ("Road traffic action on box, gamma_Q;sup", [1.00, 1.35, 1.35, 1.15]),
        "MaterialM": ("Material factor to phi', gamma_M", [1.00, 1.10, 1.00, 1.25]),
        "WaterPressure_sup": ("Vertical and horizontal water pressures, gamma_G;sup", [0.00, 1.00, 1.00, 1.00]),
    }
    fav = {
        "SelfWeight_inf": ("Self weight of structure & backfill, gamma_G;inf", [1.00, 0.95, 0.95, 1.00]),
        "Superimposed_inf": ("Superimposed permanent load, gamma_G;inf", [1.00, 0.95, 0.95, 1.00]),
    }

    r = section(ws, r, "Unfavourable")
    ws.cell(r, 1, "Row");
    for i, combo in enumerate(COMBOS):
        ws.cell(r, 2 + i, COMBO_LABELS[combo]).font = BOLD
    r += 1
    for key, (label, vals) in unfav.items():
        ws.cell(r, 1, label)
        for i, v in enumerate(vals):
            c = ws.cell(r, 2 + i, v)
            c.number_format = "0.00"
            name = f"{key}_{COMBOS[i]}"
            wb.defined_names[name] = openpyxl.workbook.defined_name.DefinedName(
                name, attr_text=f"PartialFactors!${get_column_letter(2 + i)}${r}"
            )
        r += 1
    r += 1

    r = section(ws, r, "Favourable")
    ws.cell(r, 1, "Row")
    for i, combo in enumerate(COMBOS):
        ws.cell(r, 2 + i, COMBO_LABELS[combo]).font = BOLD
    r += 1
    for key, (label, vals) in fav.items():
        ws.cell(r, 1, label)
        for i, v in enumerate(vals):
            c = ws.cell(r, 2 + i, v)
            c.number_format = "0.00"
            name = f"{key}_{COMBOS[i]}"
            wb.defined_names[name] = openpyxl.workbook.defined_name.DefinedName(
                name, attr_text=f"PartialFactors!${get_column_letter(2 + i)}${r}"
            )
        r += 1
    r += 1

    r = label_value(ws, r, "Road construction deviation, unfavourable (+55%)", 1.55, name="road_dev_unfav")
    r = label_value(ws, r, "Road construction deviation, favourable (-40%)", 0.60, name="road_dev_fav")
    r = label_value(ws, r, "Model factor gamma_Sd;ec (Cl. 10.2.2)", 1.15, name="gamma_sd_ec")
    r = label_value(ws, r, "Water unit weight, gamma_w (kN/m3)", 9.81, name="gamma_w")

    # Table B.4/B.5/B.6 K values, per combo
    r += 1
    r = section(ws, r, "Table B.4/B.5/B.6 — Earth Pressure Coefficients")
    ws.cell(r, 1, "Combo")
    for i, combo in enumerate(COMBOS):
        ws.cell(r, 2 + i, COMBO_LABELS[combo]).font = BOLD
    r += 1
    k_rows = {
        "Ka_traffic": [0.33, 0.37, 0.33, 0.41],
        "Ka_earth": [0.33, 0.44, 0.40, 0.49],
        "Kmax": [0.60, 0.60, 0.72, 0.84],
    }
    for key, vals in k_rows.items():
        ws.cell(r, 1, key)
        for i, v in enumerate(vals):
            c = ws.cell(r, 2 + i, v)
            c.number_format = "0.00"
            name = f"{key}_{COMBOS[i]}"
            wb.defined_names[name] = openpyxl.workbook.defined_name.DefinedName(
                name, attr_text=f"PartialFactors!${get_column_letter(2 + i)}${r}"
            )
        r += 1

    autosize(ws, {"A": 46, "B": 12, "C": 14, "D": 16, "E": 16})
    ws.sheet_view.showGridLines = False
    return ws


def defname(wb, sheet, name, row, col):
    wb.defined_names[name] = openpyxl.workbook.defined_name.DefinedName(
        name, attr_text=f"'{sheet}'!${get_column_letter(col)}${row}"
    )


def build_global_calcs(wb):
    ws = wb.create_sheet("GlobalCalcs")
    r = 1
    r = title(ws, r, "Global Calculations")

    r = section(ws, r, "Self-Weights (per 1 m length)")
    r = label_value(ws, r, "B_ext = B + 2*t_w (m)", "=B+2*t_w", fmt="0.000")
    defname(wb, "GlobalCalcs", "B_ext", r - 1, 2)
    r = label_value(ws, r, "H_ext = H + 2*t_s (m)", "=H+2*t_s", fmt="0.000")
    defname(wb, "GlobalCalcs", "H_ext", r - 1, 2)
    r = label_value(ws, r, "A_conc = B_ext*H_ext - B*H (m2)", "=B_ext*H_ext-B*H", fmt="0.000")
    defname(wb, "GlobalCalcs", "A_conc", r - 1, 2)
    r = label_value(ws, r, "W_box = A_conc * gamma_concrete (kN/m)", "=A_conc*gamma_concrete", fmt="0.00")
    defname(wb, "GlobalCalcs", "W_box", r - 1, 2)
    r += 1

    r = section(ws, r, "Cover Layer Self-Weights")
    ws.cell(r, 1, "Layer"); ws.cell(r, 2, "Active?"); ws.cell(r, 3, "UDL_i = gamma_i*(t_i/1000) (kN/m)")
    for c in (1, 2, 3):
        ws.cell(r, c).font = BOLD
    r += 1
    udl_first_row = r
    for i in (1, 2, 3):
        ws.cell(r, 1, f"Layer {i}")
        active_f = f"={i}<=n_layers"
        ac = ws.cell(r, 2, active_f)
        udl_f = f"=IF({i}<=n_layers, gamma_{i}*(t_{i}/1000), 0)"
        uc = ws.cell(r, 3, udl_f)
        uc.number_format = "0.00"
        defname(wb, "GlobalCalcs", f"UDL_{i}", r, 3)
        r += 1
    udl_last_row = r - 1
    r = label_value(ws, r, "UDL_total (kN/m)", f"=SUM(C{udl_first_row}:C{udl_last_row})", fmt="0.00")
    defname(wb, "GlobalCalcs", "UDL_total", r - 1, 2)
    r += 1

    r = section(ws, r, "Horizontal Surcharge Model for LM1, LM2 & LM3")
    r = label_value(
        ws, r, "H_c = sum(active t_i)/1000 (m)",
        f"=(t_1 + IF(n_layers>=2,t_2,0) + IF(n_layers>=3,t_3,0))/1000", fmt="0.000",
    )
    defname(wb, "GlobalCalcs", "H_c", r - 1, 2)
    r = label_value(ws, r, "Reduction factor = (1-H_c/2)^2", "=(1-H_c/2)^2", fmt="0.000")
    defname(wb, "GlobalCalcs", "reduction_factor", r - 1, 2)
    r = label_value(
        ws, r, "F_hll_1m_coeff = 2*reduction_factor*330/w_L (coeff. of Kd, kN)",
        "=2*reduction_factor*330/w_L", fmt="0.00",
    )
    defname(wb, "GlobalCalcs", "F_hll_1m_coeff", r - 1, 2)
    r += 1
    ws.cell(r, 1, "F_hUDL_LM12 = 20*Kd kN/m2, F_hUDL_LM3 = 30*Kd kN/m2 (applied directly in Table B.4/5/6)")
    ws.cell(r, 1).font = Font(italic=True, color="808080")

    autosize(ws, {"A": 46, "B": 14, "C": 30})
    ws.sheet_view.showGridLines = False
    return ws


def build_lm1(wb):
    ws = wb.create_sheet("LM1")
    r = 1
    r = title(ws, r, "LM1 Calculations — Maximum Vertical Load & Braking")

    r = section(ws, r, "Notional Lanes")
    r = label_value(ws, r, "n_lanes = INT(w_C / 3)", "=INT(w_C/3)", fmt="0")
    defname(wb, "LM1", "n_lanes", r - 1, 2)
    r = label_value(ws, r, "Notional Lane Width (m)", 3.0, fmt="0.0")
    defname(wb, "LM1", "notional_lane_width", r - 1, 2)
    r = label_value(ws, r, "Remaining width = w_C - n_lanes*3 (m)", "=w_C-n_lanes*notional_lane_width", fmt="0.00")
    r += 1

    r = section(ws, r, "UDL & TS per Lane (BS EN 1991-2 Table 4.2, UK NA alpha factors)")
    ws.cell(r, 1, "Lane"); ws.cell(r, 2, "Active?"); ws.cell(r, 3, "alpha_qi")
    ws.cell(r, 4, "qik (kN/m2)"); ws.cell(r, 5, "UDL_i (kN/m2)"); ws.cell(r, 6, "Qi,TS (kN)")
    for c in range(1, 7):
        ws.cell(r, c).font = BOLD
    r += 1
    lane_first = r
    lane_alpha = {1: 0.61, 2: 2.2, 3: 2.2}
    lane_qk = {1: 9.0, 2: 2.5, 3: 2.5}
    lane_ts = {1: 300.0, 2: 200.0, 3: 100.0}
    for i in (1, 2, 3):
        ws.cell(r, 1, f"Lane {i}")
        ws.cell(r, 2, f"={i}<=n_lanes")
        ac = ws.cell(r, 3, lane_alpha[i]); ac.number_format = "0.00"
        qc = ws.cell(r, 4, lane_qk[i]); qc.number_format = "0.00"
        uc = ws.cell(r, 5, f"=C{r}*D{r}"); uc.number_format = "0.00"
        tc = ws.cell(r, 6, lane_ts[i]); tc.number_format = "0"
        defname(wb, "LM1", f"lane{i}_udl", r, 5)
        defname(wb, "LM1", f"lane{i}_ts", r, 6)
        r += 1
    r += 1

    r = section(ws, r, "Contact Patch & Dispersal Through Fill")
    r = label_value(ws, r, "Contact patch (mm)", 400.0, fmt="0")
    defname(wb, "LM1", "contact_patch", r - 1, 2)
    r = label_value(ws, r, "tan(30deg)", "=TAN(RADIANS(30))", fmt="0.0000")
    defname(wb, "LM1", "tan_30", r - 1, 2)
    r = label_value(
        ws, r, "Dispersed patch = contact_patch + 2*H_c*1000*tan_30 (mm)",
        "=contact_patch+2*H_c*1000*tan_30", fmt="0.0",
    )
    r = label_value(ws, r, "disp_m (m)", f"=B{r-1}/1000", fmt="0.000")
    defname(wb, "LM1", "disp_m", r - 1, 2)
    r += 1

    r = section(ws, r, "Transverse Dispersal (Figure 11) — lanes 1 & 2")
    r = label_value(ws, r, "W1 = lane1_ts / 2 (kN)", "=lane1_ts/2", fmt="0.00")
    r_w1 = r - 1
    r = label_value(ws, r, "W2 = lane2_ts / 2 (kN)", "=lane2_ts/2", fmt="0.00")
    r_w2 = r - 1
    r = label_value(ws, r, "Gap between lanes 1 & 2 = 3.0 - 2.0 (m)", "=notional_lane_width-2", fmt="0.00")
    r_gap = r - 1
    r = label_value(ws, r, "Overlap a = MAX(disp_m - gap, 0) (m)", f"=MAX(disp_m-B{r_gap},0)", fmt="0.000")
    r_a = r - 1
    r = label_value(
        ws, r, "F_transverse_1m (kN/m)",
        f"=IF(n_lanes>=2, 1*B{r_w1}/disp_m + B{r_a}*B{r_w2}/disp_m, B{r_w1}/disp_m)", fmt="0.00",
    )
    defname(wb, "LM1", "F_transverse_1m", r - 1, 2)
    r += 1

    r = section(ws, r, "Longitudinal Dispersal")
    r = label_value(ws, r, "Patch load = F_transverse_1m / disp_m (kN/m)", "=F_transverse_1m/disp_m", fmt="0.00")
    defname(wb, "LM1", "patch_load", r - 1, 2)
    r += 1

    r = section(ws, r, "Braking and Acceleration Forces")
    r = label_value(ws, r, "term1 = 0.6*alpha_Q1*(2*Q1k), alpha_Q1=1.0", "=0.6*1*(2*lane1_ts)", fmt="0.00")
    r_t1 = r - 1
    r = label_value(
        ws, r, "term2 = 0.1*alpha_q1*q1k*w1*L, alpha_q1=1.0, w1=3.0, L=B_ext",
        "=0.1*1*D" + str(lane_first) + "*notional_lane_width*B_ext", fmt="0.00",
    )
    r_t2 = r - 1
    r = label_value(ws, r, "Q_lk,raw = term1 + term2 (kN)", f"=B{r_t1}+B{r_t2}", fmt="0.00")
    r_raw = r - 1
    r = label_value(
        ws, r, "Q_lk,clamped = MAX(180, MIN(900, Q_lk,raw)) (kN)",
        f"=MAX(180,MIN(900,B{r_raw}))", fmt="0.00",
    )
    r_clamped = r - 1
    r = label_value(
        ws, r, "Reduction factor eta (H_c<0.6: 1; H_c<B_ext: (B_ext-H_c)/(B_ext-0.6); else 0)",
        "=IF(H_c<0.6,1,IF(H_c<B_ext,(B_ext-H_c)/(B_ext-0.6),0))", fmt="0.000",
    )
    r_eta = r - 1
    r = label_value(ws, r, "Q_lk = eta * Q_lk,clamped (kN)", f"=B{r_eta}*B{r_clamped}", fmt="0.00")
    defname(wb, "LM1", "Q_lk", r - 1, 2)

    autosize(ws, {"A": 58, "B": 14, "C": 10, "D": 12, "E": 14, "F": 12})
    ws.sheet_view.showGridLines = False
    return ws


# ── LM3 (Special Vehicle) axle geometry — fixed specification data, not a user input, so it's
# precomputed here in Python (mirrors lm3_calculations.py's _sv80_100_axles/_sv196_axles/_build_
# vehicle exactly) rather than reconstructed as Excel formulas. What DOES stay live in Excel is
# everything downstream of H_c/B_ext: dispersion widths and the worst-position search. ──────────

DAF_BY_LOAD = {100.0: 1.20, 130.0: 1.16, 165.0: 1.12, 180.0: 1.10, 225.0: 1.07}
GROUP_GAPS = [1.2, 5.0, 9.0]


def _sv80_100_axles(basic_load, gap):
    g1 = [0.0, 1.2, 2.4]
    g2 = [g1[-1] + gap, g1[-1] + gap + 1.2, g1[-1] + gap + 2.4]
    return g1 + g2, [basic_load] * 6


def _sv196_axles(gap):
    g1 = [0.0, 1.2, 2.4, 3.6, 4.8]
    start2 = g1[-1] + gap
    g2 = [start2, start2 + 1.2, start2 + 2.4, start2 + 3.6]
    start3 = g2[-1] + 4.0
    g3 = [start3, start3 + 1.6, start3 + 1.6 + 4.4]
    return g1 + g2 + g3, [165.0] * 5 + [165.0] * 4 + [180.0, 180.0, 100.0]


def _build_vehicle_axles(name, gap):
    if name == "SV80":
        pos, basic = _sv80_100_axles(130.0, gap)
    elif name == "SV100":
        pos, basic = _sv80_100_axles(165.0, gap)
    elif name == "SV196":
        pos, basic = _sv196_axles(gap)
    else:
        raise ValueError(name)
    daf = [DAF_BY_LOAD[b] for b in basic]
    return pos, basic, daf


def _minmax_overlap_formula(offset_cell, pos_cell, half_B, B_ext):
    """Element-wise MAX(0, MIN(offset+pos+half_B, B_ext) - MAX(offset+pos-half_B, 0)) using the
    a/b -> (a+b+-ABS(a-b))/2 min/max identities, since Excel's own MIN/MAX AGGREGATE an array
    instead of clipping it element-wise, but single-argument ABS() does vectorize correctly."""
    R = f"({offset_cell}+{pos_cell}+{half_B})"
    L = f"({offset_cell}+{pos_cell}-{half_B})"
    clipped_right = f"(({R}+{B_ext}-ABS({R}-{B_ext}))/2)"
    clipped_left = f"(({L}+ABS({L}))/2)"
    diff = f"({clipped_right}-{clipped_left})"
    return f"(({diff}+ABS({diff}))/2)"


def build_vehicle_gap_block(ws, wb, sheet_name, r, vehicle_name, gap, half_B_name, disp_B_name, disp_LL_name):
    """One (vehicle, gap-candidate) block: axle table (fixed numbers) + the 4 breakpoint offsets
    per axle (live formulas) + the total landed load at each breakpoint (live SUMPRODUCT array
    formula) + the block's governing (maximum) load. Returns (next_row, block_max_cell_addr)."""
    pos, basic, daf = _build_vehicle_axles(vehicle_name, gap)
    n = len(pos)

    ws.cell(r, 1, f"{vehicle_name} — inter-group gap = {gap:.1f} m").font = Font(bold=True, italic=True)
    r += 1
    ws.cell(r, 1, "Axle"); ws.cell(r, 2, "Position (m)"); ws.cell(r, 3, "Basic Load (kN)")
    ws.cell(r, 4, "DAF"); ws.cell(r, 5, "Factored Load (kN)")
    for c in range(1, 6):
        ws.cell(r, c).font = BOLD
    r += 1
    axle_first = r
    for i in range(n):
        ws.cell(r, 1, i + 1)
        ws.cell(r, 2, pos[i]).number_format = "0.00"
        ws.cell(r, 3, basic[i]).number_format = "0.0"
        ws.cell(r, 4, daf[i]).number_format = "0.00"
        fc = ws.cell(r, 5, f"=C{r}*D{r}")
        fc.number_format = "0.00"
        r += 1
    axle_last = r - 1

    r += 1
    ws.cell(r, 1, "Breakpoint candidate offset").font = BOLD
    ws.cell(r, 2, "Offset (m)").font = BOLD
    ws.cell(r, 3, "Total landed load at this offset (kN/m)").font = BOLD
    r += 1
    bp_first = r
    half_B = half_B_name
    for i in range(n):
        axle_row = axle_first + i
        pos_ref = f"$B${axle_row}"
        for kind, formula in [
            ("right=0", f"=-{half_B}-{pos_ref}"),
            ("right=B_ext", f"=B_ext-{half_B}-{pos_ref}"),
            ("left=0", f"={half_B}-{pos_ref}"),
            ("left=B_ext", f"=B_ext+{half_B}-{pos_ref}"),
        ]:
            ws.cell(r, 1, f"axle {i + 1}, {kind}")
            ws.cell(r, 2, formula).number_format = "0.000"
            pos_range = f"$B${axle_first}:$B${axle_last}"
            load_range = f"$E${axle_first}:$E${axle_last}"
            overlap = _minmax_overlap_formula(f"$B{r}", pos_range, half_B, "B_ext")
            load_formula = f"=SUMPRODUCT({load_range}*{overlap})/{disp_B_name}/{disp_LL_name}"
            ws.cell(r, 3, load_formula).number_format = "0.00"
            r += 1
    bp_last = r - 1

    r += 1
    ws.cell(r, 1, f"{vehicle_name} block max, gap={gap:.1f}m (kN/m)")
    max_cell = ws.cell(r, 2, f"=MAX(C{bp_first}:C{bp_last})")
    max_cell.number_format = "0.00"
    max_addr = f"'{sheet_name}'!$B${r}"
    r += 2
    return r, max_addr


def build_lm3(wb):
    ws = wb.create_sheet("LM3")
    r = 1
    r = title(ws, r, "LM3 Calculations — Special Vehicle (SV) Maximum Vertical Load & Braking")

    r = section(ws, r, "Wheel Dispersal Through Fill")
    r = label_value(ws, r, "Wheel contact patch, L_L direction (m)", 0.35, fmt="0.00")
    defname(wb, "LM3", "sv_contact_t", r - 1, 2)
    r = label_value(ws, r, "Wheel contact patch, B_ext direction (m)", 0.35, fmt="0.00")
    defname(wb, "LM3", "sv_contact_l", r - 1, 2)
    r = label_value(ws, r, "Wheel spacing, L_L direction (m)", 2.65, fmt="0.00")
    defname(wb, "LM3", "sv_wheel_spacing", r - 1, 2)
    r = label_value(ws, r, "tan(30deg)", "=TAN(RADIANS(30))", fmt="0.0000")
    defname(wb, "LM3", "lm3_tan_30", r - 1, 2)
    r = label_value(
        ws, r, "Dispersed width per wheel, L_L direction = contact_t + 2*tan30*H_c (m)",
        "=sv_contact_t+2*lm3_tan_30*H_c", fmt="0.000",
    )
    r_disp_single = r - 1
    r = label_value(
        ws, r, "Gap between wheels' dispersed zones = wheel_spacing - dispersed width (m)",
        f"=sv_wheel_spacing-B{r_disp_single}", fmt="0.000",
    )
    r_gap = r - 1
    r = label_value(
        ws, r, "disp_LL (m) — merged if gap<0, else zones stay separate",
        f"=IF(B{r_gap}>=0, 2*B{r_disp_single}, sv_wheel_spacing+B{r_disp_single})", fmt="0.000",
    )
    defname(wb, "LM3", "disp_LL", r - 1, 2)
    r = label_value(
        ws, r, "disp_B (m) — dispersed width per axle, B_ext direction",
        "=sv_contact_l+2*lm3_tan_30*H_c", fmt="0.000",
    )
    defname(wb, "LM3", "disp_B", r - 1, 2)
    r = label_value(ws, r, "half_B = disp_B / 2 (m)", "=disp_B/2", fmt="0.000")
    defname(wb, "LM3", "half_B", r - 1, 2)
    r += 1

    r = section(ws, r, "Worst-Case Position — SV80")
    r, sv80_g1 = build_vehicle_gap_block(ws, wb, "LM3", r, "SV80", 1.2, "half_B", "disp_B", "disp_LL")
    r, sv80_g2 = build_vehicle_gap_block(ws, wb, "LM3", r, "SV80", 5.0, "half_B", "disp_B", "disp_LL")
    r, sv80_g3 = build_vehicle_gap_block(ws, wb, "LM3", r, "SV80", 9.0, "half_B", "disp_B", "disp_LL")
    ws.cell(r, 1, "SV80 governing (max over all 3 gaps), kN/m")
    ws.cell(r, 2, f"=MAX({sv80_g1},{sv80_g2},{sv80_g3})").number_format = "0.00"
    defname(wb, "LM3", "sv80_max", r, 2)
    r += 2

    r = section(ws, r, "Worst-Case Position — SV100")
    r, sv100_g1 = build_vehicle_gap_block(ws, wb, "LM3", r, "SV100", 1.2, "half_B", "disp_B", "disp_LL")
    r, sv100_g2 = build_vehicle_gap_block(ws, wb, "LM3", r, "SV100", 5.0, "half_B", "disp_B", "disp_LL")
    r, sv100_g3 = build_vehicle_gap_block(ws, wb, "LM3", r, "SV100", 9.0, "half_B", "disp_B", "disp_LL")
    ws.cell(r, 1, "SV100 governing (max over all 3 gaps), kN/m")
    ws.cell(r, 2, f"=MAX({sv100_g1},{sv100_g2},{sv100_g3})").number_format = "0.00"
    defname(wb, "LM3", "sv100_max", r, 2)
    r += 2

    r = section(ws, r, "Worst-Case Position — SV196")
    r, sv196_g1 = build_vehicle_gap_block(ws, wb, "LM3", r, "SV196", 1.2, "half_B", "disp_B", "disp_LL")
    r, sv196_g2 = build_vehicle_gap_block(ws, wb, "LM3", r, "SV196", 5.0, "half_B", "disp_B", "disp_LL")
    r, sv196_g3 = build_vehicle_gap_block(ws, wb, "LM3", r, "SV196", 9.0, "half_B", "disp_B", "disp_LL")
    ws.cell(r, 1, "SV196 governing (max over all 3 gaps), kN/m")
    ws.cell(r, 2, f"=MAX({sv196_g1},{sv196_g2},{sv196_g3})").number_format = "0.00"
    defname(wb, "LM3", "sv196_max", r, 2)
    r += 2

    r = section(ws, r, "Selected Vehicle Result")
    r = label_value(
        ws, r, "max_V_per_m — selected by Inputs!sv_vehicle (kN/m)",
        '=IF(sv_vehicle="SV80",sv80_max,IF(sv_vehicle="SV100",sv100_max,sv196_max))', fmt="0.00",
    )
    defname(wb, "LM3", "max_V_per_m", r - 1, 2)
    r += 1

    r = section(ws, r, "Braking and Acceleration Forces")
    r = label_value(
        ws, r, "Braking coefficient delta (SV80=0.50, SV100=0.40, SV196=0.25)",
        '=IF(sv_vehicle="SV80",0.5,IF(sv_vehicle="SV100",0.4,0.25))', fmt="0.00",
    )
    r_delta = r - 1
    r = label_value(
        ws, r, "Basic axle load w for braking (SV80=130, SV100=165, SV196=165, heaviest common group) (kN)",
        '=IF(sv_vehicle="SV80",130,165)', fmt="0.0",
    )
    r_w = r - 1
    ws.cell(r, 1, (
        "Total braking force = delta x (sum of basic axle loads) — see Assumptions for the exact "
        "per-vehicle axle grouping this simplifies (SV80/SV100: 6 axles at one basic load; SV196: "
        "9 axles at 165kN plus 2 at 180kN plus 1 at 100kN, all at delta=0.25)."
    ))
    ws.cell(r, 1).font = Font(italic=True, color="808080")
    r += 1
    r = label_value(
        ws, r, "Total braking force (kN)",
        f'=IF(sv_vehicle="SV196", 0.25*(9*165+2*180+1*100), B{r_delta}*6*B{r_w})', fmt="0.00",
    )
    r_totbrk = r - 1
    defname(wb, "LM3", "total_braking", r - 1, 2)
    r = label_value(ws, r, "Q_brk_per_m = total_braking / L_L (kN/m)", f"=B{r_totbrk}/L_L", fmt="0.00")
    defname(wb, "LM3", "Q_brk_per_m", r - 1, 2)
    r = label_value(
        ws, r, "Vertical load from fill above culvert = UDL_total * B_ext (kN)",
        "=UDL_total*B_ext", fmt="0.00",
    )
    r_fillv = r - 1
    r = label_value(
        ws, r, "Max friction = (max_V_per_m + fill_vertical) * tan30 (kN)",
        f"=(max_V_per_m+B{r_fillv})*lm3_tan_30", fmt="0.00",
    )
    defname(wb, "LM3", "max_friction", r - 1, 2)
    ws.cell(r, 1).font = Font(italic=True, color="808080")

    autosize(ws, {"A": 62, "B": 16, "C": 34, "D": 10, "E": 16})
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 85
    return ws


# ── Table B.4 / B.5 / B.6 — shared sliding & overturning check ────────────────────────────────
# Mirrors table_b4.py's common_terms()/model_check()/sliding_check() exactly: B.4 is
# favourable=False (maximum/unfavourable self-weight); B.5 is favourable=True (minimum); B.6 is
# favourable=True plus a per-combo buoyancy uplift subtracted from V_d. All three tables share
# this one generator, parameterised, so the formula structure only has to be got right once.

def build_common_terms(ws, wb, r, combo, favourable):
    """Returns (next_row, refs) — refs holds cell addresses (this sheet) for the quantities
    model_check() needs: active_surcharge, active_backfill, passive_surcharge, passive_backfill,
    total_passive, common_vertical."""
    label = COMBO_LABELS[combo]
    r = section(ws, r, f"Common Terms — {label} ({'favourable/min' if favourable else 'unfavourable/max'})")

    Ka_earth, Kmax = f"Ka_earth_{combo}", f"Kmax_{combo}"
    if favourable:
        gamma_self, gamma_super = f"SelfWeight_inf_{combo}", f"Superimposed_inf_{combo}"
        road_dev, sd_ec = "road_dev_fav", "1"
    else:
        gamma_self, gamma_super = f"SelfWeight_sup_{combo}", f"Superimposed_sup_{combo}"
        road_dev, sd_ec = "road_dev_unfav", "gamma_sd_ec"

    r = label_value(ws, r, "road_udl_char = UDL_1 (kN/m)", "=UDL_1", fmt="0.00")
    road_udl = f"B{r - 1}"
    r = label_value(ws, r, "fill_udl_char = UDL_total - UDL_1 (kN/m)", "=UDL_total-UDL_1", fmt="0.00")
    fill_udl = f"B{r - 1}"
    r = label_value(ws, r, "surcharge_road = road_dev * road_udl_char (kN/m)", f"={road_dev}*{road_udl}", fmt="0.00")
    surch_road = f"B{r - 1}"

    r = label_value(
        ws, r, "active_surcharge = Ka_earth*gamma_super*(surcharge_road+fill_udl_char)*H_ext (kN)",
        f"={Ka_earth}*{gamma_super}*({surch_road}+{fill_udl})*H_ext", fmt="0.00",
    )
    active_surcharge = f"B{r - 1}"
    r = label_value(
        ws, r, "passive_surcharge = Kmax*gamma_super*(surcharge_road+fill_udl_char)*H_ext (kN)",
        f"={Kmax}*{gamma_super}*({surch_road}+{fill_udl})*H_ext", fmt="0.00",
    )
    passive_surcharge = f"B{r - 1}"

    r = label_value(ws, r, "backfill_pressure = gamma_backfill * H_ext (kN/m2)", "=gamma_backfill*H_ext", fmt="0.00")
    backfill_pressure = f"B{r - 1}"
    r = label_value(
        ws, r, "active_backfill = Ka_earth*gamma_self*backfill_pressure*H_ext/2 (kN)",
        f"={Ka_earth}*{gamma_self}*{backfill_pressure}*H_ext/2", fmt="0.00",
    )
    active_backfill = f"B{r - 1}"
    r = label_value(
        ws, r, "passive_backfill = Kmax*gamma_self*backfill_pressure*H_ext/2 (kN)",
        f"={Kmax}*{gamma_self}*{backfill_pressure}*H_ext/2", fmt="0.00",
    )
    passive_backfill = f"B{r - 1}"
    r = label_value(
        ws, r, "total_passive = passive_surcharge + passive_backfill (kN)",
        f"={passive_surcharge}+{passive_backfill}", fmt="0.00",
    )
    total_passive = f"B{r - 1}"

    r = label_value(
        ws, r, "road_vertical = gamma_super * gamma_sd_ec * road_dev * road_udl_char * B_ext (kN)",
        f"={gamma_super}*{sd_ec}*{road_dev}*{road_udl}*B_ext", fmt="0.00",
    )
    road_vertical = f"B{r - 1}"
    r = label_value(
        ws, r, "fill_vertical = gamma_super * gamma_sd_ec * fill_udl_char * B_ext (kN)",
        f"={gamma_super}*{sd_ec}*{fill_udl}*B_ext", fmt="0.00",
    )
    fill_vertical = f"B{r - 1}"
    r = label_value(ws, r, "self_weight_vertical = gamma_self * W_box (kN)", f"={gamma_self}*W_box", fmt="0.00")
    self_weight_vertical = f"B{r - 1}"
    r = label_value(
        ws, r, "common_vertical = road_vertical + fill_vertical + self_weight_vertical (kN)",
        f"={road_vertical}+{fill_vertical}+{self_weight_vertical}", fmt="0.00",
    )
    common_vertical = f"B{r - 1}"

    refs = {
        "active_surcharge": active_surcharge, "active_backfill": active_backfill,
        "passive_surcharge": passive_surcharge, "passive_backfill": passive_backfill,
        "total_passive": total_passive, "common_vertical": common_vertical,
    }
    return r, refs


def build_model_check(ws, wb, r, model, combo, common, buoyancy_ref=None):
    """Mirrors table_b4.py's model_check(). Returns (next_row, refs) with margin/ot_margin/ok/
    ot_ok cell addresses."""
    label = COMBO_LABELS[combo]
    r = section(ws, r, f"{model} Scenario — {label}")

    Ka_traffic, Kmax = f"Ka_traffic_{combo}", f"Kmax_{combo}"
    gamma_Q, gamma_M = f"RoadTraffic_sup_{combo}", f"MaterialM_{combo}"
    udl_coeff = 20.0 if model == "LM1" else 30.0

    r = label_value(
        ws, r, "active_line_load = Ka_traffic*gamma_Q*F_hll_1m_coeff (kN)",
        f"={Ka_traffic}*{gamma_Q}*F_hll_1m_coeff", fmt="0.00",
    )
    active_line_load = f"B{r - 1}"
    r = label_value(
        ws, r, f"active_udl = Ka_traffic*gamma_Q*{udl_coeff:.0f}*H_ext (kN)",
        f"={Ka_traffic}*{gamma_Q}*{udl_coeff}*H_ext", fmt="0.00",
    )
    active_udl = f"B{r - 1}"

    if model == "LM1":
        braking_char_formula = "=Q_lk/L_L"
        vertical_char_formula = "=lane1_udl*B_ext+patch_load*disp_m*2"
    else:
        braking_char_formula = "=Q_brk_per_m"
        vertical_char_formula = "=max_V_per_m"

    r = label_value(ws, r, "braking_char (kN)", braking_char_formula, fmt="0.00")
    braking_char = f"B{r - 1}"
    r = label_value(ws, r, "braking = gamma_Q * braking_char (kN)", f"={gamma_Q}*{braking_char}", fmt="0.00")
    braking = f"B{r - 1}"

    r = label_value(
        ws, r, "total_active = active_surcharge+active_backfill+active_line_load+active_udl+braking (kN)",
        f"={common['active_surcharge']}+{common['active_backfill']}+{active_line_load}+{active_udl}+{braking}",
        fmt="0.00",
    )
    total_active = f"B{r - 1}"

    r = label_value(ws, r, "vertical_char (kN)", vertical_char_formula, fmt="0.00")
    vertical_char = f"B{r - 1}"
    r = label_value(ws, r, "vertical = gamma_Q * vertical_char (kN)", f"={gamma_Q}*{vertical_char}", fmt="0.00")
    vertical = f"B{r - 1}"

    if buoyancy_ref:
        r = label_value(
            ws, r, "V_d = common_vertical + vertical - buoyancy (kN)",
            f"={common['common_vertical']}+{vertical}-{buoyancy_ref}", fmt="0.00",
        )
    else:
        r = label_value(
            ws, r, "V_d = common_vertical + vertical (kN)",
            f"={common['common_vertical']}+{vertical}", fmt="0.00",
        )
    V_d = f"B{r - 1}"

    r = label_value(
        ws, r, "delta_d = ATAN(TAN(RADIANS(phi_founding))/gamma_M) (deg)",
        f"=DEGREES(ATAN(TAN(RADIANS(phi_founding))/{gamma_M}))", fmt="0.00",
    )
    delta_d = f"B{r - 1}"
    r = label_value(
        ws, r, "max_Rd = V_d * TAN(RADIANS(delta_d)) (kN)",
        f"={V_d}*TAN(RADIANS({delta_d}))", fmt="0.00",
    )
    max_Rd = f"B{r - 1}"
    r = label_value(
        ws, r, "friction_required = total_active - total_passive (kN)",
        f"={total_active}-{common['total_passive']}", fmt="0.00",
    )
    friction_required = f"B{r - 1}"
    r = label_value(ws, r, "SLIDING margin = max_Rd - friction_required (kN)", f"={max_Rd}-{friction_required}", fmt="0.00")
    margin = f"B{r - 1}"
    r = label_value(ws, r, "Sliding OK? (margin >= 0)", f"={margin}>=0", fmt="General")
    ok = f"B{r - 1}"
    r = label_value(
        ws, r, "UR_sliding = MAX(0,friction_required)/max_Rd (%)",
        f"=MAX(0,{friction_required})/{max_Rd}*100", fmt="0.0",
    )
    ur_sliding = f"B{r - 1}"

    r = label_value(
        ws, r, "M_active = act_surch*(H_ext/2)+act_bkfl*(H_ext/3)+line_load*H_ext+udl*(H_ext/2)+braking*H_ext (kNm)",
        f"={common['active_surcharge']}*(H_ext/2)+{common['active_backfill']}*(H_ext/3)"
        f"+{active_line_load}*H_ext+{active_udl}*(H_ext/2)+{braking}*H_ext", fmt="0.00",
    )
    M_active = f"B{r - 1}"
    r = label_value(
        ws, r, "M_passive = pass_surch*(H_ext/2) + pass_bkfl*(H_ext/3) (kNm)",
        f"={common['passive_surcharge']}*(H_ext/2)+{common['passive_backfill']}*(H_ext/3)", fmt="0.00",
    )
    M_passive = f"B{r - 1}"
    r = label_value(ws, r, "M_driving = MAX(0, M_active - M_passive) (kNm)", f"=MAX(0,{M_active}-{M_passive})", fmt="0.00")
    M_driving = f"B{r - 1}"
    r = label_value(ws, r, "M_stabilizing = V_d * B_ext/2 (kNm)", f"={V_d}*B_ext/2", fmt="0.00")
    M_stabilizing = f"B{r - 1}"
    r = label_value(
        ws, r, "OVERTURNING margin = M_stabilizing - M_driving (kNm)", f"={M_stabilizing}-{M_driving}", fmt="0.00",
    )
    ot_margin = f"B{r - 1}"
    r = label_value(ws, r, "Overturning OK? (ot_margin >= 0)", f"={ot_margin}>=0", fmt="General")
    ot_ok = f"B{r - 1}"
    r = label_value(
        ws, r, "UR_overturning = MAX(0,M_driving)/M_stabilizing (%)",
        f"=MAX(0,{M_driving})/{M_stabilizing}*100", fmt="0.0",
    )
    ur_overturning = f"B{r - 1}"

    refs = {
        "margin": margin, "ok": ok, "ur_sliding": ur_sliding,
        "ot_margin": ot_margin, "ot_ok": ot_ok, "ur_overturning": ur_overturning,
    }
    return r, refs


def build_combo_block(ws, wb, r, combo, favourable, buoyancy_char_ref=None):
    label = COMBO_LABELS[combo]
    r = title(ws, r, f"Sliding & Overturning at {label}", span=2)

    buoyancy_ref = None
    if buoyancy_char_ref:
        gamma_water = f"WaterPressure_sup_{combo}"
        r = label_value(
            ws, r, f"F_buoyancy = {gamma_water} * F_buoyancy_char (kN)",
            f"={gamma_water}*{buoyancy_char_ref}", fmt="0.00",
        )
        buoyancy_ref = f"B{r - 1}"

    r, common = build_common_terms(ws, wb, r, combo, favourable)
    r, lm1 = build_model_check(ws, wb, r, "LM1", combo, common, buoyancy_ref)
    r, lm3 = build_model_check(ws, wb, r, "LM3", combo, common, buoyancy_ref)

    r = label_value(
        ws, r, "Governing (sliding) — LM1 if its margin is smaller",
        f'=IF({lm1["margin"]}<{lm3["margin"]},"LM1","LM3")', fmt="General",
    )
    r = label_value(
        ws, r, "Governing (overturning) — LM1 if its margin is smaller",
        f'=IF({lm1["ot_margin"]}<{lm3["ot_margin"]},"LM1","LM3")', fmt="General",
    )
    r += 1

    combo_refs = {
        "sliding_margin": f"MIN({lm1['margin']},{lm3['margin']})",
        "ot_margin": f"MIN({lm1['ot_margin']},{lm3['ot_margin']})",
        "lm1": lm1, "lm3": lm3,
    }
    return r, combo_refs


def build_stability_sheet(wb, sheet_name, display_title, favourable, with_buoyancy=False):
    ws = wb.create_sheet(sheet_name)
    r = 1
    r = title(ws, r, display_title)
    ws.cell(r, 1, "Sliding and overturning, LM1 and LM3, all four limit states — the smaller margin governs.")
    ws.cell(r, 1).font = Font(italic=True, color="808080")
    r += 2

    buoyancy_char_ref = None
    if with_buoyancy:
        r = section(ws, r, "Buoyancy (Archimedes, submerged external cross-section)")
        r = label_value(ws, r, "Submerged height = MIN(h_wt, H_ext) (m)", "=MIN(h_wt,H_ext)", fmt="0.00")
        submerged = f"B{r - 1}"
        r = label_value(
            ws, r, "F_buoyancy_char = gamma_w * B_ext * submerged height (kN)",
            f"=gamma_w*B_ext*{submerged}", fmt="0.00",
        )
        buoyancy_char_ref = f"B{r - 1}"
        r += 1

    combo_results = {}
    for combo in COMBOS:
        r, combo_results[combo] = build_combo_block(ws, wb, r, combo, favourable, buoyancy_char_ref)

    autosize(ws, {"A": 78, "B": 16})
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 85
    return ws, combo_results


def build_summary(wb, table_refs_by_sheet):
    """table_refs_by_sheet: {sheet_name: combo_results} for TableB4/B5/B6, each combo_results
    as returned by build_stability_sheet — used to find the governing (highest utilisation %)
    case across all 4 combos and both traffic models, per sheet."""
    ws = wb.create_sheet("Summary")
    r = 1
    r = title(ws, r, "Summary — Governing Utilisation")
    ws.cell(r, 1, "Highest utilisation (%) across all four limit states and both LM1/LM3, per table.")
    ws.cell(r, 1).font = Font(italic=True, color="808080")
    r += 2

    ws.cell(r, 1, "Check"); ws.cell(r, 2, "Utilisation (%)"); ws.cell(r, 3, "Status")
    for c in (1, 2, 3):
        ws.cell(r, c).font = BOLD
    r += 1

    display_names = {"TableB4": "Table B.4", "TableB5": "Table B.5", "TableB6": "Table B.6"}
    for sheet_name, combo_results in table_refs_by_sheet.items():
        for check_key, check_label in [("ur_sliding", "Sliding"), ("ur_overturning", "Overturning")]:
            cells = []
            for combo in COMBOS:
                cells.append(f"'{sheet_name}'!{combo_results[combo]['lm1'][check_key]}")
                cells.append(f"'{sheet_name}'!{combo_results[combo]['lm3'][check_key]}")
            max_formula = f"=MAX({','.join(cells)})"
            ws.cell(r, 1, f"{display_names[sheet_name]} — {check_label}")
            ur_cell = ws.cell(r, 2, max_formula)
            ur_cell.number_format = "0.0"
            status_cell = ws.cell(r, 3, f'=IF(B{r}<=100,"OK","Review required")')
            r += 1

    r += 1
    ws.cell(r, 1, "Conditional formatting: green if <= 100%, red if > 100%.")
    ws.cell(r, 1).font = Font(italic=True, color="808080")

    # Conditional formatting on the Utilisation column
    from openpyxl.formatting.rule import CellIsRule
    data_first_row = 6
    data_last_row = data_first_row + 6 * 2 - 1  # 3 tables x 2 checks each
    rng = f"B{data_first_row}:B{data_last_row}"
    ws.conditional_formatting.add(
        rng, CellIsRule(operator="lessThanOrEqual", formula=["100"], fill=OK_FILL)
    )
    ws.conditional_formatting.add(
        rng, CellIsRule(operator="greaterThan", formula=["100"], fill=BAD_FILL)
    )

    autosize(ws, {"A": 30, "B": 16, "C": 18})
    ws.sheet_view.showGridLines = False
    return ws


def build_assumptions(wb):
    ws = wb.create_sheet("Assumptions")
    r = 1
    r = title(ws, r, "Assumptions")

    assumptions = [
        "Design is carried out on a 1.0 m strip basis.",
        "The structure has no longitudinal joints, so full load dispersal through the fill can be "
        "considered (PD6694-1 Cl. 10.2.7) — dispersal is not curtailed by a segment joint.",
        "The Transverse Dispersal formula assumes the dispersed wheel width is at least the 1.0 m "
        "design strip width. This requires H_c >= 0.52 m — not checked in this workbook.",
        "Per PD6694-1 Cl. 10.2.1, dispersal through fill is only valid for H_c >= 0.6 m; below "
        "that the structure should be treated as a normal bridge deck with undispersed traffic "
        "loading — not enforced or flagged here.",
        "The Transverse Dispersal formula assumes only two adjacent wheels' dispersion zones "
        "overlap in the critical 1 m strip (lanes 1 & 2 only) — not extended to 3+ overlapping "
        "wheels.",
        "Road construction (cover Layer 1) is treated separately from fill (remaining layers) for "
        "the +55%/-40% construction-thickness deviation — an assumption carried over from the "
        "source Streamlit app, not explicitly stated in PD6694-1.",
        "LM3's worst vehicle position is found by evaluating the exact breakpoints of the "
        "(piecewise-linear) landed-load-vs-offset function, rather than a fine numerical scan — "
        "mathematically equivalent to (and more precise than) the Streamlit app's 0.01 m grid "
        "search; cross-checked against it for SV196 (163.8 kN/m, matching to 3 s.f.).",
        "LM3 braking force = delta x (sum of characteristic axle loads), delta = 0.50/0.40/0.25 "
        "for SV80/SV100/SV196 (NA.2.18.1) — algebraically identical to summing per-axle-group "
        "braking forces, since delta is constant per vehicle.",
        "Table B.6 buoyancy = gamma_w x B_ext x MIN(h_wt, H_ext) (Archimedes, submerged external "
        "cross-section) — a discrete uplift force, not a change to backfill unit weight or earth "
        "pressure coefficients below the water table.",
        "Bearing pressure (PD6694-1 Cl. 10.3.2) is not covered by this workbook — sliding and "
        "overturning only.",
        "This workbook is a direct transcription of the culvert-stability Streamlit app's "
        "calculation logic into live Excel formulas — see that app's own Assumptions tab for "
        "further detail on individual modelling choices.",
    ]
    for a in assumptions:
        ws.cell(r, 1, f"- {a}")
        ws.cell(r, 1).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 30
        r += 1

    autosize(ws, {"A": 110})
    ws.sheet_view.showGridLines = False
    return ws


if __name__ == "__main__":
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    ws_inputs = build_inputs(wb)
    ws_pf = build_partial_factors(wb)
    ws_global = build_global_calcs(wb)
    ws_lm1 = build_lm1(wb)
    ws_lm3 = build_lm3(wb)
    ws_b4, b4_refs = build_stability_sheet(wb, "TableB4", "Table B.4 — Sliding & Overturning (Maximum Vertical)", favourable=False)
    ws_b5, b5_refs = build_stability_sheet(wb, "TableB5", "Table B.5 — Sliding & Overturning (Minimum Vertical)", favourable=True)
    ws_b6, b6_refs = build_stability_sheet(wb, "TableB6", "Table B.6 — Sliding & Overturning (Minimum Vertical + Water Table)", favourable=True, with_buoyancy=True)
    ws_summary = build_summary(wb, {"TableB4": b4_refs, "TableB5": b5_refs, "TableB6": b6_refs})
    ws_assumptions = build_assumptions(wb)
    check_name_collisions(wb)

    # --- Final polish: freeze panes, tab colours, sheet order, active sheet ---
    for ws in (ws_pf, ws_global, ws_lm1, ws_lm3, ws_b4, ws_b5, ws_b6, ws_summary, ws_assumptions):
        ws.freeze_panes = "A2"

    INPUT_TAB = "ED7D31"     # orange — Inputs
    CALC_TAB = "8EA9DB"      # mid blue — working/calc sheets
    TABLE_TAB = "203864"     # dark navy — PD6694-1 tables
    SUMMARY_TAB = "548235"   # green — Summary
    NOTE_TAB = "A6A6A6"      # grey — Assumptions

    ws_inputs.sheet_properties.tabColor = INPUT_TAB
    ws_pf.sheet_properties.tabColor = CALC_TAB
    ws_global.sheet_properties.tabColor = CALC_TAB
    ws_lm1.sheet_properties.tabColor = CALC_TAB
    ws_lm3.sheet_properties.tabColor = CALC_TAB
    ws_b4.sheet_properties.tabColor = TABLE_TAB
    ws_b5.sheet_properties.tabColor = TABLE_TAB
    ws_b6.sheet_properties.tabColor = TABLE_TAB
    ws_summary.sheet_properties.tabColor = SUMMARY_TAB
    ws_assumptions.sheet_properties.tabColor = NOTE_TAB

    # Put Summary right after Inputs so results are visible without scrolling through
    # every calc sheet; everything else stays in calculation order.
    wb.move_sheet("Summary", offset=-(wb.sheetnames.index("Summary") - 1))

    wb.active = wb.sheetnames.index("Inputs")
    for name in wb.sheetnames:
        wb[name].sheet_view.tabSelected = (name == "Inputs")

    check_name_collisions(wb)
    wb.save("Culvert_Stability.xlsx")
    print("Saved Culvert_Stability.xlsx with sheets:", wb.sheetnames)
