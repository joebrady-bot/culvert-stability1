# Nomenclature

Reference table of user inputs and their symbols, for use across all calculation modules in the rebuild. Add new inputs to this file as they're defined so equations always reference a single, agreed source of truth.

## Culvert Geometry

| Input | Symbol | Units | Notes |
|---|---|---|---|
| Internal Width | `B` | m | |
| Internal Height | `H` | m | |
| Overall Length | `L_L` | m | |
| Wall Thickness | `t_w` | m | |
| Slab Thickness | `t_s` | m | |
| Concrete Density | `gamma_concrete` | kN/m³ | Default 25 |

## Water Table

| Input | Symbol | Units | Notes |
|---|---|---|---|
| Water Table | `h_wt` | m | Height relative to bottom of culvert |

## Road Geometry

| Input | Symbol | Units | Notes |
|---|---|---|---|
| Carriageway Width | `w_C` | m | |
| Lane Width | `w_L` | m | |

## Cover Details

User can input up to 3 layers, `i` = layer number.

| Input | Symbol | Units | Notes |
|---|---|---|---|
| Thickness | `t_i` | mm | |
| Unit Weight | `gamma_i` | kN/m³ | |

## Soil Properties

| Input | Symbol | Units | Notes |
|---|---|---|---|
| Backfill Friction Angle | `phi_backfill` | degrees | |
| Backfill Density | `gamma_backfill` | kN/m³ | |
| Founding Friction Angle | `phi_founding` | degrees | |
| Founding Density | `gamma_founding` | kN/m³ | |
| Overburden Depth | `H_ob` | m | |

## LM3 Vehicle Type

| Input | Options | Notes |
|---|---|---|
| SV Vehicle | Drop-down: `SV80`, `SV100`, `SV196` | |

## Derived Geometry (calculated)

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| External Width | `B_ext` | m | `B + 2 t_w` | |
| External Height | `H_ext` | m | `H + 2 t_s` | Assumes `t_s` applies to both top and bottom slab (symmetric) |
| Concrete Cross-sectional Area | `A_conc` | m² | `B_ext H_ext − B H` | Per 1 m length strip |

## Self-weights (calculated)

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| Box Self-weight | `W_box` | kN/m | `A_conc × gamma_concrete` | Per 1 m strip along culvert length |
| Cover Layer UDL | `UDL_i` | kN/m | `gamma_i × (t_i / 1000)` | Per layer, per 1 m length × 1 m width strip (not yet integrated over `B_ext`) |

## Horizontal Surcharge Model (calculated)

PD6694-1 Table 6 / Figure 2, for LM1, LM2 & LM3.

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| Horizontal Line Load | `F_hll` | kN | `330 × Kd` | `Kd` (= `Ka` or `K0`) is purpose-built, not yet defined — kept as plain text/placeholder, not linked to a real variable |
| Cover Depth to Structure | `H_c` | m | `sum(t_i) / 1000` | Sum of all defined cover layer thicknesses (PD6694-1 NOTE 5) |
| Reduction Factor | `reduction_factor` | — | `(1 − H_c/2)²` | Per PD6694-1 NOTE 5, for buried structures with less than 2 m of fill |
| Line Load on 1 m Strip | `F_hll_1m_coeff` | kN (coefficient of `Kd`) | `2 × reduction_factor × 330 / w_L` | Smears the two edge-of-lane line loads across the lane width `w_L` onto the project's 1 m strip basis; result stays symbolic in `Kd` until `Ka`/`K0` exist |
| Horizontal UDL, LM1 & LM2 | `F_hUDL_LM12` | kN/m² (coefficient of `Kd`) | `20 × Kd` | PD6694-1 Table 6, Normal highway traffic row; stays symbolic in `Kd` |
| Horizontal UDL, LM3 | `F_hUDL_LM3` | kN/m² (coefficient of `Kd`) | `30 × Kd` | PD6694-1 Table 6, Special vehicle traffic row (SV196/SV100); stays symbolic in `Kd` |

## Vertical Load on Top of Culvert — LM1 (calculated)

BS EN 1991-2 Cl. 4.2/4.3 (LM1) + PD6694-1 Cl. 10.2.7 (dispersal through fill). Direction convention:
direction of travel is parallel to `B`; lane widths (and this dispersal check) run in the `L_L` direction.

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| Number of Notional Lanes | `n1` | — | `Int(w_C / 3)` | BS EN 1991-2 4.2.3, standard carriageway band |
| Width of Remaining Area | `remaining_width` | m | `w_C − n1 × 3.0` | |
| UDL per Lane | `lane_udls[i]` | kN/m² | `alpha_qi × qik` | `alpha_q1=0.61, alpha_q2=2.2`; lane 3+ assumed = `alpha_qr=2.2` (not confirmed, only 2 lanes load currently) |
| TS Axle Load per Lane | `lane_ts[i]` | kN | `Qik` (300, 200, 100 for lanes 1–3) | BS EN 1991-2 Table 4.2 characteristic values |
| Dispersed Contact Patch | `disp_m` | m | `(400 + 2 × H_c[mm] × tan30°) / 1000` | Wheel contact patch 400×400 mm, dispersed through `H_c` at 30° (PD6694-1 Cl. 10.2.7) |
| Transverse Load on 1 m Strip | `F_transverse_1m` | kN/m | `b·W1/L1 + a·W2/L2` | PD6694-1 Figure 11; `W1,W2` = wheel loads (`lane_ts[i]/2`) of the two most heavily loaded adjacent lanes; `a` = dispersal overlap length; `b=1.0 m` |
| Longitudinal Patch Load | `patch_load` | kN/m | `F_transverse_1m / disp_m` | Load per axle after longitudinal dispersal |

**Open items to resolve:**
- "Edge of carriageway to headwall" clearance check (PD6694-1 Cl. 10.2.7a, curtailment by wing wall) is not yet implemented — no input currently captures this distance.
- `alpha_q3` (lane 3+ UDL factor) assumed equal to `alpha_qr` — confirm if a carriageway wide enough to load 3 lanes is ever expected.
- `w_L` (Lane Width input, currently defaults to 3.65 m) is *not* used in this section — the standard 3.0 m notional lane width is used instead, matching the worked example. Worth confirming whether `w_L` should instead default to/reuse this 3.0 m standard, since it's also used as the "effective lane width" in the Horizontal Surcharge Model section above.
