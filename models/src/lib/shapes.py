"""Shared factories for axisymmetric engine models. Axis = +X, profiles are (x, r) in mm.

Parts are described as recipes: a list of ops applied in order (each op is added, "cut" removes).
build() turns a recipe into a cadgen solid; integrations/sw_api.py PartBuilder.build() turns the
same recipe into native SolidWorks features, so both outputs come from one set of numbers.

    ("revolve", name, points)                               closed (x, r) polygon revolved about X
    ("offset_revolve", name, points, axis_y)                same, about a line parallel to X at height axis_y
    ("spline", name, points)                                spline through points (first on the axis), closed to the axis
    ("cut", name, points)                                   revolved polygon removed from everything before it
    ("torus", name, x, r, tube_r)
    ("ring", name, x, r0, r1, chord, thick, n, stagger, angle=0)   n flat blades from r0 to r1
    ("pins", name, x, r0, r1, dia, n, angle=0)              n radial round pins from r0 to r1
    ("axial_pins", name, x, r, dia, length, n, angle=0)     n cylinders along X, centred on x
    ("loft", name, x, sections, n)                          n blades lofted through elliptical sections [(r, chord, thick, twist°)]
    ("duct", name, stations, wall)                          hollow duct through circles [(x, y_centre, r_outer)], wall thickness
    ("offset_ring", name, points, axis_y, n)                n copies of an offset_revolve around X (e.g. a ring of cones)
    ("fins", name, points, thick, n)                        n flat fins: (x, r) planform polygon, thickness thick, first fin at +Y

`name` becomes the SolidWorks feature name; `angle` rotates the whole ring about X (degrees).
"""
from math import cos, pi, radians, sin, sqrt

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


def _around(shape, n, angle=0):
    return [bd.Rot(angle + 360 / n * i, 0, 0) * shape for i in range(n)]


def blade_ring(x, r0, r1, chord, thick, n, stagger, angle=0):
    """n flat blades spanning radius r0..r1 at axial station x, staggered about their radial axis."""
    return _around(bd.Pos(x, (r0 + r1) / 2, 0) * bd.Rot(0, stagger, 0) * bd.Box(chord, r1 - r0, thick), n, angle)


def pins(x, r0, r1, dia, n, angle=0):
    return _around(bd.Pos(x, (r0 + r1) / 2, 0) * bd.Cylinder(dia / 2, r1 - r0, rotation=(90, 0, 0)), n, angle)


def axial_pins(x, r, dia, length, n, angle=0):
    return _around(bd.Pos(x, r, 0) * bd.Cylinder(dia / 2, length, rotation=(0, 90, 0)), n, angle)


def torus(x, r, tube_r):
    return bd.Pos(x, 0, 0) * bd.Torus(r, tube_r, rotation=(0, 90, 0))


def blade_section(x, r, chord, thick, twist, k=16):
    """k points around an elliptical blade section on the plane y=r, chord turned `twist`° from +X toward +Z.

    Sections are closed splines through these points rather than true ellipses: point i of every
    section sits at the same angle, so a twisted loft joins matching points in any CAD kernel
    (lofts between ellipses have no defined start point and pinch or bulge when twisted).
    """
    a = radians(twist)
    return [(x + u * cos(a) + w * sin(a), r, u * sin(a) - w * cos(a))
            for u, w in ((chord / 2 * cos(t), thick / 2 * sin(t)) for t in (2 * pi * i / k for i in range(k)))]


def loft_ring(x, sections, n):
    """n blades lofted through blade_section() splines, one per (r, chord, thick, twist) station.

    Ruled (straight between stations): OpenCascade's smooth loft overshoots ~12 % next to the end
    sections; ruled through closely spaced stations matches SolidWorks' smooth loft to 0.01 % in volume.
    """
    wires = [bd.Wire(bd.Edge.make_spline(blade_section(x, *s), periodic=True)) for s in sections]
    return _around(bd.Solid.make_loft(wires, ruled=True), n)


