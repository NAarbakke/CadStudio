"""Recipe helpers for missile cutaway models: thin shells, solid-rocket motors, simple solids.

Illustration level: parts sit where the sources put them with plausible proportions. Grains are
plain cylindrical-bore cartridges and payloads are placeholder volumes; nothing here is
performance or design data. All helpers return (x, r) profiles or recipe ops (see shapes.py).
"""
from math import cos, pi, sin, sqrt


def ogive(length, r_base, n=14):
    """Tangent-ogive (x, r) points from the tip (x=0) to the base (x=length)."""
    rho = (r_base ** 2 + length ** 2) / (2 * r_base)
    xs = [length * (i / n) ** 1.6 for i in range(n + 1)]  # denser near the tip
    return [(x, max(0.0, sqrt(rho ** 2 - (length - x) ** 2) + r_base - rho)) for x in xs]


def smooth(points, per_segment=5):
    """Monotone cubic (Fritsch-Carlson) through digitized (x, r) points: no overshoot, no facets."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(len(xs) - 1)]
    m = [0.0 if d[i - 1] * d[i] <= 0 else 2 / (1 / d[i - 1] + 1 / d[i]) for i in range(1, len(d))]
    m = [d[0]] + m + [d[-1]]
    out = []
    for i in range(len(d)):
        h = xs[i + 1] - xs[i]
        for k in range(per_segment):
            t = k / per_segment
            h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
            out.append((xs[i] + t * h, h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]))
    return out + [points[-1]]


def shell(outer, t):
    """Closed profile of a wall of thickness t under an outer (x, r) curve (tip on the axis allowed)."""
    inner = [(x, r - t) for x, r in outer if r - t > 0]
    pts = outer + list(reversed(inner))
    if outer[0][1] == 0:  # solid tip: close back to it along the axis
        pts.append((inner[0][0], 0.0))
    return pts


def tube(x0, x1, r_out, t):
    return [(x0, r_out - t), (x1, r_out - t), (x1, r_out), (x0, r_out)]


def dome(xe, r, a, y_min, forward, n=7):
    """Ellipsoidal dome points from radius y_min up to the equator r (forward: bulges to -X)."""
    s = -1 if forward else 1
    ys = [y_min + (r - y_min) * sin(pi / 2 * i / n) for i in range(n + 1)]
    return [(xe + s * a * sqrt(max(0.0, 1 - (y / r) ** 2)), y) for y in ys]


def _from_radius(pts, y0):
    """Polyline (ordered by rising r) cut to start exactly at r = y0."""
    for (x0, r0), (x1, r1) in zip(pts, pts[1:]):
        if r0 <= y0 <= r1:
            return [(x0 + (x1 - x0) * (y0 - r0) / (r1 - r0), y0)] + [pt for pt in pts if pt[1] > y0]
    raise ValueError(f"radius {y0} outside {pts[0][1]}..{pts[-1][1]}")


def sphere(xc, r, n=12):
    """Half-circle profile; the end points are exactly on the axis (sin(pi) is 1e-16, not 0)."""
    return [(xc - r * cos(pi * i / n), 0.0 if i in (0, n) else r * sin(pi * i / n)) for i in range(n + 1)]


def motor(name, *, xe0, xe1, r, t, a, port_fwd, port_aft, bore, throat, exit, skirts=None, t_nozzle=12):
    """Ops for one solid motor: case (+ skirts), grain, igniter, nozzle; returns {part: ops}.

    xe0/xe1 are the dome equator stations, a the dome depth, throat=(x, r), exit=(x, r).
    """
    fwd_o, aft_o = dome(xe0, r, a, port_fwd, True), dome(xe1, r, a, port_aft, False)
    fwd_i, aft_i = dome(xe0, r - t, a - t, port_fwd, True), dome(xe1, r - t, a - t, port_aft, False)
    case = fwd_o + list(reversed(aft_o)) + aft_i + list(reversed(fwd_i))
    ops = {"case": [("revolve", f"{name}Case", case)]}
    for i, (x0, x1) in enumerate(skirts or []):
        ops["case"].append(("revolve", f"{name}Skirt{i + 1}", tube(x0, x1, r, t)))
    # the grain follows the case's inner dome points exactly (same chords), cut off at the bore radius
    g_fwd, g_aft = _from_radius(fwd_i, bore), _from_radius(aft_i, bore)
    ops["grain"] = [("revolve", f"{name}Grain", g_fwd + list(reversed(g_aft)))]
    x_port_o, x_port_i = fwd_o[0][0], fwd_i[0][0]
    ops["igniter"] = [("revolve", f"{name}Igniter", [(x_port_o - 30, 0), (x_port_i + 220, 0),
                                                        (x_port_i + 220, port_fwd * 0.7), (x_port_i, port_fwd * 0.7),
                                                        (x_port_i, port_fwd), (x_port_o - 30, port_fwd)])]
    x_att = aft_i[0][0]
    (xt, rt), (xx, rx) = throat, exit
    ops["nozzle"] = [("revolve", f"{name}Nozzle", [
        (x_att, port_aft), (xt, rt + t_nozzle), (xx, rx + t_nozzle), (xx, rx), (xt, rt), (x_att, port_aft - t_nozzle)])]
    return ops
