"""Shared factories for axisymmetric engine models. Axis = +X, profiles are (x, r) in mm.

Parts are described as recipes: a list of ops applied in order (each op is added, "cut" removes).
build() turns a recipe into a cadgen solid; integrations/solidworks/solidworks_api.py PartBuilder.build() turns the
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
    ("fins", name, points, thick, n, angle=0)               n flat fins: (x, r) planform polygon, thickness thick, first fin at +Y
    ("pipe", name, points, dia)                             solid round pipe along a 3D polyline [(x, y, z)], spherical elbows
                                                            (cadgen and FreeCAD only; the SolidWorks builder raises)
    ("sweep", name, points, dia, radius)                    solid round duct along a 3D polyline whose corners are arcs of
                                                            `radius` (see sweep_path); cadgen and FreeCAD only
    ("lathe", name, points, radius, origin=(0, 0, 0), axis=(1, 0, 0), chamfer=False)
                                                            closed (a, r) polygon revolved about any axis through origin,
                                                            a along the axis; corners rounded to `radius` (see round_profile),
                                                            or cut straight across with chamfer=True
    ("hex_circle", name, origin, axis, r, flats, length, n, angle=0)
                                                            n hex prisms (nuts, bolt heads) on a circle of radius r about the
                                                            axis, each along the axis and centred on the plane through origin
    ("pin_circle", name, origin, axis, r, dia, length, n, angle=0)   the same with round pins (studs)
                                                            (these three: cadgen and FreeCAD only)

`name` becomes the SolidWorks feature name; `angle` rotates the whole ring about X (degrees).
"""
from math import acos, cos, pi, radians, sin, sqrt, tan

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


def fins(points, thick, n, angle=0):
    """n flat fins: (x, r) planform in the XY plane, extruded symmetrically to `thick` in Z."""
    with bd.BuildPart() as fin:
        with bd.BuildSketch(bd.Plane.XY):
            with bd.BuildLine():
                bd.Polyline(*points, close=True)
            bd.make_face()
        bd.extrude(amount=thick / 2, both=True)
    return _around(fin.part, n, angle)


def pipe(points, dia):
    """Cylinders between consecutive (x, y, z) points plus a sphere at each inner point (the elbows)."""
    segs = [(bd.Vector(a), bd.Vector(b)) for a, b in zip(points, points[1:])]
    return ([bd.Solid.make_cylinder(dia / 2, (b - a).length, bd.Plane(origin=a, z_dir=b - a)) for a, b in segs]
            + [bd.Pos(*p) * bd.Solid.make_sphere(dia / 2) for p in points[1:-1]])


def sweep_path(points, radius):
    """A 3D polyline with every corner turned into a tangent arc: [("line", p, q) | ("arc", p, mid, q, r)].

    Each arc has `radius`, shortened where a leg is short (tangent length at most 0.45 of it). The end
    points stay where they are. Corners turning less than 1 degree are passed straight through.
    """
    def unit(v):
        length = sqrt(sum(c * c for c in v))
        return [c / length for c in v], length
    segs, at = [], tuple(points[0])
    for p, v, q in zip(points, points[1:], points[2:]):
        (u, lu), (w, lw) = unit([a - b for a, b in zip(p, v)]), unit([a - b for a, b in zip(q, v)])
        turn = pi - acos(max(-1.0, min(1.0, sum(a * b for a, b in zip(u, w)))))
        if turn < radians(1):
            continue
        d = min(radius * tan(turn / 2), 0.45 * lu, 0.45 * lw)
        r = d / tan(turn / 2)
        bis, _ = unit([a + b for a, b in zip(u, w)])
        a, b = tuple(c + e * d for c, e in zip(v, u)), tuple(c + e * d for c, e in zip(v, w))
        mid = tuple(c + e * (r / cos(turn / 2) - r) for c, e in zip(v, bis))
        segs += [("line", at, a), ("arc", a, mid, b, r)]
        at = b
    return segs + [("line", at, tuple(points[-1]))]


