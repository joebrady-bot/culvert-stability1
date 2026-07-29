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

## Maximum Vertical Load on Top of Culvert — LM1 (calculated)

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

## Braking and Acceleration Forces — LM1 (calculated)

PD6694-1 Cl. 10.2.8.2, applied to BS EN 1991-2 Cl. 4.4.1. PD6694-1 labels the reduction-factor comparison
length "the overall length of the structure (LL)" — but that's the structure's extent *in the direction
of travel*, which for this culvert's orientation (travel ∥ `B`) is `B_ext`, not the project's `L_L`
(Overall Length) input. Both the `Q_lk_raw` formula's `L` and the reduction factor use `B_ext`.

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| Raw Braking Force | `Q_lk_raw` | kN | `0.6·alpha_Q1·(2·Q1k) + 0.1·alpha_q1·q1k·w1·L` | `L = B_ext` (loaded length in direction of travel); `alpha_Q1 = alpha_q1 = 1`; `w1 = 3.0 m` (notional lane width) |
| Clamped Braking Force | `Q_lk_clamped` | kN | `clamp(Q_lk_raw, 180·alpha_Q1, 900)` | BS EN 1991-2 Cl. 4.4.1 limits |
| Reduction Factor | `eta_braking` | — | `1.0` if `H_c<0.6m`; `(B_ext−H_c)/(B_ext−0.6)` if `0.6m≤H_c<B_ext`; `0` if `H_c≥B_ext` | PD6694-1 Cl. 10.2.8.2, buried-structure reduction |
| Design Braking Force | `Q_lk` | kN | `eta_braking × Q_lk_clamped` | |

## Partial Factors (reference, `partial_factors.py`)

NA to BS EN 1990:2002+A1:2005. Shared across LM1 and LM3 calculations — look these up rather than
hardcoding a factor value in a calc module. SLS: Cl. NA.2.3.9; EQU: Table NA.A2.4(A); STR/GEO Comb1:
Table NA.A2.4(B); STR/GEO Comb2: Table NA.A2.4(C). Displayed in the Assumptions tab.

| Quantity | Symbol | Dict Key (`UNFAVOURABLE` / `FAVOURABLE`) | SLS | EQU | STR/GEO C1 | STR/GEO C2 |
|---|---|---|---|---|---|---|
| Self weight of structure & backfill (unfav.) | `gamma_G;sup` | `"Self weight of structure & backfill, gamma_G;sup"` | 1.00 | 1.05 | 1.35 | 1.00 |
| Superimposed permanent load (unfav.) | `gamma_G;sup` | `"Superimposed permanent load, gamma_G;sup"` | 1.00 | 1.05 | 1.20 | 1.00 |
| Road traffic action on box (unfav.) | `gamma_Q;sup` | `"Road traffic action on box, gamma_Q;sup"` | 1.00 | 1.35 | 1.35 | 1.15 |
| Thermal actions (unfav.) | `gamma_Q;sup` | `"Thermal actions, gamma_Q;sup"` | 1.00 | 1.55 | 1.55 | 1.30 |
| Material factor to φ' (unfav.) | `gamma_M` | `"Material factor to phi', gamma_M"` | 1.00 | 1.10 | 1.00 | 1.25 |
| Vertical/horizontal water pressures (unfav.) | `gamma_G;sup` | `"Vertical and horizontal water pressures, gamma_G;sup"` | 0.00 | 1.00 | 1.00 | 1.00 |
| Self weight of structure & backfill (fav.) | `gamma_G;inf` | `"Self weight of structure & backfill, gamma_G;inf"` | 1.00 | 0.95 | 0.95 | 1.00 |
| Superimposed permanent load (fav.) | `gamma_G;inf` | `"Superimposed permanent load, gamma_G;inf"` | 1.00 | 0.95 | 0.95 | 1.00 |

Also: `ROAD_CONSTRUCTION_DEVIATION = {"unfavourable": 1.55, "favourable": 0.60}` — UK NA to BS EN 1991-1-1
Table NA.1 Cl. 5.2.3(3), road construction thickness deviation (+55% / −40%).

