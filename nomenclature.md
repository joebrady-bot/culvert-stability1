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
