import math

import streamlit as st

# UK NA to BS EN 1991-2 Table NA.5 SV vehicle definitions. Axle loads are DAF-factored.
# SV196 confirmed against the D. Childs worked example (basic axle loads 100/180x2/165x9 kN,
# DAF 1.20/1.10/1.12 respectively). SV80/SV100 carried over from the old v1 build — not yet
# re-verified against a worked example, treat with caution.
SV_VEHICLES = {
    "SV80": {
        "axle_loads": [100.0] * 8,
        "basic_axle_loads": [100.0] * 8,   # no DAF applied — not yet verified against a worked example
        "axle_pos": [0.0, 1.5, 6.5, 8.0, 13.0, 14.5, 19.5, 21.0],
    },
    "SV100": {
        "axle_loads": [100.0] * 10,
        "basic_axle_loads": [100.0] * 10,  # no DAF applied — not yet verified against a worked example
        "axle_pos": [0.0, 1.5, 6.5, 8.0, 13.0, 14.5, 19.5, 21.0, 26.0, 27.5],
    },
    "SV196": {
        "axle_loads": [120.0, 198.0, 198.0] + [184.8] * 9,
        "basic_axle_loads": [100.0, 180.0, 180.0] + [165.0] * 9,   # unfactored, for braking (Q_lk,s = delta x W)
        "axle_pos": [0.0, 3.5, 5.0, 8.0, 9.2, 10.4, 11.6, 12.8, 14.0, 15.2, 16.4, 17.6],
    },
}

SV_CONTACT_L = 0.35        # m, wheel contact patch in B_ext (travel) direction
SV_CONTACT_T = 0.35        # m, wheel contact patch in L_L (transverse) direction
SV_WHEEL_SPACING = 2.65    # m, wheel centre-to-centre in L_L direction
SV_BRAKING_COEFF = 0.25    # delta, BS EN 1991-2 Cl. 4.4.4: braking force per axle = delta x basic axle load
TAN_30 = math.tan(math.radians(30))


def _group_axles(basic_loads):
    """Group consecutive axles sharing the same basic load, for display (e.g. 'axles 2 & 3')."""
    groups = []
    start = 0
    for i in range(1, len(basic_loads) + 1):
        if i == len(basic_loads) or basic_loads[i] != basic_loads[start]:
            groups.append((start + 1, i, basic_loads[start]))   # 1-indexed axle numbers
            start = i
    return groups


def _dispersion(H_c):
    """Dispersed wheel/axle footprint at crown level, 30° through the fill."""
    spread = TAN_30 * H_c
    disp_LL_single = SV_CONTACT_T + 2 * spread
    gap_LL = SV_WHEEL_SPACING - disp_LL_single
    if gap_LL >= 0:
        disp_LL = 2 * disp_LL_single   # zones stay separate; worst 1 m strip sits under one wheel
        merged = False
    else:
        disp_LL = SV_WHEEL_SPACING + disp_LL_single   # zones merge
        merged = True
    disp_B = SV_CONTACT_L + 2 * spread
    return disp_LL, disp_B, disp_LL_single, merged


def _load_at_offset(axle_pos, axle_loads, offset, B_ext, disp_LL, disp_B):
    """Total load per metre strip landing on [0, B_ext] with the vehicle's front axle at `offset`."""
    half_B = disp_B / 2.0
    total = 0.0
    contributions = []
    for ax_pos, ax_load in zip(axle_pos, axle_loads):
        centre = offset + ax_pos
        ax_left = centre - half_B
        ax_right = centre + half_B
        overlap = max(0.0, min(ax_right, B_ext) - max(ax_left, 0.0))
        frac = overlap / disp_B if disp_B > 0 else 0.0
        contrib = ax_load * frac / disp_LL
        total += contrib
        if frac > 0:
            contributions.append((ax_pos, ax_load, overlap, frac, contrib))
    return total, contributions


def _worst_position(axle_pos, axle_loads, B_ext, disp_LL, disp_B, step=0.01):
    """Scan the vehicle across B_ext and return the offset that maximises the landed load."""
    half_B = disp_B / 2.0
    total_length = axle_pos[-1] if axle_pos else 0.0
    offset = -(total_length + half_B)
    end = B_ext + half_B

    max_load = 0.0
    worst_offset = offset

    while offset <= end + 1e-9:
        load_here, _ = _load_at_offset(axle_pos, axle_loads, offset, B_ext, disp_LL, disp_B)
        if load_here > max_load:
            max_load = load_here
            worst_offset = offset
        offset += step

    return max_load, worst_offset


