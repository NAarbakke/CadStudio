"""Check native SolidWorks parts against the cadgen STEP export of the same model.

    .venv\\Scripts\\python integrations\\sw_verify.py turbojet [--dir models/SolidWorks/turbojet] [--parts ...]

Per part: rebuild errors, sketch status (all must be fully defined), and the geometry itself: the
part is exported to STEP and compared with the cadgen part (volume, and volume of the overlap, so a
misplaced or flipped feature fails even when its volume is right). Needs models/STEP/<model>.step.
"""
import argparse
import importlib
import pathlib
import sys
import tempfile

from cadgen import build123d as bd
from cadgen import read_step
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
from OCP.TopTools import TopTools_ListOfShape
from sw_api import connect, features, open_doc, save_as, typed

TOLERANCE = 0.001  # 0.1 %; a 7° misplaced pin ring in the turbojet liner already costs 0.7 % overlap
# Lofts: sections are identical, but each kernel interpolates the surface between them its own way
# (fan blade, 8 stations, ruled in cadgen: one blade 0.006 % volume, slices within 0.5 %, 1.8 % near the tip).
LOFT_TOLERANCE = 0.002
STATES = {1: "unknown", 2: "under", 3: "fully", 4: "over", 5: "no-solution"}  # swConstrainedStatus_e


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
    import random
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


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model")
    ap.add_argument("--dir", type=pathlib.Path)
    ap.add_argument("--parts", nargs="+")
    args = ap.parse_args()
    folder = args.dir or pathlib.Path("models/SolidWorks") / args.model
    reference = {c.label: c for c in read_step(f"models/STEP/{args.model}.step").leaves}
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "models" / "src"))
    lofted = {name for name, _, ops in importlib.import_module(args.model).parts() if any(op[0] in ("loft", "duct") for op in ops)}
    sw = connect()
    tmp = pathlib.Path(tempfile.mkdtemp())
    ok = True
    for path in sorted(folder.glob("*.SLDPRT")):
        name = path.stem
        if name.startswith("~$") or (args.parts and name not in args.parts):  # ~$ = SolidWorks lock file
            continue
        doc = open_doc(sw, path)
        doc.ForceRebuild3(False)
        errors = [f.Name for f in features(doc) if f.GetErrorCode2()[0] != 0]
        loose = [f.Name for f in features(doc) if f.GetTypeName2() == "ProfileFeature"
                 and STATES.get(typed(f.GetSpecificFeature2(), "ISketch").GetConstrainedStatus()) != "fully"]
        step = tmp / f"{name}.step"
        save_as(doc, step)
        sw.CloseDoc(doc.GetTitle())

        good, v_sw, v_cad, overlap = compare(bd.import_step(str(step)), reference[name], name in lofted)
        good = good and not errors and not loose
        ok &= good
        print(f"{'OK ' if good else 'BAD'} {name:20s} SW {v_sw / 1e6:9.4f} L  cadgen {v_cad / 1e6:9.4f} L  "
              f"{overlap}" + (f"  rebuild errors {errors}" if errors else "")
              + (f"  not fully defined {loose}" if loose else ""), flush=True)
    print("ALL OK" if ok else "PROBLEMS FOUND")


if __name__ == "__main__":
    main()
