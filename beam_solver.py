"""First-principles beam analysis: reactions, shear force and bending moment for a beam on any
number of simple (pin/roller) supports, under any combination of point loads and UDLs.

Method: each span is first solved as an independent simply-supported beam under its own loads
(pure statics — unambiguous). For more than two supports, the beam is statically indeterminate,
so the redundant support moments are found with the classical three-moment theorem (Clapeyron's
equation), using numerical integration of each span's simple-beam moment diagram to get the area
and centroid terms the theorem needs — this generalises the theorem to *any* loading (not just
the textbook point-load/UDL cases it's traditionally tabulated for) without changing the method
itself. Sagging positive throughout (matches the reference beam formula tables).

No overhangs beyond the first/last support in this version — the beam spans exactly between them.
"""

import numpy as np

N_SUB = 24  # subdivisions per gap between critical points, for smooth diagrams + UDL accuracy


def _simple_span(L, point_loads, udls, x_eval):
    """Simply-supported span of length L (0..L), point_loads=[(x,P)], udls=[(s,e,w)] local to
    this span. Returns R_left, R_right, V(x_eval), M(x_eval) — sagging positive, P/w downward +."""
    total_P = sum(p for _, p in point_loads)
    total_w = sum(w * (e - s) for s, e, w in udls)

    M_about_left = sum(p * xp for xp, p in point_loads)
    M_about_left += sum(w * (e - s) * (s + e) / 2.0 for s, e, w in udls)

    R_right = M_about_left / L if L > 0 else 0.0
    R_left = total_P + total_w - R_right

    V = np.full_like(x_eval, R_left, dtype=float)
    M = R_left * x_eval

    for xp, p in point_loads:
        mask = x_eval > xp + 1e-12
        V[mask] -= p
        M[mask] -= p * (x_eval[mask] - xp)

    for s, e, w in udls:
        mid_mask = (x_eval > s + 1e-12) & (x_eval < e - 1e-12)
        past_mask = x_eval >= e - 1e-12
        V[mid_mask] -= w * (x_eval[mid_mask] - s)
        M[mid_mask] -= w * (x_eval[mid_mask] - s) ** 2 / 2.0
        V[past_mask] -= w * (e - s)
        M[past_mask] -= w * (e - s) * (x_eval[past_mask] - (s + e) / 2.0)

    return R_left, R_right, V, M


def _span_loads(point_loads, udls, x0, x1):
    """Filter global-coordinate loads down to those touching span [x0,x1] and shift to local
    (0..L) coordinates. A UDL that only partly overlaps the span is clipped to the overlap."""
    local_pl = [(x - x0, p) for x, p in point_loads if x0 - 1e-9 <= x <= x1 + 1e-9]
    local_udl = []
    for s, e, w in udls:
        lo, hi = max(s, x0), min(e, x1)
        if hi - lo > 1e-9:
            local_udl.append((lo - x0, hi - x0, w))
    return local_pl, local_udl


