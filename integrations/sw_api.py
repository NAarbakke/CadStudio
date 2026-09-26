"""Thin typed layer over the SolidWorks COM API (Windows, pywin32), shared by the SolidWorks scripts.

Every COM object is wrapped in its typed interface from the generated SolidWorks type library, so
getters are always method calls (doc.GetTitle()) and out-parameters work. SolidWorks must already
be running (the 3DEXPERIENCE edition cannot be started over COM). The API works in metres and
radians; the helpers here take mm and degrees.
"""
import math

import pythoncom
import win32com.client
from win32com.client import gencache

TYPELIB = "{83A33D31-27C5-11CE-BFD4-00400513BB57}"  # "SldWorks <version> Type Library"
MM = 0.001

DOC_PART, DOC_ASSEMBLY = 1, 2              # swDocumentTypes_e
SAVE_SILENT = 1                            # swSaveAsOptions_e
PREF_TEMPLATE_PART, PREF_TEMPLATE_ASM = 8, 9  # swUserPreferenceStringValue_e


def _typelib_module():
    """Generate (once) and return the Python wrappers for the newest registered SolidWorks type library."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"TypeLib\{TYPELIB}") as k:
        versions = [winreg.EnumKey(k, i) for i in range(winreg.QueryInfoKey(k)[0])]
    major, minor = max(tuple(int(p, 16) for p in v.split(".")) for v in versions)
    return gencache.EnsureModule(TYPELIB, 0, major, minor)


_mod = None


def typed(obj, iface):
    """Wrap a raw/dynamic COM object in the named SolidWorks interface (e.g. "IModelDoc2")."""
    if obj is None:
        return None
    return getattr(_mod, iface)(obj._oleobj_ if hasattr(obj, "_oleobj_") else obj)


def connect():
    global _mod
    _mod = _mod or _typelib_module()
    try:
        app = win32com.client.GetActiveObject("SldWorks.Application")
    except pythoncom.com_error:
        raise SystemExit("SolidWorks is not running. Open SolidWorks (and log in) first, then rerun.")
    sw = typed(app, "ISldWorks")
    sw.Visible = True
    return sw


PREF_INPUT_DIM_ON_CREATE = 10  # swUserPreferenceToggle_e.swInputDimValOnCreate


class no_dimension_prompts:
    """Turn off "Input dimension value" (a modal Modify box per new dimension blocks the API) and restore it."""

    def __init__(self, sw):
        self.sw = sw

    def __enter__(self):
        self.saved = self.sw.GetUserPreferenceToggle(PREF_INPUT_DIM_ON_CREATE)
        self.sw.SetUserPreferenceToggle(PREF_INPUT_DIM_ON_CREATE, False)

    def __exit__(self, *exc):
        self.sw.SetUserPreferenceToggle(PREF_INPUT_DIM_ON_CREATE, self.saved)


def open_docs(sw):
    """[(IModelDoc2, title, path)] for every open document."""
    out, d = [], sw.GetFirstDocument()
    while d is not None:
        d = typed(d, "IModelDoc2")
        out.append((d, d.GetTitle(), d.GetPathName()))
        d = d.GetNext()
    return out


def open_doc(sw, path):
    import pathlib
    path = str(pathlib.Path(path).resolve())  # SolidWorks resolves relative paths against its own cwd
    kind = DOC_ASSEMBLY if path.upper().endswith(".SLDASM") else DOC_PART
    doc, errors, _warnings = sw.OpenDoc6(path, kind, 1, "", 0, 0)  # typed call returns out-params; 1 = Silent
    if doc is None:
        hint = " - a document with the same name is open from another folder; close it" if errors == 65536 else ""
        raise SystemExit(f"could not open {path} (swFileLoadError {errors}){hint}")
    return typed(doc, "IModelDoc2")


def save_as(doc, path):
    status = doc.SaveAs3(str(path), 0, SAVE_SILENT)
    if status != 0:
        raise SystemExit(f"saving {path} failed (swFileSaveError {status})")


def features(doc):
    f = doc.FirstFeature()
    while f is not None:
        f = typed(f, "IFeature")
        yield f
        f = f.GetNextFeature()


def dimensions(doc):
    """Yield (feature, IDimension) for every dimension shown on a feature or sketch."""
    for f in features(doc):
        d = f.GetFirstDisplayDimension()
        while d is not None:
            yield f, typed(typed(d, "IDisplayDimension").GetDimension2(0), "IDimension")
            d = f.GetNextDisplayDimension(d)


# ---------- building parts ----------

def _array(values):
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in values])


def _about_x(p, angle):
    """Rotate model point p (mm) about the X axis by `angle` degrees (right-handed, as build123d Rot)."""
    a = math.radians(angle)
    x, y, z = p
    return x, y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)


class PartBuilder:
    """Builds one native part from a recipe (models/src/lib/shapes.py): one method per op kind.

    Revolve sketches are fully dimensioned (vertex i -> x<i>/r<i>); blade, pin and loft sections are
    fixed geometry on named reference planes; rings are one feature + a circular pattern whose count
    is the global variable "<name>_count".
    """

    def __init__(self, sw):
        self.sw = sw
        self.doc = typed(sw.NewDocument(sw.GetUserPreferenceStringValue(PREF_TEMPLATE_PART), 0, 0, 0), "IModelDoc2")
        self.ext, self.sk, self.fm = self.doc.Extension, self.doc.SketchManager, self.doc.FeatureManager
        self.mu = typed(sw.GetMathUtility(), "IMathUtility")
        self.planes = [f.Name for f in features(self.doc) if f.GetTypeName2() == "RefPlane"]  # Front, Top, Right
        self._axis = None
        self.ref_geometry = []  # our planes/axis, hidden on save

    def build(self, ops):
        for kind, name, *args in ops:
            getattr(self, kind)(name, *args)

    # ---- selection, naming, equations ----

    def select(self, name, kind, append=False, mark=0, xyz=(0, 0, 0)):
        x, y, z = (c * MM for c in xyz)
        if not self.ext.SelectByID2(name, kind, x, y, z, append, mark, None, 0):
            raise RuntimeError(f"could not select {kind} {name!r} at {xyz}")

    def last_feature(self, name):
        f = typed(self.doc.FeatureByPositionReverse(0), "IFeature")
        f.Name = name
        return f

    def add_global(self, name, value):
        """Global variable (Tools > Equations) that features can be driven from."""
        self.doc.GetEquationMgr().Add2(-1, f'"{name}" = {value}', True)

    def link(self, dim_full_name, global_name):
        """Drive a dimension (e.g. "D1@Struts") from a global variable."""
        self.doc.GetEquationMgr().Add2(-1, f'"{dim_full_name}" = "{global_name}"', True)

    # ---- reference geometry ----

    def axis(self):
        """Reference axis along X (Front ∩ Top plane), created once."""
        if self._axis is None:
            self.doc.ClearSelection2(True)
            self.select(self.planes[0], "PLANE")
            self.select(self.planes[1], "PLANE", append=True)
            self.doc.InsertAxis2(True)
            self._axis = self.last_feature("EngineAxis")
            self.ref_geometry.append(("EngineAxis", "AXIS"))
        return self._axis

    def _plane(self, name, refs, c1, v1, c2=0, v2=0):
        """Reference plane from [(ref name, kind)] + swRefPlaneReferenceConstraints_e (8 distance, 4 coincident, 16 angle)."""
        self.doc.ClearSelection2(True)
        for i, (ref, kind) in enumerate(refs):
            self.select(ref, kind, append=i > 0, mark=i)
        if self.fm.InsertRefPlane(c1, v1, c2, v2, 0, 0) is None:
            raise RuntimeError(f"{name}: reference plane failed")
        self.ref_geometry.append((name, "PLANE"))
        return self.last_feature(name).Name

    def _radial_plane(self, name, r, angle):
        """Plane normal to the radial direction at `angle` (deg about X from +Y), at distance r from the axis."""
        base = self.planes[1]  # Top Plane (XZ), normal +Y
        if angle:
            self.axis()
            base = self._plane(f"{name}Angle", [("EngineAxis", "AXIS"), (base, "PLANE")], 4, 0, 16, math.radians(angle))
        return self._plane(f"{name}Plane", [(base, "PLANE")], 8, r * MM)

    # ---- sketches ----

    def _sketch(self, plane):
        """Open a sketch on `plane`; returns f(model point mm) -> sketch point mm (x, y, z)."""
        self.doc.ClearSelection2(True)
        self.select(plane, "PLANE")
        self.sk.InsertSketch(True)
        xf = typed(self.sk.ActiveSketch, "ISketch").ModelToSketchTransform

        def to_sketch(p):
            q = typed(typed(self.mu.CreatePoint(_array(c * MM for c in p)), "IMathPoint").MultiplyTransform(xf), "IMathPoint")
            return tuple(c / MM for c in q.ArrayData)
        return to_sketch

    def _close_sketch(self, name):
        self.sk.InsertSketch(True)
        return self.last_feature(name)

    def _on_plane(self, to_sketch, origin, normal, what):
        """Check the sketch plane passes through `origin`; return True if `normal` points out of its +Z side."""
        z0 = to_sketch(origin)[2]
        if abs(z0) > 1e-3:
            raise RuntimeError(f"{what}: sketch plane is {z0:.3f} mm off the intended position")
        return to_sketch(tuple(o + n for o, n in zip(origin, normal)))[2] > 0

    def _merge(self, a, b):
        self.doc.ClearSelection2(True)
        typed(a, "ISketchPoint").Select4(False, None)
        typed(b, "ISketchPoint").Select4(True, None)
        self.doc.SketchAddConstraints("sgMERGEPOINTS")

    def _polygon(self, pts):
        """Closed polyline (sketch mm) with merged vertices; returns (vertex ISketchPoints, lines)."""
        self.sk.AddToDB = True
        lines = [typed(self.sk.CreateLine(x0 * MM, y0 * MM, 0, x1 * MM, y1 * MM, 0), "ISketchLine")
                 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])]
        self.sk.AddToDB = False
        for prev, line in zip(lines[-1:] + lines[:-1], lines):
            self._merge(line.GetStartPoint2(), prev.GetEndPoint2())
        return [typed(line.GetStartPoint2(), "ISketchPoint") for line in lines], lines

    def _fix(self, segments):
        """Fix sketch geometry in place (fully defined, not meant to be edited by dimension)."""
        self.doc.ClearSelection2(True)
        for seg in segments:
            typed(seg, "ISketchSegment").Select4(True, None)
        self.doc.SketchAddConstraints("sgFIXED")

    def _fix_points(self, points):
        self.doc.ClearSelection2(True)
        for pt in points:
            typed(pt, "ISketchPoint").Select4(True, None)
        self.doc.SketchAddConstraints("sgFIXED")

    def _dimension_points(self, vertices, points):
        """Dimension every vertex from the origin: x<i> horizontally, r<i> vertically (named by vertex index)."""
        for i, (vertex, (x, r)) in enumerate(zip(vertices, points)):
            for axis in ("x", "r"):
                self.doc.ClearSelection2(True)
                vertex.Select4(False, None)
                self.select("Point1@Origin", "EXTSKETCHPOINT", append=True)
                if (x if axis == "x" else r) == 0:  # a zero-length dimension is impossible: align with the origin
                    self.doc.SketchAddConstraints("sgVERTICALPOINTS2D" if axis == "x" else "sgHORIZONTALPOINTS2D")
                    continue
                place = (x + 15, r + 25, 0) if axis == "x" else (x - 25, r / 2, 0)
                add = self.doc.AddHorizontalDimension2 if axis == "x" else self.doc.AddVerticalDimension2
                disp = add(*(c * MM for c in place))
                if disp is not None:  # None when already fully constrained (e.g. a point on the origin)
                    typed(typed(disp, "IDisplayDimension").GetDimension2(0), "IDimension").Name = f"{axis}{i}"

    def _centerline(self, xs, y=0.0):
        self.sk.AddToDB = True
        line = self.sk.CreateCenterLine((min(xs) - 50) * MM, y * MM, 0, (max(xs) + 50) * MM, y * MM, 0)
        self.sk.AddToDB = False
        self._fix([line])

    # ---- features ----

    def _revolve(self, name, cut=False):
        if self.fm.FeatureRevolve2(True, True, False, cut, False, False, 0, 0, 2 * math.pi, 0,
                                   False, False, 0, 0, 0, 0, 0, True, True, True) is None:
            raise RuntimeError(f"revolve {name} failed")
        return self.last_feature(name)

    def _extrude(self, name, depth, outward=True, midplane=False):
        # FeatureExtrusion3: Sd, Flip, Dir, T1 (0 blind, 6 mid plane), T2, D1, D2, ... Merge, UseFeatScope, UseAutoSelect
        if self.fm.FeatureExtrusion3(True, False, not outward, 6 if midplane else 0, 0, depth * MM, 0,
                                     False, False, False, False, 0, 0, False, False, False, False,
                                     True, True, True, 0, 0, False) is None:
            raise RuntimeError(f"{name}: extrude failed")
        return self.last_feature(name)

    def _bodies(self):
        return [typed(b, "IBody2") for b in typed(self.doc, "IPartDoc").GetBodies2(0, True) or []]  # 0 = solid

    def _pattern(self, seed, name, n, bodies_before):
        """Circular pattern of `seed` about the engine axis; count driven by global "<name>_count".

        A seed that merged into an existing body (blades on a disk) is patterned as a feature; a seed
        that made its own body (free-standing stator vanes) is patterned as a body.
        """
        axis = self.axis()
        self.doc.ClearSelection2(True)
        bodies = self._bodies()
        # Only a seed that added a body is free-standing; a seed that fused bodies renames the merged
        # body, so a name check alone would pattern the whole merged body. GetBodies2 order is arbitrary.
        new_bodies = [b for b in bodies if b.Name not in bodies_before] if len(bodies) > len(bodies_before) else []
        if new_bodies:
            data = typed(self.doc.SelectionManager, "ISelectionMgr").CreateSelectData()
            data.Mark = 256  # bodies to pattern
            for body in new_bodies:
                body.Select2(True, data)
        else:
            seed.Select2(False, 4)  # mark 4 = features to pattern
        axis.Select2(True, 1)   # mark 1 = pattern axis
        if self.fm.FeatureCircularPattern5(n, 2 * math.pi, False, "NULL", False, True, False, False,
                                           False, False, 1, 0, "NULL", False) is None:
            raise RuntimeError(f"{name}: circular pattern failed")
        self.last_feature(name)
        self.add_global(f"{name}_count", n)
        self.link(f"D1@{name}", f"{name}_count")

    # ---- ops (same names and arguments as the recipe ops in models/src/lib/shapes.py) ----

    def revolve(self, name, points, cut=False, axis_y=0.0):
        """Closed (x, r) profile on the Front Plane revolved 360° about X (or a parallel line at axis_y).

        Vertex i -> dimensions x<i>/r<i> in "<name>Profile", measured from the origin (r<i> = axis_y + r).
        """
        self._sketch(self.planes[0])  # Front Plane: sketch coordinates = model X, Y
        pts = [(float(x), float(r) + axis_y) for x, r in points]
        vertices, _ = self._polygon(pts)
        self._centerline([x for x, _ in pts], axis_y)
        self._dimension_points(vertices, pts)
        self._close_sketch(f"{name}Profile")
        return self._revolve(name, cut)

    def cut(self, name, points):
        return self.revolve(name, points, cut=True)

    def fins(self, name, points, thick, n):
        """n flat fins: (x, r) planform on the Front Plane ("<name>Profile", vertices x<i>/r<i>), mid-plane extrude, pattern."""
        self.axis()
        before = {b.Name for b in self._bodies()}
        self._sketch(self.planes[0])
        pts = [(float(x), float(r)) for x, r in points]
        vertices, _ = self._polygon(pts)
        self._dimension_points(vertices, pts)
        self._close_sketch(f"{name}Profile")
        self._pattern(self._extrude(f"{name}Blade", thick, midplane=True), name, n, before)

    def offset_revolve(self, name, points, axis_y):
        return self.revolve(name, points, axis_y=axis_y)

    def duct(self, name, stations, wall):
        """Hollow duct: loft through outer circles [(x, y_centre, r)], then cut-loft through circles r - wall.

        Sketches "<name>Outer<i>"/"<name>Inner<i>" on planes "<name><i>Plane" normal to X.
        """
        outer, inner = [], []
        for i, (x, y, r) in enumerate(stations):
            plane = self._plane(f"{name}{i}Plane", [(self.planes[2], "PLANE")], 8, abs(x) * MM)  # Right Plane = YZ
            for kind, radius, profiles in (("Outer", r, outer), ("Inner", r - wall, inner)):
                to_sketch = self._sketch(plane)
                self._on_plane(to_sketch, (x, y, 0), (1, 0, 0), name)
                cx, cy, _ = to_sketch((x, y, 0))
                # SolidWorks 2026 will not loft from a full circle centred on the engine axis (the same
                # circle 1 mm off-axis works), so on-axis stations are two semicircles. Arcs everywhere
                # make other station pairs fail instead, so off-axis stations stay plain circles.
                left, right = ((cx - radius) * MM, cy * MM, 0), ((cx + radius) * MM, cy * MM, 0)
                self.sk.AddToDB = True
                if abs(y) < 1e-6:
                    segs = [typed(self.sk.CreateArc(cx * MM, cy * MM, 0, *a, *b, 1), "ISketchArc")
                            for a, b in ((right, left), (left, right))]
                    self._merge(segs[0].GetEndPoint2(), segs[1].GetStartPoint2())
                    self._merge(segs[1].GetEndPoint2(), segs[0].GetStartPoint2())
                    self._merge(segs[0].GetCenterPoint2(), segs[1].GetCenterPoint2())
                else:
                    segs = [self.sk.CreateCircleByRadius(cx * MM, cy * MM, 0, radius * MM)]
                self.sk.AddToDB = False
                self._fix(segs)
                if len(segs) == 2:  # a fixed arc only pins its circle; its ends can still slide along it
                    self._fix_points([segs[0].GetStartPoint2(), segs[0].GetEndPoint2()])
                profiles.append(self._close_sketch(f"{name}{kind}{i}"))
        for profiles, cut in ((outer, False), (inner, True)):
            self.doc.ClearSelection2(True)
            for p in profiles:
                p.Select2(True, 1)  # mark 1 = loft profiles
            if cut:
                feat = self.fm.InsertCutBlend(False, True, False, 1, 0, 0, False, 0, 0, 0, True, True)
            else:
                feat = self.fm.InsertProtrusionBlend2(False, True, False, 1, 0, 0, 1, 1, False, False, False, 0, 0, 0,
                                                      True, True, True, 0)
            if feat is None:
                raise RuntimeError(f"{name}: {'cut ' if cut else ''}loft failed")
            self.last_feature(f"{name}{'Bore' if cut else ''}")

    def spline(self, name, points):
        """Spline through (x, r) points (first one on the axis), closed down to the axis and revolved."""
        self._sketch(self.planes[0])
        pts = [(float(x), float(r)) for x, r in points]
        (x0, _), (xl, rl) = pts[0], pts[-1]
        self.sk.AddToDB = True
        spl = typed(self.sk.CreateSpline2(_array(c * MM for x, r in pts for c in (x, r, 0)), False), "ISketchSpline")
        down = typed(self.sk.CreateLine(xl * MM, rl * MM, 0, xl * MM, 0, 0), "ISketchLine")
        back = typed(self.sk.CreateLine(xl * MM, 0, 0, x0 * MM, 0, 0), "ISketchLine")
        self.sk.AddToDB = False
        self._merge(spl.GetPoints2()[-1], down.GetStartPoint2())
        self._merge(down.GetEndPoint2(), back.GetStartPoint2())
        self._merge(back.GetEndPoint2(), spl.GetPoints2()[0])
        self._centerline([x0, xl])
        vertices = [typed(p, "ISketchPoint") for p in spl.GetPoints2()] + [typed(down.GetEndPoint2(), "ISketchPoint")]
        self._dimension_points(vertices, pts + [(xl, 0)])
        self._close_sketch(f"{name}Profile")
        return self._revolve(name)

    def torus(self, name, x, r, tube_r):
        """Circle of radius tube_r centred at (x, r) on the Front Plane, revolved about X."""
        self._sketch(self.planes[0])
        self.sk.AddToDB = True
        circle = self.sk.CreateCircleByRadius(x * MM, r * MM, 0, tube_r * MM)
        self.sk.AddToDB = False
        self._fix([circle])
        self._centerline([x - tube_r, x + tube_r])
        self._close_sketch(f"{name}Profile")
        return self._revolve(name)

    def _radial_ring(self, name, x, r0, r1, n, angle, draw):
        """Section drawn by draw(to_sketch, rot) on a radial plane at r0, extruded out to r1, patterned n times."""
        self.axis()  # before any selection: creating it clears the selection set
        before = {b.Name for b in self._bodies()}
        to_sketch = self._sketch(self._radial_plane(name, r0, angle))
        rot = lambda p: _about_x(p, angle)
        outward = self._on_plane(to_sketch, rot((x, r0, 0)), rot((0, 1, 0)), name)
        self._fix(draw(to_sketch, rot))
        self._close_sketch(f"{name}Sketch")
        self._pattern(self._extrude(f"{name}Blade", r1 - r0, outward), name, n, before)

    def ring(self, name, x, r0, r1, chord, thick, n, stagger, angle=0):
        """n flat blades (chord x thick, staggered about the radial axis) from r0 to r1; span = D1@<name>Blade."""
        a = math.radians(stagger)  # build123d Rot(0, stagger, 0): local (u, w) -> (u cos a + w sin a, -u sin a + w cos a)
        corners = [(x + u * math.cos(a) + w * math.sin(a), r0, -u * math.sin(a) + w * math.cos(a))
                   for u, w in ((-chord / 2, -thick / 2), (chord / 2, -thick / 2), (chord / 2, thick / 2), (-chord / 2, thick / 2))]
        self._radial_ring(name, x, r0, r1, n, angle,
                          lambda to_sketch, rot: self._polygon([to_sketch(rot(c))[:2] for c in corners])[1])

    def pins(self, name, x, r0, r1, dia, n, angle=0):
        """n radial round pins of diameter dia from r0 to r1."""
        def draw(to_sketch, rot):
            cx, cy, _ = to_sketch(rot((x, r0, 0)))
            self.sk.AddToDB = True
            circle = self.sk.CreateCircleByRadius(cx * MM, cy * MM, 0, dia / 2 * MM)
            self.sk.AddToDB = False
            return [circle]
        self._radial_ring(name, x, r0, r1, n, angle, draw)

    def axial_pins(self, name, x, r, dia, length, n, angle=0):
        """n cylinders along X centred on x (mid-plane extrude from a plane at x)."""
        self.axis()
        before = {b.Name for b in self._bodies()}
        to_sketch = self._sketch(self._plane(f"{name}Plane", [(self.planes[2], "PLANE")], 8, abs(x) * MM))
        centre = _about_x((x, r, 0), angle)
        self._on_plane(to_sketch, centre, (1, 0, 0), name)
        cx, cy, _ = to_sketch(centre)
        self.sk.AddToDB = True
        circle = self.sk.CreateCircleByRadius(cx * MM, cy * MM, 0, dia / 2 * MM)
        self.sk.AddToDB = False
        self._fix([circle])
        self._close_sketch(f"{name}Sketch")
        self._pattern(self._extrude(f"{name}Pin", length, midplane=True), name, n, before)

    def loft(self, name, x, sections, n):
        """n blades lofted through closed-spline sections [(r, chord, thick, twist°)] on radial planes.

        Section points come from blade_section() in models/src/lib/shapes.py, the same points cadgen lofts.
        """
        from lib.shapes import blade_section  # models/src is on sys.path (see sw_build.py)
        self.axis()
        before, profiles = {b.Name for b in self._bodies()}, []
        for i, (r, chord, thick, twist) in enumerate(sections):
            to_sketch = self._sketch(self._radial_plane(f"{name}{i}", r, 0))
            self._on_plane(to_sketch, (x, r, 0), (0, 1, 0), name)
            pts = [to_sketch(p) for p in blade_section(x, r, chord, thick, twist)]
            self.sk.AddToDB = True
            spline = self.sk.CreateSpline2(_array(c * MM for p in pts + pts[:1] for c in p), False)  # repeated start = closed
            self.sk.AddToDB = False
            self._fix([spline])
            profiles.append(self._close_sketch(f"{name}Section{i}"))
        self.doc.ClearSelection2(True)
        for p in profiles:
            p.Select2(True, 1)  # mark 1 = loft profiles
        if self.fm.InsertProtrusionBlend2(False, True, False, 1, 0, 0, 1, 1, False, False, False, 0, 0, 0,
                                          True, True, True, 0) is None:
            raise RuntimeError(f"{name}: loft failed")
        self._pattern(self.last_feature(f"{name}Blade"), name, n, before)

    def color(self, hex_rgb):
        """Part appearance colour from '#RRGGBB'."""
        values = list(self.doc.MaterialPropertyValues)
        values[0:3] = [int(hex_rgb[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        self.doc.MaterialPropertyValues = values

    def save(self, path):
        self.doc.ClearSelection2(True)
        for name, kind in self.ref_geometry:
            self.select(name, kind, append=True)
        if self.ref_geometry:
            self.doc.BlankRefGeom()  # hide construction planes/axis
        self.doc.ClearSelection2(True)
        self.doc.ForceRebuild3(False)
        save_as(self.doc, path)
        return path


def build_assembly(sw, part_paths, path):
    """New assembly with each (already open) part placed at the origin and fixed: all parts share the engine frame."""
    doc = typed(sw.NewDocument(sw.GetUserPreferenceStringValue(PREF_TEMPLATE_ASM), 0, 0, 0), "IModelDoc2")
    asm = typed(doc, "IAssemblyDoc")
    identity = typed(sw.GetMathUtility(), "IMathUtility").CreateTransform(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]))
    comps = []
    for p in part_paths:
        comp = asm.AddComponent5(str(p), 0, "", False, "", 0, 0, 0)
        if comp is None:
            raise RuntimeError(f"could not insert {p}")
        comp = typed(comp, "IComponent2")
        comp.Transform2 = identity  # AddComponent centres the bounding box; snap the part origin to the assembly origin
        comps.append(comp)
    doc.ClearSelection2(True)
    for c in comps:
        c.Select4(True, None, False)
    asm.FixComponent()
    doc.ClearSelection2(True)
    doc.ForceRebuild3(False)
    save_as(doc, path)
    return doc
