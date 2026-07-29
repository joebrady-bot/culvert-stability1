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

**Vehicle geometry/loads corrected 2026-07-29** against the actual source documents (`BS EN 1991-2.pdf`
and `NA to BS EN 1991-2.pdf`, both in the project folder) — the previous SV80/SV100 data (ported from the
old v1 build) was wrong in both axle count and load (v1 used 8/10 axles at a flat 100kN; the NA actually
specifies 6 axles each, at 130kN for SV80 and 165kN for SV100). Verified visually against Figure NA.1
(NA PDF p.8-9, doc p.4-5) and Table NA.2 (NA PDF p.11, doc p.7). SV196's DAF-factored axle loads were
already correct in composition (9×184.8, 2×198, 1×120 kN) but the axle *order/grouping* was wrong — the
real structure is group of 5×165kN, [critical gap], group of 4×165kN, fixed 4.0m, then 180/180/100kN
(1.6m/4.4m spacing) — now matches Figure NA.1(c) exactly.

**Key correction**: Figure NA.1 Key note 2 says the gap between the two main axle groups is "the critical
of 1,2 m or 5,0 m or 9,0 m" — i.e. not a single fixed value. `_worst_over_gaps()` tries all three and
keeps the worst, per vehicle. For SV196 at H_c=1.0m, B_ext=3.1m, gap=1.2m governs (it merges the 5- and
4-axle groups into one continuous 9-axle train at uniform 1.2m spacing).

Same direction convention as LM1 (travel ∥ `B`). Worst-case vehicle position is found by an exhaustive
numeric scan across `B_ext` (not a fixed hand-derived formula) — confirmed against the D. Childs SV196
worked example: the scan finds a *higher* load (163.8 kN/m, 4 axles) than the worked example's hand calc
(151.4 kN, 3 axles), because PD6694-1 NOTE 2 to Figure 11 allows the hand method to simplify to a
tractable subset of overlapping axles, while the scan is exhaustive. Decision: keep the full scan result.
This 163.8 kN/m result is unchanged by the geometry correction above (same governing local pattern).

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| Group Gap Candidates | `GROUP_GAP_CANDIDATES` | m | `[1.2, 5.0, 9.0]` | NA.1 Key note 2 — tried exhaustively, worst kept |
| DAF by Basic Load | `DAF_BY_LOAD` | — | `{100:1.20, 130:1.16, 165:1.12, 180:1.10, 225:1.07}` | Table NA.2 |
| Dispersed Width per Wheel | `disp_LL_single` | m | `SV_CONTACT_T + 2×tan30°×H_c` | Contact patch 350×350 mm |
| Dispersed Width, L_L direction | `disp_LL` | m | `2×disp_LL_single` if wheel spacing (2.65 m) ≥ `disp_LL_single`, else `SV_WHEEL_SPACING + disp_LL_single` | Whether the two wheels of an axle merge |
| Dispersed Width per Axle, B_ext direction | `disp_B` | m | `SV_CONTACT_L + 2×tan30°×H_c` | |
| Worst-Case Offset | `worst_offset` | m | found by scanning front-axle position across `B_ext` in 0.01 m steps, for each candidate gap | Front axle position relative to culvert's leading edge |
| Maximum Vertical Load | `max_V_per_m` | kN/m | `sum(axle_load × overlap/disp_B / disp_LL)` over all contributing axles at `worst_offset`, best of the 3 gap candidates | |

**Vehicle definitions (NA Figure NA.1, all confirmed against the source PDF):**
- SV80: 6 axles @ 130 kN basic (150.8 kN DAF-factored, DAF=1.16). Two groups of 3, 1.2m spacing within group.
- SV100: 6 axles @ 165 kN basic (184.8 kN DAF-factored, DAF=1.12). Same structure as SV80.
- SV196: 12 axles — 9×165kN (DAF 1.12→184.8), 2×180kN (DAF 1.10→198), 1×100kN (DAF 1.20→120). Grouped
  5+4+3 as described above.
- All three: contact patch 350×350mm; outside track/overall width 3.0m; wheel spacing (transverse) =
  3.0 − 0.35 = 2.65m.

## Braking and Acceleration Forces — LM3 (calculated)