## Maximum Vertical Load on Top of Culvert — LM3 (calculated, `lm3_calculations.py`)

UK NA to BS EN 1991-2 Table NA.5 SV vehicle definitions + PD6694-1 Cl. 10.2.7 dispersal. Same direction
convention as LM1 (travel ∥ `B`). Worst-case vehicle position is found by an exhaustive numeric scan
across `B_ext` (not a fixed hand-derived formula) — confirmed against the D. Childs SV196 worked example:
the scan finds a *higher* load (163.8 kN/m, 4 axles) than the worked example's hand calc (151.4 kN, 3
axles), because PD6694-1 NOTE 2 to Figure 11 allows the hand method to simplify to a tractable subset of
overlapping axles, while the scan is exhaustive. Decision: keep the full scan result — see the
"Scan vs worked ex." decision in conversation history if this needs revisiting.

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| Dispersed Width per Wheel | `disp_LL_single` | m | `SV_CONTACT_T + 2×tan30°×H_c` | Contact patch 350×350 mm |
| Dispersed Width, L_L direction | `disp_LL` | m | `2×disp_LL_single` if wheel spacing (2.65 m) ≥ `disp_LL_single`, else `SV_WHEEL_SPACING + disp_LL_single` | Whether the two wheels of an axle merge |
| Dispersed Width per Axle, B_ext direction | `disp_B` | m | `SV_CONTACT_L + 2×tan30°×H_c` | |
| Worst-Case Offset | `worst_offset` | m | found by scanning front-axle position across `B_ext` in 0.01 m steps | Front axle position relative to culvert's leading edge |
| Maximum Vertical Load | `max_V_per_m` | kN/m | `sum(axle_load × overlap/disp_B / disp_LL)` over all contributing axles at `worst_offset` | |

SV vehicle axle loads (`SV_VEHICLES` dict) are DAF-factored. SV196 confirmed against the worked example
(basic axle loads 100/180×2/165×9 kN; DAF 1.20/1.10/1.12 → 120/198×2/184.8×9 kN). SV80/SV100 carried over
from the old v1 build, marked as not yet re-verified against a worked example.

## Braking and Acceleration Forces — LM3 (calculated)

PD6694-1 Cl. 10.2.8.2, BS EN 1991-2 Cl. 4.4.4. Note this uses `basic_axle_loads` (unfactored), not the
DAF-factored `axle_loads` used for the vertical load check above. The distribution length is `L_L`
(Overall Length input) — PD6694-1 Cl. 10.2.8.2's "distributed... over a length of Lj", confirmed against
the worked example where `Lj = L_L = 20.6 m` for that scenario (a different structure length than our
current default of 10 m — set `L_L` accordingly to reproduce the worked example's 24 kN/m result).

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| Braking Coefficient | `SV_BRAKING_COEFF` (δ) | — | `0.25` | BS EN 1991-2 Cl. 4.4.4, fixed for all SV vehicles |
| Per-Axle-Group Braking | `Q_lk,s` | kN | `delta × basic_axle_load` | Grouped by consecutive axles sharing the same basic load (e.g. "axles 2 & 3") |
| Total Braking Force | `total_braking` | kN | `sum(count × delta × basic_axle_load)` over all axle groups | = `delta × GVW` (unfactored), just computed per-group for transparency |
| Design Braking Force | `Q_brk_per_m` | kN/m | `total_braking / L_L` | Distributed over the barrel length via in-plane rigidity |
| Fill Vertical Load | `fill_vertical` | kN | `UDL_total × B_ext` | Reuses `UDL_total` from Global Calculations (Self-weights) |
| Maximum Friction | `max_friction` | kN | `(max_V_per_m + fill_vertical) × tan30°` | `max_V_per_m` = this module's own computed worst-case vertical load (not the worked example's 151.4 kN) — friction check is correspondingly less conservative to reconcile against than the book |
| Governing Check | — | — | `Q_brk_per_m < max_friction` | If exceeded, PD6694-1 says load effects in the members need to be considered (not yet implemented) |
