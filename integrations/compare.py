"""Geometry check shared by the native-CAD builders: is a part rebuilt in SolidWorks/FreeCAD the same
solid as the cadgen part? Compares volume, and volume of the overlap, so a misplaced or flipped
feature fails even when its volume is right.
"""
import random

from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
from OCP.TopTools import TopTools_ListOfShape

TOLERANCE = 0.001  # 0.1 %; a 7° misplaced pin ring in the turbojet liner already costs 0.7 % overlap
# Lofts: sections are identical, but each kernel interpolates the surface between them its own way
# (fan blade, 8 stations, ruled in cadgen: one blade 0.006 % volume, slices within 0.5 %, 1.8 % near the tip).
LOFT_TOLERANCE = 0.002


def volume(shape, eps=1e-6):
    """Volume by adaptive integration: build123d's default `.volume` is ~10 % off on spline lofts (fan blades)."""
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape if hasattr(shape, "IsNull") else shape.wrapped, props, eps, False)
    return props.Mass()


def common_volume(a, b, fuzz=1e-3):
    """Volume of a ∩ b. Fuzzy boolean: the two solids share almost every face, which plain booleans get wrong."""
    op, args, tools = BRepAlgoAPI_Common(), TopTools_ListOfShape(), TopTools_ListOfShape()
    args.Append(a.wrapped)
    tools.Append(b.wrapped)
    op.SetArguments(args)
    op.SetTools(tools)
    op.SetFuzzyValue(fuzz)
    op.Build()
    return volume(op.Shape())


def sampled_iou(a, b, n=600, seed=1):
    """Overlap estimated by classifying random points in b's bounding box as inside a and/or b.

    Fallback for when the fuzzy boolean returns nothing (cone tips, many nearly coincident faces).
    """
    rnd, box = random.Random(seed), b.bounding_box()
    def inside(shape, p):
        return any(BRepClass3d_SolidClassifier(s.wrapped, gp_Pnt(*p), 1e-3).State() == TopAbs_IN for s in shape.solids())
    both = either = 0
    for _ in range(n):
        p = (rnd.uniform(box.min.X, box.max.X), rnd.uniform(box.min.Y, box.max.Y), rnd.uniform(box.min.Z, box.max.Z))
        ia, ib = inside(a, p), inside(b, p)
        both += ia and ib
        either += ia or ib
    return both / either if either else 1.0


def compare(native, cad, lofted):
    """(good, v_native, v_cad, note) for a native CAD part against its cadgen part."""
    v_native, v_cad = volume(native), volume(cad)
    v_common = common_volume(native, cad)
    tolerance = LOFT_TOLERANCE if lofted else TOLERANCE
    note = f"overlap {v_common / v_cad:7.2%}"
    if v_common < 0.01 * v_cad:  # the boolean gave up: check the geometry by point sampling instead
        iou = sampled_iou(native, cad)
        note = f"overlap {iou:7.2%} (sampled, boolean failed)"
        v_common = v_cad if iou >= (0.99 if lofted else 0.998) else v_cad * iou
    good = max(abs(v_native - v_cad), abs(v_common - v_cad)) / v_cad < tolerance
    return good, v_native, v_cad, note
