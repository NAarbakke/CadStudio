r"""LaTeX report: what the fidelity upgrade added to the models, measured against the previous commit.

    .venv\Scripts\python reports\latex\model_fidelity.py

Counts parts, sub-assemblies, fasteners, rounded profiles and finishes from each model's parts()
recipes, measures the saved STEP and GLB, and compares them with the same model built from BASELINE
(the commit before the upgrade), which is checked out and built once under tmp/latex/model_fidelity/.
Renders, the corner figure and the check results come from the saved exports, so build the models
first. --tex-only skips the LaTeX compile; --no-render leaves out the CAD images.
"""
from __future__ import annotations

import argparse
from datetime import date
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "models"))
from latex_report import GREY, INK, TEXT_WIDTH_IN, build, plot_style, save_figure
from model_check import check

BASELINE = "173555b"   # the commit before the upgrade
PILOT = "rocketdyne_f1"
TITLES = {"rocketdyne_f1": "Rocketdyne F-1", "naca_lewis_16in_ramjet": "NACA Lewis 16-inch ramjet",
          "lyulka_nuclear_turbojet": "Lyulka nuclear turbojet", "oreshnik": "Oreshnik", "tsirkon": "Tsirkon",
          "ge_e3_turbofan": "GE E3 turbofan", "nasa_lewis_small_turbojet": "NASA Lewis small turbojet"}
WORK = ROOT / "tmp" / "latex" / "model_fidelity"
OLD = WORK / "baseline" / "models"
RENDER = '{"mode":"render","floor":{"placement":"lowest"}}'
VIEW = "215:25"
DETAIL = '{"position":[-2600,3000,2900],"target":[450,600,0],"up":[0,1,0]}'   # F-1 powerhead, mm


def run(args, cwd=ROOT):
    result = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                            errors="replace")
    if result.returncode:
        raise RuntimeError(f"{' '.join(str(a) for a in args[:6])} failed:\n{(result.stderr or result.stdout)[-1500:]}")
    return result.stdout


def load(source, name):
    """Import a model source file under its own module name (the baseline and current sources share stems)."""
    for cached in [m for m in sys.modules if m == "lib" or m.startswith("lib.")]:
        del sys.modules[cached]   # each tree brings its own lib/
    sys.path.insert(0, str(source.parent))
    try:
        spec = importlib.util.spec_from_file_location(name, source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(source.parent))


def source_stats(module):
    """What the recipes declare: parts, operations, fasteners, rounded profiles, finishes, sub-assemblies."""
    parts = module.parts()
    ops = [op for _, _, part_ops in parts for op in part_ops]
    return {
        "parts": len(parts), "operations": len(ops),
        "fasteners": sum(op[7] for op in ops if op[0] == "hex_circle"),
        "rounded": sum(op[0] == "lathe" for op in ops),
        "finishes": len(getattr(module, "MATERIALS", {}).get("definitions", {})),
        "groups": len(getattr(module, "GROUPS", {})),
    }


def cached(path, newer_than, make):
    """JSON at `path`, recomputed by make() when it is missing or older than the file it describes."""
    if path.is_file() and path.stat().st_mtime >= newer_than.stat().st_mtime:
        return json.loads(path.read_text(encoding="utf-8"))
    value = make()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1), encoding="utf-8")
    return value


def faces(step):
    from cadgen import read_step
    return sum(len(c.faces()) for c in read_step(str(step)).leaves)


