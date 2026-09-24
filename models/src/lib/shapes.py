"""Shared factories for axisymmetric engine models. Axis = +X, profiles are (x, r) in mm."""
from math import cos, radians, sin, sqrt

from cadgen import build123d as bd


def revolved(points, spline=False):
    """Revolve a closed (x, r) profile about the X axis. A spline profile must start on the axis."""
    with bd.BuildPart() as part:
        with bd.BuildSketch(bd.Plane.XY):
            with bd.BuildLine():
                if spline:
                    bd.Spline(*points)
                    bd.Polyline(points[-1], (points[-1][0], 0), points[0])
                else:
                    bd.Polyline(*points, close=True)
            bd.make_face()
        bd.revolve(axis=bd.Axis.X)
    return part.part


def interp(table, x):
    """Piecewise-linear lookup in a sorted [(x, value), ...] table, clamped at the ends."""
    if x <= table[0][0]:
        return table[0][1]
    for (x0, v0), (x1, v1) in zip(table, table[1:]):
        if x <= x1:
            return v0 + (v1 - v0) * (x - x0) / (x1 - x0)
    return table[-1][1]


def tip_radius(r_limit, chord, thick, stagger):
    """Largest radius a flat-ended blade can reach so its corners stay inside r_limit."""
    a = radians(stagger)
    z_ext = chord / 2 * abs(sin(a)) + thick / 2 * abs(cos(a))
    return sqrt(r_limit ** 2 - z_ext ** 2)


def blade_ring(x, r0, r1, chord, thick, n, stagger):
    """n flat blades spanning radius r0..r1 at axial station x, staggered about their radial axis."""
    blade = bd.Pos(x, (r0 + r1) / 2, 0) * bd.Rot(0, stagger, 0) * bd.Box(chord, r1 - r0, thick)
    return [bd.Rot(360 / n * i, 0, 0) * blade for i in range(n)]


def tube(x0, x1, r_in, r_out):
    """Hollow cylinder along X from x0 to x1."""
    return revolved([(x0, r_in), (x1, r_in), (x1, r_out), (x0, r_out)])


def labelled(shape, label, color):
    from cadgen import srgb
    shape.label = label
    shape.color = srgb(color)
    return shape


def x_half(chord, thick, stagger):
    """Axial half-extent of a staggered flat blade."""
    a = radians(stagger)
    return chord / 2 * abs(cos(a)) + thick / 2 * abs(sin(a))


def stage(kind, x, chord, thick, n, stagger, *, bore, outer, hub, gap):
    """One blade row in a gas path given as (x, r) tables `outer` (casing) and `hub`.

    Rotor ("R"): disk from `bore` to the hub + blades reaching to `gap` below the casing.
    Stator ("S"): vanes from `gap` above the hub, flush with the casing (corner-safe).
    """
    dx = x_half(chord, thick, stagger)
    r_out = min(interp(outer, x - dx), interp(outer, x + dx))
    if kind == "R":
        r_hub = interp(hub, x)
        tip = tip_radius(r_out - gap, chord, thick, stagger)
        return [tube(x - dx - 2, x + dx + 2, bore, r_hub), *blade_ring(x, r_hub - 5, tip, chord, thick, n, stagger)]
    root = max(interp(hub, x - dx), interp(hub, x + dx)) + gap
    return blade_ring(x, root, tip_radius(r_out, chord, thick, stagger), chord, thick, n, stagger)