def solve_beam(support_positions, point_loads, udls, n_sub=N_SUB):
    """
    support_positions: sorted list/array of >=2 support x-positions (m).
    point_loads: list of (x, P) with P positive = downward (kN).
    udls: list of (x_start, x_end, w) with w positive = downward (kN/m).
    Returns dict: x, V, M (arrays over the whole beam), reactions (list aligned with
    support_positions), V_max, M_max, M_min, x_of_Mmax, x_of_Mmin, support_moments.
    """
    supports = list(support_positions)
    n_spans = len(supports) - 1
    L = [supports[i + 1] - supports[i] for i in range(n_spans)]

    # Simple-span solution for every span, in isolation, under its own loads only.
    simple = []
    for i in range(n_spans):
        pl, udl = _span_loads(point_loads, udls, supports[i], supports[i + 1])
        xs = np.linspace(0.0, L[i], 400)
        Rl, Rr, V0, M0 = _simple_span(L[i], pl, udl, xs)
        area = np.trapezoid(M0, xs)
        centroid_from_left = np.trapezoid(M0 * xs, xs) / area if abs(area) > 1e-12 else L[i] / 2.0
        simple.append({
            "pl": pl, "udl": udl, "Rl": Rl, "Rr": Rr,
            "area": area, "a_from_left": centroid_from_left,
        })

    # Three-moment theorem (Clapeyron): for each interior support k, relating the (unknown)
    # moments at supports k-1, k, k+1 of the two spans meeting there —
    #   MS[k-1]*L_k + 2*MS[k]*(L_k+L_{k+1}) + MS[k+1]*L_{k+1}
    #       = -6*Area_k*a_k/L_k - 6*Area_{k+1}*b_{k+1}/L_{k+1}
    # where a_k = centroid of span k's simple-beam moment diagram from its LEFT end, and
    # b_{k+1} = centroid of span k+1's diagram from its RIGHT end. MS[0] = MS[n_spans] = 0
    # (no overhangs, so the outer end supports carry no moment).
    MS = np.zeros(n_spans + 1)
    n_interior = n_spans - 1
    if n_interior > 0:
        A = np.zeros((n_interior, n_interior))
        b = np.zeros(n_interior)
        for row, k in enumerate(range(1, n_spans)):  # k = interior support index (1..n_spans-1)
            L1, L2 = L[k - 1], L[k]
            s1, s2 = simple[k - 1], simple[k]
            b2_from_right = L2 - s2["a_from_left"]
            b[row] = -6.0 * s1["area"] * s1["a_from_left"] / L1 - 6.0 * s2["area"] * b2_from_right / L2
            if row - 1 >= 0:
                A[row, row - 1] = L1
            A[row, row] = 2.0 * (L1 + L2)
            if row + 1 < n_interior:
                A[row, row + 1] = L2
        MS[1:n_spans] = np.linalg.solve(A, b)

    # Reconstruct V(x), M(x) across every span by superposing each span's simple-beam solution
    # with the linear moment term fixed by the (now known) support moments.
    x_all, V_all, M_all = [], [], []
    span_V_right0 = []  # V just right of each span's left support
    span_V_leftL = []   # V just left of each span's right support
    for i in range(n_spans):
        xs = np.linspace(0.0, L[i], n_sub * 4 + 1)
        s = simple[i]
        _, _, V0, M0 = _simple_span(L[i], s["pl"], s["udl"], xs)
        M = M0 + MS[i] * (1.0 - xs / L[i]) + MS[i + 1] * (xs / L[i])
        V = V0 + (MS[i + 1] - MS[i]) / L[i]

        span_V_right0.append(V[0])
        span_V_leftL.append(V[-1])

        if i > 0:
            xs, V, M = xs[1:], V[1:], M[1:]  # don't duplicate the shared support point
        x_all.append(supports[i] + xs)
        V_all.append(V)
        M_all.append(M)

    x = np.concatenate(x_all)
    V = np.concatenate(V_all)
    M = np.concatenate(M_all)

    # Reactions from the shear jump at each support: R_0 = V just right of the first support;
    # R_last = -(V just left of the last support); interior R_k = jump across support k.
    reactions = [span_V_right0[0]]
    for k in range(1, n_spans):
        reactions.append(span_V_right0[k] - span_V_leftL[k - 1])
    reactions.append(-span_V_leftL[-1])

    i_max, i_min = int(np.argmax(M)), int(np.argmin(M))
    return {
        "x": x, "V": V, "M": M,
        "supports": supports,
        "reactions": reactions,
        "support_moments": MS,
        "V_max": float(np.max(np.abs(V))),
        "M_max": float(M[i_max]),
        "x_of_Mmax": float(x[i_max]),
        "M_min": float(M[i_min]),
        "x_of_Mmin": float(x[i_min]),
    }
