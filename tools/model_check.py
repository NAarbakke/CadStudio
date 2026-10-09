r"""Check a saved STEP assembly: every part a valid solid, and no two parts intersect.

    .venv\Scripts\python tools\model_check.py models\STEP\rocketdyne_f1.step

Prints each failure and exits nonzero if there is one. Parts that only touch (a flange on a face,
a nut on a flange) pass: a pair fails when the common volume exceeds --tolerance mm3. The result is
also written to tmp/check/<model>_check.json, which reports/latex/model_fidelity.py reads.
"""
import argparse
import itertools
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integrations"))


def boxes_overlap(a, b, gap=1e-6):
    return all(getattr(a.min, k) < getattr(b.max, k) - gap and getattr(b.min, k) < getattr(a.max, k) - gap for k in "XYZ")


def check(step, tolerance=1.0):
    """{"parts", "faces", "volume_l", "envelope_mm", "invalid", "pairs_tested", "intersecting"} for a STEP file."""
    from cadgen import read_step
    from compare import common_volume, volume
    leaves = list(read_step(str(step)).leaves)
    volumes = {c.label: volume(c) for c in leaves}
    boxes = {c.label: c.bounding_box() for c in leaves}
    close = [(a, b) for a, b in itertools.combinations(leaves, 2) if boxes_overlap(boxes[a.label], boxes[b.label])]
    hits = [(a.label, b.label, round(v, 1)) for a, b in close if (v := common_volume(a, b, fuzz=1e-4)) > tolerance]
    return {
        "step": str(pathlib.Path(step).resolve().relative_to(ROOT).as_posix()), "parts": len(leaves),
        "faces": sum(len(c.faces()) for c in leaves), "volume_l": sum(volumes.values()) / 1e6,
        "envelope_mm": [[round(min(getattr(b.min, k) for b in boxes.values()), 2) for k in "XYZ"],
                        [round(max(getattr(b.max, k) for b in boxes.values()), 2) for k in "XYZ"]],
        "invalid": [c.label for c in leaves if not c.is_valid or volumes[c.label] <= 0],
        "pairs_tested": len(close), "intersecting": hits, "tolerance_mm3": tolerance,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", type=pathlib.Path)
    parser.add_argument("--tolerance", type=float, default=1.0, help="Common volume in mm3 above which a pair fails")
    args = parser.parse_args()
    result = check(args.step, args.tolerance)
    out = ROOT / "tmp" / "check" / f"{args.step.stem}_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    low, high = result["envelope_mm"]
    print(f"{result['parts']} parts, {result['faces']} faces, {result['volume_l']:.1f} L, "
          f"envelope {low} to {high} mm, {result['pairs_tested']} neighbouring pairs tested")
    for label in result["invalid"]:
        print(f"INVALID   {label}")
    for a, b, v in result["intersecting"]:
        print(f"INTERSECT {a} / {b}: {v} mm3")
    ok = not result["invalid"] and not result["intersecting"]
    print("ALL OK" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
