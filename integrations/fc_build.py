"""Build a model as a parametric FreeCAD document and check it against the cadgen STEP.

    .venv\\Scripts\\python integrations\\fc_build.py MODEL [--no-verify]

Evaluates models/src/<MODEL>.py parts() here (FreeCAD's Python has no cadgen), writes the recipes
as JSON, runs integrations/freecad/fc_builder.py in freecadcmd, and saves
models/FreeCAD/<MODEL>.FCStd. Then each part is compared with the cadgen part like sw_verify.py
(volume, fuzzy-boolean overlap). FreeCAD 1.x; set FREECADCMD if it is not in the default place.
"""
import argparse
import importlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "models" / "src"))
FREECADCMD = os.environ.get("FREECADCMD", str(pathlib.Path(os.environ["LOCALAPPDATA"]) / "Programs/FreeCAD 1.1/bin/freecadcmd.exe"))


def recipes(model):
    from lib.shapes import blade_section
    parts = []
    for label, color, ops in importlib.import_module(model).parts():
        out = []
        for op in ops:
            if op[0] == "loft":  # hand FreeCAD the exact section points cadgen lofts through
                kind, name, x, sections, n = op
                op = (kind, name, x, [(s[0], blade_section(x, *s)) for s in sections], n)
            out.append(op)
        parts.append((label, color, out))
    return {"model": model, "parts": parts}


def verify(model, steps):
    from cadgen import build123d as bd
    from cadgen import read_step
    from sw_verify import compare
    ref = {c.label: c for c in read_step(str(ROOT / "models" / "STEP" / f"{model}.step")).leaves}
    lofted = {n for n, _, ops in importlib.import_module(model).parts() if any(o[0] in ("loft", "duct") for o in ops)}
    ok = True
    for f in sorted(steps.glob("*.step")):
        good, v_fc, v_cad, note = compare(bd.import_step(str(f)), ref[f.stem], f.stem in lofted)
        ok &= good
        print(f"{'OK ' if good else 'BAD'} {f.stem:24s} FreeCAD {v_fc / 1e6:9.4f} L  cadgen {v_cad / 1e6:9.4f} L  {note}", flush=True)
    print("ALL OK" if ok else "PROBLEMS FOUND")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model")
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()
    out = ROOT / "models" / "FreeCAD" / f"{args.model}.FCStd"
    out.parent.mkdir(parents=True, exist_ok=True)
    work = pathlib.Path(tempfile.mkdtemp(prefix=f"fc_{args.model}_"))
    (work / "steps").mkdir()
    (work / "recipe.json").write_text(json.dumps(recipes(args.model)), encoding="utf-8")
    env = dict(os.environ, FC_JSON=str(work / "recipe.json"), FC_OUT=str(out), FC_STEPS=str(work / "steps"))
    run = subprocess.run([FREECADCMD, str(ROOT / "integrations" / "freecad" / "fc_builder.py")],
                         env=env, capture_output=True, text=True)
    log = run.stdout + run.stderr
    for line in log.splitlines():
        if line.startswith(("FC_", "Traceback")) or "Error" in line:
            print(line)
    if "FC_SAVED" not in log:
        raise SystemExit(f"FreeCAD build failed:\n{log[-3000:]}")
    if not args.no_verify:
        sys.path.insert(0, str(ROOT / "integrations"))
        sys.exit(0 if verify(args.model, work / "steps") else 1)


if __name__ == "__main__":
    main()
