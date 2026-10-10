"""Check native SolidWorks parts against the cadgen STEP export of the same model.

    .venv\\Scripts\\python integrations\\solidworks\\solidworks_verify.py nasa_lewis_small_turbojet [--dir models/nasa_lewis_small_turbojet/SolidWorks] [--parts ...]

Per part: rebuild errors, sketch status (all must be fully defined), and the geometry itself: the
part is exported to STEP and compared with the cadgen part (volume, and volume of the overlap, so a
misplaced or flipped feature fails even when its volume is right). Needs models/<model>/STEP/<model>.step.
"""
import argparse
import importlib
import pathlib
import sys
import tempfile

from cadgen import build123d as bd
from cadgen import read_step

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # integrations/, for compare.py

from compare import compare  # noqa: E402
from solidworks_api import connect, features, open_doc, save_as, typed  # noqa: E402

STATES = {1: "unknown", 2: "under", 3: "fully", 4: "over", 5: "no-solution"}  # swConstrainedStatus_e


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model")
    ap.add_argument("--dir", type=pathlib.Path)
    ap.add_argument("--parts", nargs="+")
    args = ap.parse_args()
    models = pathlib.Path(__file__).resolve().parents[2] / "models"
    folder = args.dir or models / args.model / "SolidWorks"
    reference = {c.label: c for c in read_step(str(models / args.model / "STEP" / f"{args.model}.step")).leaves}
    sys.path[:0] = [str(models / args.model / "src"), str(models)]
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
