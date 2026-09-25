"""Import STEP files into a running SolidWorks session and save them as native files.

    .venv\\Scripts\\python integrations\\solidworks_import.py models\\STEP\\turbofan.step [more.step ...]

A STEP assembly becomes an .SLDASM plus one .SLDPRT per part; a single body becomes an .SLDPRT.
These are plain imported solids (no feature tree); for parametric parts see sw_build_ramjet.py.
Outputs go to models/SolidWorks/<name>/ unless --out is given. Windows + SolidWorks only (COM API).
"""
import argparse
import pathlib
import re

from sw_api import DOC_ASSEMBLY, connect, save_as, typed


def import_step(sw, step, out_dir):
    step, out_dir = step.resolve(), out_dir.resolve()  # SolidWorks resolves relative paths against its own cwd
    model, errors = sw.LoadFile4(str(step), "r", sw.GetImportFileData(str(step)), 0)
    if model is None:
        raise SystemExit(f"{step.name}: SolidWorks could not import it (swFileLoadError {errors})")
    model = typed(model, "IModelDoc2")
    out_dir.mkdir(parents=True, exist_ok=True)
    if model.GetType() != DOC_ASSEMBLY:
        return _save(model, out_dir, step)

    # 3D Interconnect loads a STEP assembly as an unsaved wrapper around a linked
    # "<name>.step" sub-assembly whose parts live in a temp folder. Save parts first,
    # then assemblies, so every saved reference points into out_dir; drop the wrapper.
    docs = {}
    for comp in typed(model, "IAssemblyDoc").GetComponents(False) or []:
        doc = typed(typed(comp, "IComponent2").GetModelDoc2(), "IModelDoc2")
        if doc is not None:
            docs.setdefault(doc.GetPathName(), doc)
    parts = [d for d in docs.values() if d.GetType() != DOC_ASSEMBLY]
    assemblies = [d for d in docs.values() if d.GetType() == DOC_ASSEMBLY]
    for doc in parts + assemblies:
        target = _save(doc, out_dir, step)
    if not assemblies:  # plain (non-Interconnect) import: the loaded model is the assembly
        return _save(model, out_dir, step, name=step.stem)
    sw.CloseDoc(model.GetTitle())
    return target


def _save(doc, out_dir, step, name=None):
    # "inlet_2.step.SLDPRT" -> "inlet": strip SolidWorks' repeat-import suffix and extensions.
    name = name or re.sub(r"(_\d+)?\.step.*$", "", doc.GetTitle(), flags=re.IGNORECASE)
    target = out_dir / (name + (".SLDASM" if doc.GetType() == DOC_ASSEMBLY else ".SLDPRT"))
    save_as(doc, target)
    return target


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("steps", nargs="+", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, help="output folder (default models/SolidWorks/<name>)")
    ap.add_argument("--close", action="store_true", help="close each document after saving")
    args = ap.parse_args()

    sw = connect()
    for step in args.steps:
        target = import_step(sw, step, args.out or pathlib.Path("models/SolidWorks") / step.stem)
        print("saved", target)
        if args.close:
            sw.CloseDoc(target.name)


if __name__ == "__main__":
    main()
