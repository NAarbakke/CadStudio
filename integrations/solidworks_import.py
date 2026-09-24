"""Import STEP files into a running SolidWorks session and save them as native files.

    .venv\\Scripts\\python integrations\\solidworks_import.py models\\STEP\\turbofan.step [more.step ...]

A STEP assembly becomes an .SLDASM plus one .SLDPRT per part; a single body becomes an .SLDPRT.
Outputs go to models/SolidWorks/<name>/ unless --out is given. Windows + SolidWorks only (COM API).
"""
import argparse
import pathlib
import re

import pythoncom
import win32com.client

SW_DOC_ASSEMBLY = 2                        # swDocumentTypes_e
SW_SAVE_SILENT = 1                         # swSaveAsOptions_e


def import_step(sw, step, out_dir):
    step, out_dir = step.resolve(), out_dir.resolve()  # SolidWorks resolves relative paths against its own cwd
    errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    model = sw.LoadFile4(str(step), "r", sw.GetImportFileData(str(step)), errors)
    if model is None:
        raise SystemExit(f"{step.name}: SolidWorks could not import it (swFileLoadError {errors.value})")
    out_dir.mkdir(parents=True, exist_ok=True)
    if model.GetType != SW_DOC_ASSEMBLY:  # late-bound COM: no-arg getters are properties
        return _save(model, out_dir, step)

    # 3D Interconnect loads a STEP assembly as an unsaved wrapper around a linked
    # "<name>.step" sub-assembly whose parts live in a temp folder. Save parts first,
    # then assemblies, so every saved reference points into out_dir; drop the wrapper.
    docs = {}
    for comp in model.GetComponents(False) or []:
        doc = comp.GetModelDoc2
        if doc is not None:
            docs.setdefault(doc.GetPathName, doc)
    parts = [d for d in docs.values() if d.GetType != SW_DOC_ASSEMBLY]
    assemblies = [d for d in docs.values() if d.GetType == SW_DOC_ASSEMBLY]
    for doc in parts + assemblies:
        target = _save(doc, out_dir, step)
    if not assemblies:  # plain (non-Interconnect) import: the loaded model is the assembly
        return _save(model, out_dir, step, name=step.stem)
    sw.CloseDoc(model.GetTitle)
    return target


def _save(doc, out_dir, step, name=None):
    # "inlet_2.step.SLDPRT" -> "inlet": strip SolidWorks' repeat-import suffix and extensions.
    name = name or re.sub(r"(_\d+)?\.step.*$", "", doc.GetTitle, flags=re.IGNORECASE)
    target = out_dir / (name + (".SLDASM" if doc.GetType == SW_DOC_ASSEMBLY else ".SLDPRT"))
    status = doc.SaveAs3(str(target), 0, SW_SAVE_SILENT)
    if status != 0:
        raise SystemExit(f"{step.name}: saving {target.name} failed (swFileSaveError {status})")
    return target


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("steps", nargs="+", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, help="output folder (default models/SolidWorks/<name>)")
    ap.add_argument("--close", action="store_true", help="close each document after saving")
    args = ap.parse_args()

    try:
        sw = win32com.client.GetActiveObject("SldWorks.Application")
    except pythoncom.com_error:
        try:
            sw = win32com.client.Dispatch("SldWorks.Application")
        except pythoncom.com_error:
            # 3DEXPERIENCE SOLIDWORKS must be started through its launcher/login, which COM cannot do.
            raise SystemExit("Could not start SolidWorks. Open SolidWorks (and log in) first, then rerun.")
    sw.Visible = True
    for step in args.steps:
        target = import_step(sw, step, args.out or pathlib.Path("models/SolidWorks") / step.stem)
        print("saved", target)
        if args.close:
            sw.CloseDoc(target.name)


if __name__ == "__main__":
    main()
