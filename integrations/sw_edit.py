"""Inspect and edit SolidWorks files programmatically: dimensions, global variables, feature suppression.

    sw_edit.py list  FILE [--filter TEXT]
    sw_edit.py set   FILE NAME=VALUE [NAME=VALUE ...] [--save-as PATH]
    sw_edit.py suppress|unsuppress FILE FEATURE [FEATURE ...] [--save-as PATH]

NAME is a global variable (e.g. SpikeStruts_count) or a dimension "<dim>@<feature/sketch>"
(e.g. r1@CowlProfile, D1@SpikeStrutsBlade). Lengths are mm, angles degrees, counts integers.
Works on any .SLDPRT/.SLDASM (including files not made by CadStudio); the file is rebuilt, checked
for rebuild errors and saved in place unless --save-as is given. SolidWorks must be open.
"""
import argparse
import math
import pathlib
import re

from sw_api import connect, dimensions, features, open_doc, open_docs, save_as

ANGULAR, INTEGER = 1, 2  # IDimension.GetType() on SW 2026: 0 = length, 1 = angle, 2 = integer (pattern count)
ALL_CONFIGS = 2                      # swSetValueInConfiguration_e.swSetValue_InAllConfigurations


def to_user(dim):
    kind, v = dim.GetType(), dim.SystemValue
    return (math.degrees(v), "deg") if kind == ANGULAR else (v, "") if kind == INTEGER else (v * 1000, "mm")


def to_system(dim, value):
    kind = dim.GetType()
    return math.radians(value) if kind == ANGULAR else value if kind == INTEGER else value / 1000


def get_doc(sw, path):
    path = pathlib.Path(path).resolve()
    for doc, _, p in open_docs(sw):
        if p and pathlib.Path(p).resolve() == path:
            return doc
    return open_doc(sw, path)


def global_vars(doc):
    """{name: (index, equation)} for equations of the form "name" = value."""
    mgr = doc.GetEquationMgr()
    out = {}
    for i in range(mgr.GetCount()):
        eq = mgr.Equation(i)
        m = re.match(r'\s*"([^"@]+)"\s*=', eq)
        if m and mgr.GlobalVariable(i):
            out[m.group(1)] = (i, eq)
    return out


def cmd_list(doc, filt):
    mgr = doc.GetEquationMgr()
    print("Global variables / equations:")
    for i in range(mgr.GetCount()):
        print(f"  {mgr.Equation(i):45s} = {mgr.Value(i):g}")
    print("Dimensions:")
    seen = set()
    for feat, dim in dimensions(doc):
        name = "@".join(dim.FullName.split("@")[:2])
        if name in seen or (filt and filt.lower() not in name.lower()):
            continue
        seen.add(name)
        value, unit = to_user(dim)
        print(f"  {name:40s} {value:12.4f} {unit}")
    print("Features:")
    for f in features(doc):
        if f.GetTypeName2() not in ("OriginProfileFeature", "MaterialFolder", "HistoryFolder", "SensorFolder",
                                    "DocsFolder", "DetailCabinet", "EqnFolder", "CommentsFolder", "FavoriteFolder",
                                    "SelectionSetFolder", "EnvFolder", "InkMarkupFolder", "LiveSectionFolder"):
            state = " (suppressed)" if f.IsSuppressed() else ""
            print(f"  {f.Name:40s} {f.GetTypeName2()}{state}")


def cmd_set(doc, assignments):
    gvars = global_vars(doc)
    mgr = doc.GetEquationMgr()
    for item in assignments:
        name, _, raw = item.partition("=")
        name, value = name.strip(), float(raw)
        if name in gvars:
            mgr.SetEquation(gvars[name][0], f'"{name}" = {value:g}')
            print(f"  global {name} = {value:g}")
            continue
        dim = doc.Parameter(name)
        if dim is None:
            raise SystemExit(f"no global variable or dimension named {name!r} (see: sw_edit.py list FILE)")
        from sw_api import typed
        dim = typed(dim, "IDimension")
        old, unit = to_user(dim)
        status = dim.SetSystemValue3(to_system(dim, value), ALL_CONFIGS, None)
        if status != 0:  # swSetValueReturnStatus_e: 0 = OK
            raise SystemExit(f"could not set {name} (status {status}); driven or linked by an equation?")
        print(f"  {name}: {old:g} -> {value:g} {unit}")
    mgr.EvaluateAll()


def cmd_suppress(doc, names, suppress):
    wanted = set(names)
    for f in features(doc):
        if f.Name in wanted:
            f.SetSuppression2(0 if suppress else 2, 2, None)  # swFeatureSuppressionAction_e; 2 = all configurations
            wanted.discard(f.Name)
            print(f"  {'suppressed' if suppress else 'unsuppressed'} {f.Name}")
    if wanted:
        raise SystemExit(f"features not found: {sorted(wanted)}")


def rebuild_and_save(doc, path, save_as_path):
    doc.ForceRebuild3(False)
    broken = [f.Name for f in features(doc) if f.GetErrorCode2()[0] not in (0,)]
    if broken:
        raise SystemExit(f"rebuild errors in {broken}; not saved (fix or undo in SolidWorks)")
    target = pathlib.Path(save_as_path or path).resolve()
    save_as(doc, target)
    print("saved", target)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("file"); p.add_argument("--filter")
    p = sub.add_parser("set"); p.add_argument("file"); p.add_argument("assign", nargs="+"); p.add_argument("--save-as")
    for name in ("suppress", "unsuppress"):
        p = sub.add_parser(name); p.add_argument("file"); p.add_argument("features", nargs="+"); p.add_argument("--save-as")
    args = ap.parse_args()

    sw = connect()
    doc = get_doc(sw, args.file)
    if args.cmd == "list":
        return cmd_list(doc, args.filter)
    if args.cmd == "set":
        cmd_set(doc, args.assign)
    else:
        cmd_suppress(doc, args.features, args.cmd == "suppress")
    rebuild_and_save(doc, args.file, args.save_as)


if __name__ == "__main__":
    main()