def render(inputs, box_culvert_results):
    """Render LM3 (Special Vehicle) vertical load calculations and return computed values."""
    results = {}

    st.subheader("Maximum Vertical Load on Top of Culvert — LM3")

    vehicle_name = inputs["sv_vehicle"]
    vehicle = SV_VEHICLES[vehicle_name]
    H_c = box_culvert_results["H_c"]
    B_ext = box_culvert_results["B_ext"]

    st.write(f"Special Vehicle: **{vehicle_name}**")

    disp_LL, disp_B, disp_LL_single, merged = _dispersion(H_c)
    st.markdown("**Wheel Dispersal Through Fill**")
    st.write(
        f"Contact patch = {SV_CONTACT_L * 1000:.0f} × {SV_CONTACT_T * 1000:.0f} mm; "
        f"wheel spacing = {SV_WHEEL_SPACING:.2f} m"
    )
    st.write(
        f"Dispersed width per wheel (L_L direction) = {SV_CONTACT_T:.3f} + 2×tan30°×H_c "
        f"= {SV_CONTACT_T:.3f} + 2×{TAN_30:.4f}×{H_c:.3f} = **{disp_LL_single:.3f} m**"
    )
    if merged:
        st.write(
            f"Wheel spacing ({SV_WHEEL_SPACING:.2f} m) < dispersed width ⟹ the two wheels' zones merge: "
            f"disp_LL = {SV_WHEEL_SPACING:.2f} + {disp_LL_single:.3f} = **{disp_LL:.3f} m**"
        )
    else:
        st.write(
            f"Wheel spacing ({SV_WHEEL_SPACING:.2f} m) ≥ dispersed width ⟹ zones stay separate, so the "
            f"worst 1 m strip sits under one wheel: disp_LL = 2 × {disp_LL_single:.3f} = **{disp_LL:.3f} m**"
        )
    st.write(
        f"Dispersed width per axle (B_ext / travel direction) = {SV_CONTACT_L:.3f} + 2×tan30°×H_c "
        f"= **{disp_B:.3f} m**"
    )

    st.markdown("**Worst-Case Position**")
    st.write(
        f"Scanning the vehicle's position across B_ext = {B_ext:.2f} m to find the offset that "
        f"maximises the total load landing on the culvert."
    )
    max_load, worst_offset = _worst_position(
        vehicle["axle_pos"], vehicle["axle_loads"], B_ext, disp_LL, disp_B
    )
    _, contributions = _load_at_offset(
        vehicle["axle_pos"], vehicle["axle_loads"], worst_offset, B_ext, disp_LL, disp_B
    )

    st.write(f"Worst-case front-axle offset = {worst_offset:.3f} m from the culvert's leading edge.")
    st.write(f"{len(contributions)} axle(s) contribute at this position:")
    for ax_pos, ax_load, overlap, frac, contrib in contributions:
        st.write(
            f"- Axle at {ax_pos:.1f} m: load = {ax_load:.1f} kN, overlap = {overlap:.3f} m "
            f"({frac * 100:.0f}% of dispersed width) ⟹ {ax_load:.1f} × {frac:.3f} / {disp_LL:.3f} "
            f"= **{contrib:.2f} kN/m**"
        )

    st.write(f"**Maximum vertical load on a 1 m strip = {max_load:.1f} kN/m**")

    results["max_V_per_m"] = max_load
    results["worst_offset"] = worst_offset
    results["disp_LL"] = disp_LL
    results["disp_B"] = disp_B

    st.divider()
    st.subheader("Braking and Acceleration Forces")

    L_L = inputs["L_L"]
    UDL_total = box_culvert_results["UDL_total"]

    st.write(f"For LM3: Q_lk,s = δ·ω, where δ = {SV_BRAKING_COEFF:.2f} and ω = basic (unfactored) axle load.")

    basic_loads = vehicle["basic_axle_loads"]
    groups = _group_axles(basic_loads)
    terms = []
    total_braking = 0.0
    for start, end, val in groups:
        count = end - start + 1
        Q_lks = SV_BRAKING_COEFF * val
        total_braking += count * Q_lks
        label = f"axle {start}" if count == 1 else (f"axles {start} & {end}" if count == 2 else f"axles {start} to {end}")
        st.write(f"Q_lk,s ({label}) = {SV_BRAKING_COEFF:.2f} × {val:.0f}kN = **{Q_lks:.2f}kN**")
        terms.append(f"{Q_lks:.2f}" if count == 1 else f"{count} × {Q_lks:.2f}")

    st.caption(
        'PD6694-1:2011 Cl. 10.2.8.2: "The total braking or acceleration force applied to the top of the '
        'roof of a buried structure need not be taken as greater than the friction force that can be '
        'generated between the earth and the roof."'
    )

    st.write(
        f"Vertical load from fill above culvert = UDL_total × B_ext = {UDL_total:.1f} × {B_ext:.2f} "
        f"= **{(UDL_total * B_ext):.1f}kN**"
    )
    fill_vertical = UDL_total * B_ext

    st.write(
        f"Assuming a coefficient of friction of tan30°, maximum friction generated on a metre width "
        f"between the earth and the roof = ({max_load:.1f} + {fill_vertical:.1f}) × tan30° "
        f"= **{((max_load + fill_vertical) * TAN_30):.1f}kN**"
    )
    max_friction = (max_load + fill_vertical) * TAN_30

    st.write(
        f"Total braking force generated by {vehicle_name} = {' + '.join(terms)} = **{total_braking:.1f}kN**"
    )

    Q_brk_per_m = total_braking / L_L
    st.write(
        f"Using the in-plane rigidity of the roof and walls, the braking/acceleration force is "
        f"distributed over the barrel length L_L: {total_braking:.1f} / {L_L:.2f} = **{Q_brk_per_m:.1f} kN/m**"
    )

    if Q_brk_per_m < max_friction:
        st.write(
            f"**{Q_brk_per_m:.1f} kN/m < {max_friction:.1f} kN ∴ use braking/acceleration force = "
            f"{Q_brk_per_m:.1f} kN/m.**"
        )
    else:
        st.write(
            f"**{Q_brk_per_m:.1f} kN/m ≥ {max_friction:.1f} kN ∴ the braking force exceeds available "
            f"friction — load effects in the members need to be considered.**"
        )

    results["total_braking"] = total_braking
    results["Q_brk_per_m"] = Q_brk_per_m
    results["max_friction"] = max_friction

    return results
