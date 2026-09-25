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
        raise SystemExit(f"could not open {path} (swFileLoadError {errors})")
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

class PartBuilder:
    """Builds one native part: named, fully dimensioned revolve sketches and circular patterns about X."""

    def __init__(self, sw):
        self.sw = sw
        self.doc = typed(sw.NewDocument(sw.GetUserPreferenceStringValue(PREF_TEMPLATE_PART), 0, 0, 0), "IModelDoc2")
        self.ext, self.sk, self.fm = self.doc.Extension, self.doc.SketchManager, self.doc.FeatureManager
        self.planes = [f.Name for f in features(self.doc) if f.GetTypeName2() == "RefPlane"]  # Front, Top, Right
        self._axis = None
        self.globals = {}

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
        self.globals[name] = value
        mgr = self.doc.GetEquationMgr()
        mgr.Add2(-1, f'"{name}" = {value}', True)

    def link(self, dim_full_name, global_name):
        """Drive a dimension (e.g. "D1@Struts") from a global variable."""
        self.doc.GetEquationMgr().Add2(-1, f'"{dim_full_name}" = "{global_name}"', True)

    def _polygon(self, pts):
        """Closed polyline with merged vertices; returns one ISketchPoint per vertex."""
        self.sk.AddToDB = True
        lines = [typed(self.sk.CreateLine(x0 * MM, y0 * MM, 0, x1 * MM, y1 * MM, 0), "ISketchLine")
                 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])]
        self.sk.AddToDB = False
        vertices = []
        for prev, line in zip(lines[-1:] + lines[:-1], lines):
            start, end = typed(line.GetStartPoint2(), "ISketchPoint"), typed(prev.GetEndPoint2(), "ISketchPoint")
            self.doc.ClearSelection2(True)
            start.Select4(False, None)
            end.Select4(True, None)
            self.doc.SketchAddConstraints("sgMERGEPOINTS")
            vertices.append(typed(line.GetStartPoint2(), "ISketchPoint"))
        return vertices, lines

    def _fix(self, segments):
        """Fix sketch geometry in place (fully defined, not meant to be edited by dimension)."""
        self.doc.ClearSelection2(True)
        for seg in segments:
            typed(seg, "ISketchSegment").Select4(True, None)
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

    def revolve(self, points, name):
        """Closed (x, r) profile on the Front Plane, revolved 360° about the X axis.

        Vertex i gets driving dimensions x<i> and r<i> in sketch "<name>Profile".
        """
        self.doc.ClearSelection2(True)
        self.select(self.planes[0], "PLANE")
        self.sk.InsertSketch(True)
        pts = [(float(x), float(r)) for x, r in points]
        vertices, _ = self._polygon(pts)
        xs = [x for x, _ in pts]
        self.sk.AddToDB = True
        centerline = self.sk.CreateCenterLine((min(xs) - 50) * MM, 0, 0, (max(xs) + 50) * MM, 0, 0)
        self.sk.AddToDB = False
        self._fix([centerline])
        self._dimension_points(vertices, pts)
        self.sk.InsertSketch(True)
        self.last_feature(f"{name}Profile")
        feat = self.fm.FeatureRevolve2(True, True, False, False, False, False, 0, 0, 2 * math.pi, 0,
                                       False, False, 0, 0, 0, 0, 0, True, True, True)
        if feat is None:
            raise RuntimeError(f"revolve {name} failed")
        return self.last_feature(name)

    def axis(self):
        """Reference axis along X (Front ∩ Top plane), created once."""
        if self._axis is None:
            self.doc.ClearSelection2(True)
            self.select(self.planes[0], "PLANE")
            self.select(self.planes[1], "PLANE", append=True)
            self.doc.InsertAxis2(True)
            self._axis = self.last_feature("EngineAxis")
        return self._axis

    def revolve_circle(self, x, r, radius, name):
        """Torus: circle of `radius` centred at (x, r) on the Front Plane, revolved about X."""
        self.doc.ClearSelection2(True)
        self.select(self.planes[0], "PLANE")
        self.sk.InsertSketch(True)
        self.sk.AddToDB = True
        circle = self.sk.CreateCircleByRadius(x * MM, r * MM, 0, radius * MM)
        centerline = self.sk.CreateCenterLine((x - radius - 50) * MM, 0, 0, (x + radius + 50) * MM, 0, 0)
        self.sk.AddToDB = False
        self._fix([circle, centerline])
        self.sk.InsertSketch(True)
        self.last_feature(f"{name}Profile")
        if self.fm.FeatureRevolve2(True, True, False, False, False, False, 0, 0, 2 * math.pi, 0,
                                   False, False, 0, 0, 0, 0, 0, True, True, True) is None:
            raise RuntimeError(f"revolve {name} failed")
        return self.last_feature(name)

    def color(self, hex_rgb):
        """Part appearance colour from '#RRGGBB'."""
        values = list(self.doc.MaterialPropertyValues)
        values[0:3] = [int(hex_rgb[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        self.doc.MaterialPropertyValues = values

    def blade_ring(self, x, r0, r1, chord, thick, n, stagger, name, round_section=False):
        """One flat staggered blade (sketched on a plane at radius r0, extruded to r1) + circular pattern of n.

        round_section=True makes a round pin of diameter `chord` instead (thick/stagger ignored).
        Editable afterwards: global "<name>_count" drives the pattern count; the extrude depth
        (span) is D1@<name>Blade and the plane offset (root radius) is D1@<name>Plane.
        """
        axis = self.axis()  # before any selection: creating it clears the selection set
        self.doc.ClearSelection2(True)
        self.select(self.planes[1], "PLANE")  # Top Plane (XZ), normal +Y = radial direction
        plane = self.fm.InsertRefPlane(8, r0 * MM, 0, 0, 0, 0)  # 8 = swRefPlaneReferenceConstraint_Distance
        if plane is None:
            raise RuntimeError(f"{name}: offset plane failed")
        plane_name = self.last_feature(f"{name}Plane").Name
        self.doc.ClearSelection2(True)
        self.select(plane_name, "PLANE")
        self.sk.InsertSketch(True)
        # Sketch coordinates on this plane: sketch X = model X, sketch Y = model -Z (Top Plane orientation).
        a = math.radians(stagger)
        u, v = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
        cx, cy = x, 0.0
        corners = [(cx + su * chord / 2 * u[0] + sv * thick / 2 * v[0], cy + su * chord / 2 * u[1] + sv * thick / 2 * v[1])
                   for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        if round_section:
            self.sk.AddToDB = True
            section = [self.sk.CreateCircleByRadius(cx * MM, 0, 0, chord / 2 * MM)]
            self.sk.AddToDB = False
        else:
            section = self._polygon(corners)[1]
        self._fix(section)
        self.sk.InsertSketch(True)
        self.last_feature(f"{name}Sketch")
        feat = self.fm.FeatureExtrusion3(True, False, False, 0, 0, (r1 - r0) * MM, 0, False, False, False, False,
                                         0, 0, False, False, False, False, True, True, True, 0, 0, False)
        if feat is None:
            raise RuntimeError(f"{name}: blade extrude failed")
        blade = self.last_feature(f"{name}Blade")
        self.doc.ClearSelection2(True)
        blade.Select2(False, 4)  # mark 4 = features to pattern
        axis.Select2(True, 1)    # mark 1 = pattern axis
        pat = self.fm.FeatureCircularPattern5(n, 2 * math.pi, False, "NULL", False, True, False, False,
                                              False, False, 1, 0, "NULL", False)
        if pat is None:
            raise RuntimeError(f"{name}: circular pattern failed")
        self.last_feature(name)
        self.add_global(f"{name}_count", n)
        self.link(f"D1@{name}", f"{name}_count")

    def save(self, path):
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
