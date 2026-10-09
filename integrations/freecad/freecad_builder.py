"""Runs inside FreeCAD (freecadcmd): builds a model's recipes (JSON from freecad_build.py) as parametric
Part-workbench features and saves an .FCStd, plus one STEP per part for verification.

Environment: FC_JSON (recipe file), FC_OUT (.FCStd path), FC_STEPS (folder for per-part STEP).
Revolve / fin profiles are fully constrained sketches with dimensions named x<i>/r<i>; blade, pin
and cone rows are parametric primitives in a Draft polar array (NumberPolar = count).
"""
import json
import os

import Draft
import FreeCAD as App
import Part
import Sketcher

V = App.Vector
data = json.load(open(os.environ["FC_JSON"], encoding="utf-8"))
doc = App.newDocument(data["model"])


def add(kind, name):
    return doc.addObject(kind, name)


def sketch(name, placement=None):
    sk = add("Sketcher::SketchObject", name)
    if placement is not None:
        sk.Placement = placement
    return sk


def polygon(name, pts, dimension=True):
    """Closed polygon sketch on the XY plane; each vertex dimensioned from the origin (x<i>, r<i>)."""
    sk = sketch(name)
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        sk.addGeometry(Part.LineSegment(V(x0, y0, 0), V(x1, y1, 0)))
    for i in range(n):
        sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % n, 1))
    if not dimension:
        for i in range(n):
            sk.addConstraint(Sketcher.Constraint("Block", i))
        return sk
    for i, (x, y) in enumerate(pts):
        for axis, value, on_axis in (("x", x, -2), ("r", y, -1)):  # -2 = V_Axis, -1 = H_Axis
            if abs(value) < 1e-9:
                sk.addConstraint(Sketcher.Constraint("PointOnObject", i, 1, on_axis))
            else:
                c = sk.addConstraint(Sketcher.Constraint("DistanceX" if axis == "x" else "DistanceY", -1, 1, i, 1, value))
                sk.renameConstraint(c, f"{axis}{i}")
    return sk


def revolution(name, sk, axis_y=0.0):
    rev = add("Part::Revolution", name)
    rev.Source, rev.Axis, rev.Base, rev.Angle, rev.Solid = sk, V(1, 0, 0), V(0, axis_y, 0), 360, True
    return rev


def polar(obj, name, n, axis=V(1, 0, 0), center=V(0, 0, 0)):
    arr = Draft.make_polar_array(obj, number=n, angle=360, center=center, use_link=False)
    arr.Axis = axis
    arr.Label = name
    return arr


def about_x(angle):
    return App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), angle))


# ---- one function per recipe op ----

def op_revolve(name, pts, axis_y=0.0):
    return revolution(name, polygon(f"{name}Profile", [(x, r + axis_y) for x, r in pts]), axis_y)


def op_offset_revolve(name, pts, axis_y):
    return op_revolve(name, pts, axis_y)


def op_offset_ring(name, pts, axis_y, n):
    return polar(op_revolve(f"{name}Seed", pts, axis_y), name, n)


def op_spline(name, pts):
    sk = sketch(f"{name}Profile")
    bs = Part.BSplineCurve()
    bs.interpolate([V(x, r, 0) for x, r in pts])
    (x0, _), (xl, rl) = pts[0], pts[-1]
    sk.addGeometry(bs)
    sk.addGeometry(Part.LineSegment(V(xl, rl, 0), V(xl, 0, 0)))
    sk.addGeometry(Part.LineSegment(V(xl, 0, 0), V(x0, 0, 0)))
    for i in range(3):
        sk.addConstraint(Sketcher.Constraint("Block", i))
    return revolution(name, sk)


def op_torus(name, x, r, tube_r):
    t = add("Part::Torus", name)
    t.Radius1, t.Radius2 = r, tube_r
    # seam turned 45° off the XY plane: on a Part::Revolution seam, MultiFuse silently leaves the torus unfused
    t.Placement = App.Placement(V(x, 0, 0), App.Rotation(V(1, 0, 0), 45).multiply(App.Rotation(V(0, 1, 0), 90)))
    return t


def op_ring(name, x, r0, r1, chord, thick, n, stagger, angle=0):
    box = add("Part::Box", f"{name}Blade")
    box.Length, box.Width, box.Height = chord, r1 - r0, thick
    local = App.Placement(V(-chord / 2, 0, -thick / 2), App.Rotation())
    box.Placement = about_x(angle).multiply(App.Placement(V(x, r0, 0), App.Rotation(V(0, 1, 0), stagger)).multiply(local))
    return polar(box, name, n)


def op_pins(name, x, r0, r1, dia, n, angle=0):
    cyl = add("Part::Cylinder", f"{name}Pin")
    cyl.Radius, cyl.Height = dia / 2, r1 - r0
    cyl.Placement = about_x(angle).multiply(App.Placement(V(x, r0, 0), App.Rotation(V(1, 0, 0), -90)))
    return polar(cyl, name, n)


def op_axial_pins(name, x, r, dia, length, n, angle=0):
    cyl = add("Part::Cylinder", f"{name}Pin")
    cyl.Radius, cyl.Height = dia / 2, length
    cyl.Placement = about_x(angle).multiply(App.Placement(V(x - length / 2, r, 0), App.Rotation(V(0, 1, 0), 90)))
    return polar(cyl, name, n)