def sweep(points, dia, radius):
    """A circle of `dia` swept along sweep_path(points, radius): a duct with real bends and flat ends."""
    segs = sweep_path(points, radius)
    if any(s[0] == "arc" and s[4] <= dia / 2 for s in segs):
        raise ValueError("a bend is tighter than the duct is wide; lengthen the legs or reduce the diameter")
    edges = [bd.Edge.make_line(s[1], s[2]) if s[0] == "line" else bd.Edge.make_three_point_arc(s[1], s[2], s[3])
             for s in segs]
    start = bd.Plane(origin=points[0], z_dir=tuple(bd.Vector(segs[0][2]) - bd.Vector(segs[0][1])))
    return bd.Solid.sweep(bd.Face(bd.Wire(bd.Edge.make_circle(dia / 2, start))), bd.Wire(edges))

def frame(axis):
    """(x, y, z) unit vectors for an op axis: z along it, x = Z cross axis (+Y for the engine axis +X)."""
    z = bd.Vector(axis).normalized()
    x = bd.Vector(0, 0, 1).cross(z)
    x = x.normalized() if x.length > 1e-9 else bd.Vector(1, 0, 0)
    return x, z.cross(x), z


def round_profile(points, radius, chamfer=False):
    """Closed polygon with its corners rounded: [("line", p, q) | ("arc", p, mid, q)] in profile coordinates.

    Each corner gets a tangent arc of `radius`, shortened where an adjacent side is short (tangent
    length at most 0.4 of it). Corners on the axis (r = 0) and bends under 12 degrees (points along
    a curve) stay as they are. chamfer=True joins the tangent points with a line instead: use it for a
    small radius on a large diameter, where a rounded edge meshes into a very large number of triangles.
    """
    n, cut = len(points), []
    for i, v in enumerate(points):
        p, q = points[i - 1], points[(i + 1) % n]
        u, w = (p[0] - v[0], p[1] - v[1]), (q[0] - v[0], q[1] - v[1])
        lu, lw = sqrt(u[0] ** 2 + u[1] ** 2), sqrt(w[0] ** 2 + w[1] ** 2)
        u, w = (u[0] / lu, u[1] / lu), (w[0] / lw, w[1] / lw)
        half = acos(max(-1.0, min(1.0, u[0] * w[0] + u[1] * w[1]))) / 2  # half the interior angle
        if radius <= 0 or abs(v[1]) < 1e-9 or half > radians(84):
            cut.append((v, None, v))
            continue
        d = min(radius / tan(half), 0.4 * lu, 0.4 * lw)
        r = d * tan(half)
        bis = (u[0] + w[0], u[1] + w[1])
        lb = sqrt(bis[0] ** 2 + bis[1] ** 2)
        k = r / sin(half) - r  # corner to the arc's midpoint, along the bisector
        cut.append(((v[0] + u[0] * d, v[1] + u[1] * d), (v[0] + bis[0] / lb * k, v[1] + bis[1] / lb * k),
                    (v[0] + w[0] * d, v[1] + w[1] * d)))
    segs = []
    for i, (a, mid, b) in enumerate(cut):
        if mid is not None:
            segs.append(("line", a, b) if chamfer else ("arc", a, mid, b))
        segs.append(("line", b, cut[(i + 1) % n][0]))
    return segs


def lathe(points, radius, origin=(0, 0, 0), axis=(1, 0, 0), chamfer=False):
    """Revolve a closed (a, r) profile with rounded (or chamfered) corners about the axis through origin."""
    x, _, z = frame(axis)

    def at(p):
        return bd.Vector(origin) + z * p[0] + x * p[1]
    edges = [bd.Edge.make_line(at(s[1]), at(s[2])) if s[0] == "line"
             else bd.Edge.make_three_point_arc(at(s[1]), at(s[2]), at(s[3])) for s in round_profile(points, radius, chamfer)]
    return bd.revolve(bd.Face(bd.Wire(edges)), bd.Axis(origin, tuple(z)))


def _circle(seed, origin, axis, r, n, angle):
    """n copies of a seed solid (built along local +Z about the local origin) on a circle about the op axis."""
    x, _, z = frame(axis)
    loc = bd.Plane(origin=origin, x_dir=tuple(x), z_dir=tuple(z)).location
    return [loc * bd.Rot(0, 0, angle + 360 / n * i) * bd.Pos(r, 0, 0) * seed for i in range(n)]


