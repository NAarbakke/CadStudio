"""Build a model as native, parametric SolidWorks parts + assembly (feature tree, named dimensions).

    .venv\\Scripts\\python integrations\\sw_build.py MODEL [--parts NAME ...] [--out DIR]

Geometry comes from the model's parts() recipes in models/src (the same numbers the STEP export
uses). Revolved profiles are sketches "<Feature>Profile" whose vertex i is driven by dimensions
x<i>/r<i> (mm from the origin); blade/pin rows are one feature + a circular pattern whose count is
the global variable "<Feature>_count". Edit them with integrations/sw_edit.py.
Output: models/SolidWorks/<model>/. SolidWorks must be open.
"""
import argparse
import importlib
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "models" / "src"))

from sw_api import PartBuilder, build_assembly, connect, no_dimension_prompts, open_docs  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model", help="model script name in models/src, e.g. turbofan")
    ap.add_argument("--parts", nargs="+", help="build only these parts (no assembly)")
    ap.add_argument("--out", type=pathlib.Path)
    args = ap.parse_args()
    out = (args.out or pathlib.Path("models/SolidWorks") / args.model).resolve()
    out.mkdir(parents=True, exist_ok=True)
    recipes = importlib.import_module(args.model).parts()  # model data only; nothing is built on import
    if args.parts:
        recipes = [r for r in recipes if r[0] in args.parts]
    sw = connect()
    for _, title, path in sorted(open_docs(sw), key=lambda d: not d[1].upper().endswith(".SLDASM")):
        if path and pathlib.Path(path).parent == out:  # old copies still open would block saving
            sw.CloseDoc(title)

    paths = []
    with no_dimension_prompts(sw):
        for name, color, ops in recipes:
            t = time.time()
            b = PartBuilder(sw)
            b.build(ops)
            b.color(color)
            paths.append(b.save(out / f"{name}.SLDPRT"))
            print(f"built {name}.SLDPRT ({time.time() - t:.0f} s)", flush=True)
    if not args.parts:
        build_assembly(sw, paths, out / f"{args.model}.SLDASM")
        print("built", out / f"{args.model}.SLDASM")
    # Close what was built (all saved above): leaving parts open blocks the next model's parts
    # with the same file name (e.g. stage1_case) from opening.
    for _, title, path in sorted(open_docs(sw), key=lambda d: not d[1].upper().endswith(".SLDASM")):
        if path and pathlib.Path(path).parent == out:
            sw.CloseDoc(title)


if __name__ == "__main__":
    main()