def baseline(model):
    """Source statistics and export sizes of the model as it was at BASELINE, building it once if needed."""
    step, glb = OLD / "STEP" / f"{model}.step", OLD / "GLB" / f"{model}.glb"
    source = OLD / "src" / f"{model}.py"
    if not source.is_file():
        OLD.parent.mkdir(parents=True, exist_ok=True)
        archive = subprocess.run(["git", "archive", BASELINE, "models/src"], cwd=ROOT, capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", str(OLD.parent)], input=archive.stdout, check=True)
    if not step.is_file():
        print(f"Building {model} at {BASELINE} for comparison", flush=True)
        run([sys.executable, "-c", f"import sys; sys.path.insert(0, '.'); import {model} as m; m.{model}()"], cwd=source.parent)

    def measure():
        return {**source_stats(load(source, f"baseline_{model}")), "faces": faces(step),
                "step_mb": step.stat().st_size / 1e6, "glb_mb": glb.stat().st_size / 1e6 if glb.is_file() else None}
    return cached(WORK / "baseline" / f"{model}.json", step, measure)


def current(model):
    source = ROOT / "models" / model / "src" / f"{model}.py"
    step, glb = (ROOT / "models" / model / kind / f"{model}.{kind.lower()}" for kind in ("STEP", "GLB"))
    module = load(source, f"current_{model}")
    if not step.is_file():
        raise FileNotFoundError(f"{step} is missing; run models/{model}/src/{model}.py first")
    result = cached(ROOT / "tmp" / "check" / f"{model}_check.json", step, lambda: check(step))
    log = ROOT / "tmp" / "check" / f"{model}_freecad.log"
    freecad = None
    if log.is_file() and log.stat().st_mtime >= step.stat().st_mtime:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
        freecad = {"ok": sum(line.startswith("OK ") for line in lines), "bad": sum(line.startswith("BAD") for line in lines)}
    return module, {**source_stats(module), "faces": result["faces"], "step_mb": step.stat().st_size / 1e6,
                    "glb_mb": glb.stat().st_size / 1e6, "check": result, "freecad": freecad,
                    "upgraded": hasattr(module, "MATERIALS")}


def snapshot(step, target, camera, display="solid", size=(2400, 1500)):
    """Render a saved STEP unless the image is already newer than it."""
    if not target.is_file() or target.stat().st_mtime < step.stat().st_mtime:
        run([sys.executable, "-m", "cadgen.cli", "step", "snapshot", step, target, "--camera", camera,
             "--display", display, "--width", size[0], "--height", size[1]], cwd=step.parent)
    return target.name


def figure_corners(module, path):
    """A real profile from the pilot model, as drawn in the recipe and as lathe() rounds it."""
    from lib.shapes import round_profile
    name, points, radius = next((op[1], op[2], op[3]) for _, _, ops in module.parts() for op in ops
                                if op[0] == "lathe" and op[1] == "BearingHousing")
    fig, axes = plt.subplots(1, 2, figsize=(TEXT_WIDTH_IN, 2.5), sharex=True, sharey=True)
    closed = points + [points[0]]
    axes[0].plot([p[0] for p in closed], [p[1] for p in closed], "-")
    axes[0].plot([p[0] for p in points], [p[1] for p in points], "o", markerfacecolor="white", markersize=3.5)
    xs, ys = [], []
    for seg in round_profile(points, radius):
        if seg[0] == "line":
            xs += [seg[1][0], seg[2][0]]
            ys += [seg[1][1], seg[2][1]]
        else:   # three-point arc: draw the circle through the points
            (x1, y1), (x2, y2), (x3, y3) = seg[1:]
            d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
            cx = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) + (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
            cy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) + (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
            import numpy as np
            a1, a2, a3 = (np.arctan2(y - cy, x - cx) for x, y in seg[1:])
            a2, a3 = (a1 + (a - a1 + np.pi) % (2 * np.pi) - np.pi for a in (a2, a3))
            r = np.hypot(x1 - cx, y1 - cy)
            for a in np.linspace(a1, a3, 12):
                xs.append(cx + r * np.cos(a))
                ys.append(cy + r * np.sin(a))
    axes[1].plot(xs, ys, "-")
    for axis, title in zip(axes, ("recipe polygon", f"lathe, radius {radius:.1f} mm")):
        axis.set_aspect("equal")
        axis.set_xlabel("$a$, mm")
        axis.set_title(title, fontsize=10, color=GREY)
        axis.axhline(0, color=INK, linewidth=0.5, linestyle="-.")
    axes[0].set_ylabel("$r$, mm")
    return name, radius, save_figure(fig, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tex-only", action="store_true", help="Write the .tex and figures without compiling")
    parser.add_argument("--no-render", action="store_true", help="Leave out the CAD images")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    plot_style()

    rows, modules = [], {}
    for model, title in TITLES.items():
        before = baseline(model)
        modules[model], after = current(model)
        rows.append({"model": model, "title": title, "before": before, "after": after})
    pilot = next(row for row in rows if row["model"] == PILOT)
    module = modules[PILOT]

    from lib.materials import FINISHES
    used = {}
    for _, label, finish, ops in module.SPEC:
        used.setdefault(finish, []).append(label)
    finishes = [{"id": key, **FINISHES[key], "hex": FINISHES[key]["baseColor"][1:], "parts": len(labels)}
                for key, labels in sorted(used.items(), key=lambda item: -len(item[1]))]
    by_label = {label: (finish, ops) for _, label, finish, ops in module.SPEC}
    groups = [{"name": group, "parts": len(labels),
               "fasteners": sum(op[7] for label in labels for op in by_label[label][1] if op[0] == "hex_circle"),
               "rounded": sum(op[0] == "lathe" for label in labels for op in by_label[label][1]),
               "finishes": len({by_label[label][0] for label in labels})}
              for group, labels in module.GROUPS.items()]
    loose = [label for group, label, _, _ in module.SPEC if group is None]

    profile_name, profile_radius, _ = figure_corners(module, WORK / "corners.pdf")
    images = None
    if not args.no_render:
        step, old_step = ROOT / "models" / PILOT / "STEP" / f"{PILOT}.step", OLD / "STEP" / f"{PILOT}.step"
        images = {"before": snapshot(old_step, WORK / "before_solid.png", VIEW),
                  "after": snapshot(step, WORK / "after_solid.png", VIEW),
                  "render": snapshot(step, WORK / "after_render.png", VIEW, RENDER),
                  "detail": snapshot(step, WORK / "after_detail.png", DETAIL, RENDER)}
        gallery = []
        for row in rows:
            if row["after"]["upgraded"] and row["model"] != PILOT:
                gallery.append({"title": row["title"], "image": snapshot(
                    ROOT / "models" / row["model"] / "STEP" / f"{row['model']}.step", WORK / f"{row['model']}_render.png", VIEW, RENDER,
                    (2400, 1100))})
        images["gallery"] = gallery

    from cadgen import read_step
    leaves = list(read_step(str(ROOT / "models" / PILOT / "STEP" / f"{PILOT}.step")).leaves)
    fastener_faces = sum(len(c.faces()) for c in leaves if by_label[c.label][0] == "fastener")

    mesh = re.search(r"mesh_tolerance=([\d.e-]+), mesh_angular_tolerance=([\d.]+)",
                     (ROOT / "models" / PILOT / "src" / f"{PILOT}.py").read_text(encoding="utf-8"))
    context = {
        "title": "Model fidelity upgrade", "subtitle": "Finishes, rounded edges, fasteners and sub-assemblies",
        "document_id": "CS-TR-002", "revision": "A", "date": f"{date.today().day} {date.today():%B %Y}",
        "baseline": BASELINE, "rows": rows, "pilot": pilot, "pilot_title": TITLES[PILOT],
        "upgraded": [row for row in rows if row["after"]["upgraded"]],
        "pending": [row for row in rows if not row["after"]["upgraded"]],
        "finishes": finishes, "groups": groups, "loose": loose, "images": images,
        "profile_name": profile_name, "profile_radius": profile_radius,
        "tints": [FINISHES[key]["name"].split(", ")[1] for key in module.TINT],
        "tint_from": module.JACKET_CONE * module.IN, "tint_to": module.TINT_END * module.IN,
        "mesh_tolerance": float(mesh.group(1)), "mesh_angle": float(mesh.group(2)),
        "face_ratio": pilot["after"]["faces"] / pilot["before"]["faces"],
        "step_ratio": pilot["after"]["step_mb"] / pilot["before"]["step_mb"],
        "fastener_face_share": fastener_faces / pilot["after"]["faces"],
    }
    output = args.output.resolve() if args.output else ROOT / "output" / "pdf" / "model_fidelity.pdf"
    build("model_fidelity.tex", context, output, WORK, compile_pdf=not args.tex_only)


if __name__ == "__main__":
    main()