def hex_circle(origin, axis, r, flats, length, n, angle=0):
    """n hex prisms `flats` across, one corner pointing away from the axis."""
    seed = bd.Pos(0, 0, -length / 2) * bd.extrude(bd.RegularPolygon(flats / 2, 6, major_radius=False), amount=length)
    return _circle(seed, origin, axis, r, n, angle)


def pin_circle(origin, axis, r, dia, length, n, angle=0):
    return _circle(bd.Cylinder(dia / 2, length), origin, axis, r, n, angle)


def along(origin, axis, a):
    """The point `a` along an op axis from origin."""
    length = sqrt(sum(c * c for c in axis))
    return tuple(o + c / length * a for o, c in zip(origin, axis))


def flange_bolts(name, origin, axis, r, size, n, faces, angle=0):
    """Ops for a bolt circle on a flange: a nut and stud end standing on each given face.

    `faces` are (a, side) pairs: the face at `a` along the axis, fasteners on its -1 or +1 side.
    Nuts are 1.6 x size across flats and 0.8 x size high on a stud of diameter `size`. Nothing
    passes through the flange, so the fasteners touch it without intersecting it.
    """
    ops = []
    for i, (a, side) in enumerate(faces):
        ops += [("hex_circle", f"{name}Nuts{i + 1}", along(origin, axis, a + side * 0.4 * size), axis, r,
                 1.6 * size, 0.8 * size, n, angle),
                ("pin_circle", f"{name}Studs{i + 1}", along(origin, axis, a + side * 0.65 * size), axis, r,
                 size, 1.3 * size, n, angle)]
    return ops


def segment(outer, inner, x0, x1):
    """Closed (x, r) profile of a wall between two sorted tables, cut to x0..x1 (axial slice of a shell)."""
    def cut(table):
        return [(x0, interp(table, x0))] + [p for p in table if x0 < p[0] < x1] + [(x1, interp(table, x1))]
    return cut(outer) + list(reversed(cut(inner)))


def tube_profile(x0, x1, r_in, r_out):
    return [(x0, r_in), (x1, r_in), (x1, r_out), (x0, r_out)]


def tube(x0, x1, r_in, r_out):
    """Hollow cylinder along X from x0 to x1."""
    return revolved(tube_profile(x0, x1, r_in, r_out))


OPS = {"revolve": revolved, "offset_revolve": offset_revolve, "duct": duct, "fins": fins, "offset_ring": offset_ring, "spline": lambda pts: revolved(pts, spline=True), "torus": torus,
       "ring": blade_ring, "pins": pins, "axial_pins": axial_pins, "loft": loft_ring, "pipe": pipe, "sweep": sweep,
       "lathe": lathe, "hex_circle": hex_circle, "pin_circle": pin_circle}


def exact_volume(shape, eps=1e-6):
    """Volume by adaptive integration: build123d's `.volume` is ~10 % off on spline lofts (blade rows)."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, props, eps, False)
    return props.Mass()


def build(ops):
    """cadgen solid from a recipe (see module docstring)."""
    part = bd.Part()
    for kind, name, *args in ops:
        if kind == "cut":
            part = part - revolved(*args)
            continue
        base, part = part, part + OPS[kind](*args)
        # the kernel can return an inside-out or partial solid without an error; `.volume` is the cheap test,
        # confirmed by integration because it also drops when a spline loft is added to a sound solid
        if part.volume < 0.999 * base.volume and exact_volume(part) < 0.999 * exact_volume(base):
            raise ValueError(f"{name}: adding this {kind} lost material (boolean failure); move or reshape it")
    return part


def labelled(shape, label, color):
    from cadgen import srgb
    shape.label = label
    shape.color = srgb(color)
    return shape


def assemble(parts, label, groups=None):
    """Compound of labelled parts from [(label, color, ops), ...].

    `groups` {group label: [part labels]} nests those parts under a sub-assembly, placed where its
    first part stands in the list; parts in no group stay at the top level.
    """
    owner = {name: group for group, names in (groups or {}).items() for name in names}
    children, nested = [], {}
    for name, color, ops in parts:
        shape, group = labelled(build(ops), name, color), owner.get(name)
        if group is None:
            children.append(shape)
        elif group in nested:
            nested[group].append(shape)
        else:
            nested[group] = [shape]
            children.append(group)
    return bd.Compound(children=[bd.Compound(children=nested[c], label=c) if isinstance(c, str) else c
                                 for c in children], label=label)


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