def op_loft(name, x, sections, n):
    """sections: [(r, [(x, r, z) points])] precomputed by freecad_build.py (same points as cadgen)."""
    sks = []
    for i, (r, pts) in enumerate(sections):
        sk = sketch(f"{name}Section{i}", App.Placement(V(0, r, 0), App.Rotation(V(1, 0, 0), 90)))  # local (x, y) = global (X, Z)
        bs = Part.BSplineCurve()
        bs.interpolate([V(px, pz, 0) for px, _, pz in pts], PeriodicFlag=True)
        sk.addGeometry(bs)
        sk.addConstraint(Sketcher.Constraint("Block", 0))
        sks.append(sk)
    loft = add("Part::Loft", f"{name}Blade")
    loft.Sections, loft.Solid, loft.Ruled = sks, True, True
    return polar(loft, name, n)


def op_duct(name, stations, wall):
    lofts = []
    for kind, dr in (("Outer", 0), ("Inner", wall)):
        circles = []
        for i, (x, y, r) in enumerate(stations):
            c = add("Part::Circle", f"{name}{kind}{i}")
            c.Radius = r - dr
            c.Placement = App.Placement(V(x, y, 0), App.Rotation(V(0, 1, 0), 90))
            circles.append(c)
        loft = add("Part::Loft", f"{name}{kind}")
        loft.Sections, loft.Solid, loft.Ruled = circles, True, True
        lofts.append(loft)
    cut = add("Part::Cut", name)
    cut.Base, cut.Tool = lofts
    return cut


def op_fins(name, pts, thick, n, angle=0):
    prof = polygon(f"{name}Profile", pts)
    prof.Placement = about_x(angle)
    ext = add("Part::Extrusion", f"{name}Blade")
    ext.Base, ext.Dir, ext.LengthFwd, ext.Symmetric, ext.Solid = prof, about_x(angle).Rotation.multVec(V(0, 0, 1)), thick, True, True
    return polar(ext, name, n)


def op_pipe(name, pts, dia):
    """Part::Cylinder per segment + Part::Sphere per elbow, fused (same primitives as cadgen)."""
    objs = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        a, b = V(*a), V(*b)
        cyl = add("Part::Cylinder", f"{name}Segment{i}")
        cyl.Radius, cyl.Height, cyl.Placement = dia / 2, (b - a).Length, App.Placement(a, App.Rotation(V(0, 0, 1), b - a))
        objs.append(cyl)
    for i, p in enumerate(pts[1:-1]):
        sph = add("Part::Sphere", f"{name}Elbow{i}")
        sph.Radius, sph.Placement = dia / 2, App.Placement(V(*p), App.Rotation())
        objs.append(sph)
    return fuse(objs, name)


def op_lathe(name, segs, origin, axis):
    """segs: [("line", p, q) | ("arc", p, mid, q)] in model coordinates, precomputed by freecad_build.py
    (the rounded profile cadgen revolves). A fixed Part::Feature: edit the radius in the model source."""
    edges = [Part.LineSegment(V(*s[1]), V(*s[2])).toShape() if s[0] == "line"
             else Part.Arc(V(*s[1]), V(*s[2]), V(*s[3])).toShape() for s in segs]
    feature = add("Part::Feature", name)
    feature.Shape = Part.Face(Part.Wire(edges)).revolve(V(*origin), V(*axis), 360)
    return feature


def circle(seed, name, origin, x, y, z, r, length, n, angle):
    """n copies of a primitive (along its local +Z) on a circle about the axis z through origin; x, y, z are
    the op frame from lib.shapes.frame(), precomputed by freecad_build.py."""
    frame = App.Placement(App.Matrix(x[0], y[0], z[0], origin[0], x[1], y[1], z[1], origin[1],
                                     x[2], y[2], z[2], origin[2], 0, 0, 0, 1))
    turn = App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), angle))
    seed.Placement = frame.multiply(turn).multiply(App.Placement(V(r, 0, -length / 2), App.Rotation()))
    return polar(seed, name, n, V(*z), V(*origin)) if n > 1 else seed


def op_hex_circle(name, origin, x, y, z, r, flats, length, n, angle=0):
    nut = add("Part::Prism", f"{name}Nut")
    nut.Polygon, nut.Circumradius, nut.Height = 6, flats / 3 ** 0.5, length
    return circle(nut, name, origin, x, y, z, r, length, n, angle)


def op_pin_circle(name, origin, x, y, z, r, dia, length, n, angle=0):
    pin = add("Part::Cylinder", f"{name}Pin")
    pin.Radius, pin.Height = dia / 2, length
    return circle(pin, name, origin, x, y, z, r, length, n, angle)


def fuse(objs, name):
    if len(objs) == 1:
        return objs[0]
    f = add("Part::MultiFuse", name)
    f.Shapes = objs
    return f


def build_part(label, ops):
    items = []
    for kind, name, *args in ops:
        if kind == "cut":
            base = fuse(items, f"{label}_upto_{name}")
            cut = add("Part::Cut", f"{label}_{name}")
            cut.Base, cut.Tool = base, op_revolve(name, *args)
            items = [cut]
        else:
            items.append(globals()[f"op_{kind}"](name, *args))
    result = fuse(items, label)
    result.Label = label
    return result


results = [(label, build_part(label, ops)) for label, _color, ops in data["parts"]]
doc.recompute()
bad = [o.Label for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
if bad:
    print("FC_ERRORS", bad)
steps = os.environ.get("FC_STEPS")
for label, obj in results:
    if steps:
        obj.Shape.exportStep(os.path.join(steps, f"{label}.step"))
doc.saveAs(os.environ["FC_OUT"])
print("FC_SAVED", os.environ["FC_OUT"], len(results), "parts")
