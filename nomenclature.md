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