PD6694-1 Cl. 10.2.8.2; braking formula and δ from **NA.2.18.1** (not "BS EN 1991-2 Cl. 4.4.4" as
previously logged — that clause doesn't exist; the base EN only has 4.4.1/4.4.2, and NA.2.18.1 is the UK
NA's addition under 4.4.1(3)). Uses `basic_axle_loads` (unfactored, pre-DAF), not the DAF-factored
`axle_loads` used for the vertical load check above — confirmed by the clause text ("w is the basic axle
load"). The distribution length is `L_L` (Overall Length input) — PD6694-1 Cl. 10.2.8.2's "distributed...
over a length of Lj", confirmed against the worked example where `Lj = L_L = 20.6 m` for that scenario (a
different structure length than our current default of 10 m).

**δ (deceleration factor) is vehicle-specific, not a flat constant — this was wrong before:**
`SV_BRAKING_COEFF = {"SV80": 0.5, "SV100": 0.40, "SV196": 0.25}` (NA.2.18.1 exact text). The previous flat
0.25 for all vehicles was only ever correct for SV196; it understated SV80 by half and SV100 by 37.5%.

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| Per-Axle-Group Braking | `Q_lk,s` | kN | `delta[vehicle] × basic_axle_load` | Grouped by consecutive axles sharing the same basic load (e.g. "axles 2 & 3") |
| Total Braking Force | `total_braking` | kN | `sum(count × delta × basic_axle_load)` over all axle groups | |
| Design Braking Force | `Q_brk_per_m` | kN/m | `total_braking / L_L` | Distributed over the barrel length via in-plane rigidity |
| Fill Vertical Load | `fill_vertical` | kN | `UDL_total × B_ext` | Reuses `UDL_total` from Global Calculations (Self-weights) |
| Maximum Friction | `max_friction` | kN | `(max_V_per_m + fill_vertical) × tan30°` | `max_V_per_m` = this module's own computed worst-case vertical load (not the worked example's 151.4 kN) |
| Governing Check | — | — | `Q_brk_per_m < max_friction` | If exceeded, PD6694-1 says load effects in the members need to be considered (not yet implemented) |

**Not yet implemented from the NA**: NA.2.17's 900kN upper limit on braking force (unclear if this caps
the *sum* of SV axle braking forces the way it caps LM1's `Q_lk`); NA.2.18.2's centrifugal force formula
for SV/SOV vehicles; NA.2.20's transverse/skew braking force (50% of longitudinal, or 280kN for loaded
lengths ≥120m) — currently only longitudinal braking is checked.

## Table B.5 — Sliding Check, Minimum Vertical Load (calculated, `table_b5.py`, new "Table B.5" tab)

PD6694-1 Annex B, Table B.5 / Figure B.5 — confirmed against the source PDF that Table B.5's K values are
**identical** to Table B.4's (same 4 rows), so `table_b5.py` imports `table_b4.TABLE_B4` directly rather
than duplicating the data.

**Refactored `table_b4.py` to support this** rather than duplicating ~250 lines: `common_terms()` and
`model_check()` (previously `_common_terms`/`_model_check`, un-prefixed since they're now shared across
modules) take a `favourable` parameter. `sliding_check()` (previously `_sliding_check`) threads it through.
Table B.4's own calls default to `favourable=False`, so its behaviour is unchanged by the refactor —
re-verified line-by-line against the same worked example after the refactor, identical results.