def offset_revolve(points, axis_y):
    return bd.Pos(0, axis_y, 0) * revolved(points)


def offset_ring(points, axis_y, n):
    return _around(offset_revolve(points, axis_y), n)


def duct_stations(start, end, n=9):
    """n circle stations (x, y_centre, r) from start to end; the centreline is an S-bend (smoothstep)."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        s = t * t * (3 - 2 * t)
        out.append((start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * s,
                    start[2] + (end[2] - start[2]) * t))
    return out


def duct(stations, wall):
    """Hollow duct lofted through circles on planes normal to X (ruled: see loft_ring)."""
    def loft(dr):
        return bd.Solid.make_loft([bd.Wire(bd.Edge.make_circle(r - dr, bd.Plane(origin=(x, y, 0), z_dir=(1, 0, 0))))
                                   for x, y, r in stations], ruled=True)
    return loft(0) - loft(wall)


def fins(points, thick, n):
    """n flat fins: (x, r) planform in the XY plane, extruded symmetrically to `thick` in Z."""
    with bd.BuildPart() as fin:
        with bd.BuildSketch(bd.Plane.XY):
            with bd.BuildLine():
                bd.Polyline(*points, close=True)
            bd.make_face()
        bd.extrude(amount=thick / 2, both=True)
    return _around(fin.part, n)


def tube_profile(x0, x1, r_in, r_out):
    return [(x0, r_in), (x1, r_in), (x1, r_out), (x0, r_out)]


def tube(x0, x1, r_in, r_out):
    """Hollow cylinder along X from x0 to x1."""
    return revolved(tube_profile(x0, x1, r_in, r_out))


OPS = {"revolve": revolved, "offset_revolve": offset_revolve, "duct": duct, "fins": fins, "offset_ring": offset_ring, "spline": lambda pts: revolved(pts, spline=True), "torus": torus,
       "ring": blade_ring, "pins": pins, "axial_pins": axial_pins, "loft": loft_ring}


def build(ops):
    """cadgen solid from a recipe (see module docstring)."""
    part = bd.Part()
    for kind, _name, *args in ops:
        part = part - revolved(*args) if kind == "cut" else part + OPS[kind](*args)
    return part


def labelled(shape, label, color):
    from cadgen import srgb
    shape.label = label
    shape.color = srgb(color)
    return shape


def assemble(parts, label):
    """Compound of labelled parts from [(label, color, ops), ...]."""
    return bd.Compound(children=[labelled(build(ops), name, color) for name, color, ops in parts], label=label)


def x_half(chord, thick, stagger):
    """Axial half-extent of a staggered flat blade."""
    a = radians(stagger)
    return chord / 2 * abs(cos(a)) + thick / 2 * abs(sin(a))


def stage(name, kind, x, chord, thick, n, stagger, *, bore, outer, hub, gap):
    """Ops for one blade row in a gas path given as (x, r) tables `outer` (casing) and `hub`.

    Rotor ("R"): disk "<name>Disk" from `bore` to the hub + blades reaching to `gap` below the casing.
    Stator ("S"): vanes from `gap` above the hub, flush with the casing (corner-safe).
    """
    dx = x_half(chord, thick, stagger)
    r_out = min(interp(outer, x - dx), interp(outer, x + dx))
    if kind == "R":
        r_hub = interp(hub, x)
        tip = tip_radius(r_out - gap, chord, thick, stagger)
        return [("revolve", f"{name}Disk", tube_profile(x - dx - 2, x + dx + 2, bore, r_hub)),
                ("ring", name, x, r_hub - 5, tip, chord, thick, n, stagger)]
    root = max(interp(hub, x - dx), interp(hub, x + dx)) + gap
    return [("ring", name, x, root, tip_radius(r_out, chord, thick, stagger), chord, thick, n, stagger)]