**What actually changes between B.4 and B.5** (confirmed with the user rather than assumed, since the
figures don't spell out the traffic-vertical treatment explicitly):
- Self-weight & superimposed load use `partial_factors.FAVOURABLE` (`gamma_G;inf`) instead of
  `UNFAVOURABLE` (`gamma_G;sup`).
- Road construction deviation uses `ROAD_CONSTRUCTION_DEVIATION["favourable"]` (0.60, i.e. −40%) instead
  of `["unfavourable"]` (1.55, i.e. +55%).
- **No `GAMMA_SD_EC`** (1.15) at all — Figure B.5 omits it; that model factor is specific to the
  unfavourable/maximum permanent-load case (PD6694-1 Cl. 10.2.2, Figure B.4).
- Traffic-related terms (line load, LM1/LM3 UDL surcharge, braking, LM1/LM3 vertical) are **unchanged**
  — same `gamma_Q;sup` treatment as B.4, since these are live actions, not permanent loads. Confirmed with
  the user: the vehicle causing the braking force still has its full characteristic vertical load included
  (not reduced/excluded), even though the overall check wants "minimum" vertical load — only the permanent
  (self-weight/superimposed) contributions reduce.

Verified in the running app: at SLS, road/fill surcharge and vertical both drop relative to B.4 (e.g.
road construction vertical 26.52kN → 8.93kN), γSd;ec correctly absent from the displayed formula text, and
gamma_super/gamma_self correctly show as 0.95 at EQU/Comb1 (matching `partial_factors.FAVOURABLE`).

## Table B.4 — Sliding Check (calculated, `table_b4.py`, new "Table B.4" tab)

PD6694-1 Annex B, Table B.4 / Figure B.4 — sliding resistance across all four limit states (SLS, EQU,
STR/GEO Comb1, STR/GEO Comb2). Overturning and bearing (mentioned in the intro text) are not yet built.
Validated line-by-line against the D. Childs worked example for SLS/EQU/Comb1 (exact match on every term
except the LM3 vertical load, which intentionally uses this app's own scanned value — see LM3 section
above); Comb2 was built from the established pattern and confirmed against the two lines the user
originally held back (29.23kN, 50.10kN) — exact match.

**Key modelling decisions:**
- `TABLE_B4` dict holds `Ka_traffic` ("Horizontal traffic surcharge Ka" column — resolves the `Kd`
  placeholder from the Horizontal Surcharge Model), `Ka_earth` ("Earth pressure Ka" column — used for
  surcharge/backfill lateral pressure), and `Kmax`, per combo.
- **Road construction vs fill split**: `layer_udls[0]` (Layer 1) = road construction (subject to the
  ±55%/−40% deviation factor); `sum(layer_udls[1:])` = fill (not subject to deviation). Same assumption
  flagged in the Global Calculations section — confirm if Layer 1 won't always represent road construction.
- **γSd;ec = 1.15** (`GAMMA_SD_EC`, PD6694-1 Cl. 10.2.2) is a fixed model factor applied to road/fill
  vertical loads in *every* combo, in addition to the combo-specific `gamma_super` — distinct from the
  Partial Factors table.
- **δ (structure-ground interface friction angle) = `phi_founding`** (existing input) — δ_d = tan⁻¹(tanδ/γM)
  per combo, using γM from `partial_factors`.
- **LM1 and LM3 are both checked fully at every combo** (not just SLS) — `_common_terms()` computes the
  model-independent pieces (surcharge, backfill, road/fill/self-weight vertical) once; `_model_check()`
  computes each model's active/vertical/friction breakdown and margin (`max_Rd − friction_required`); the
  smaller margin governs. This replaced an earlier "assume LM3 governs, only check LM1 at SLS for
  comparison" shortcut copied from the worked example (which only demonstrated the SV196 case).
- Explored numerically whether LM1 can ever govern sliding: comparing *only* horizontal driving force,
  LM1 overtakes lighter SV vehicles (SV80/SV100) at fairly ordinary geometries (short `L_L`, moderate
  `B_ext`). But LM1's Tandem System also brings a large, `B_ext`-independent vertical contribution that
  adds friction resistance alongside the extra horizontal demand — once the *full* margin is computed,
  LM3 kept governing in every tested case, including deliberately extreme geometries (`B_ext≈20m`,
  `L_L=3m`, SV80), though the margins converged as geometry got more extreme. No confirmed case yet where
  LM1 governs *sliding* — but this hasn't been checked for overturning or bearing, where the horizontal/
  vertical interplay (moment arms vs. force sums) differs and the balance could tip differently.
- `lm1_results["Q_lk"] / L_L` gives LM1's braking force per metre (not yet stored in `lm1_calculations.py`
  itself — computed fresh here).

| Quantity | Symbol | Units | Definition | Notes |
|---|---|---|---|---|
| Road Construction Surcharge | `surcharge_road` | kN/m | `1.55 × layer_udls[0]` | Characteristic, not yet combo-factored |
| Fill Surcharge | `fill_udl_char` | kN/m | `sum(layer_udls[1:])` | |
| Active/Passive Force, Surcharge | `active_surcharge` / `passive_surcharge` | kN | `Ka_earth (or Kmax) × gamma_super × (surcharge_road + fill_udl_char) × H_ext` | |
| Active/Passive Force, Backfill | `active_backfill` / `passive_backfill` | kN | `Ka_earth (or Kmax) × gamma_self × (gamma_backfill × H_ext) × H_ext / 2` | |
| Active Force, Traffic Line Load | `active_line_load` | kN | `Ka_traffic × gamma_Q_sup × F_hll_1m_coeff` | Resolves the `Kd` placeholder |
| Active Force, LM3 UDL | `active_lm3_udl` | kN | `Ka_traffic × gamma_Q_sup × 30 × H_ext` | |
| Braking Force, LM3 (factored) | `braking_lm3` | kN | `gamma_Q_sup × lm3_results["Q_brk_per_m"]` | SLS: `gamma_Q_sup=1.0`, shown unfactored |
| Total Active / Passive | `total_active` / `total_passive` | kN | sum of the above (active includes braking; LM1 terms excluded except at SLS) | |
| Vertical Load Components | `road_vertical`, `fill_vertical`, `self_weight_vertical`, `lm3_vertical` | kN | each = `gamma × GAMMA_SD_EC × characteristic value × B_ext` (or `× W_box` for self-weight) | |
| Design Vertical Load | `V_d` | kN | sum of the four vertical components | |
| Design Friction Angle | `delta_d_deg` | ° | `atan(tan(phi_founding) / gamma_M)` in degrees | |
| Maximum Sliding Resistance | `max_Rd` | kN | `V_d × tan(delta_d)` | |
| Friction Required | `friction_required` | kN | `total_active − total_passive` | OK if `< max_Rd` |
