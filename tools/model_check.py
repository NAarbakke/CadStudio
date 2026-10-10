r"""Check a saved STEP assembly: every part a valid solid, and no two parts intersect.

    .venv\Scripts\python tools\model_check.py models\rocketdyne_f1\STEP\rocketdyne_f1.step

Prints each failure and exits nonzero if there is one. Parts that only touch (a flange on a face,
a nut on a flange) pass: a pair fails when the common volume exceeds --tolerance mm3. The boolean
can report a false overlap against a part with hundreds of fused spline blades (the turbojet rotor), so a
hit is confirmed geometrically: it is cleared when no face of one part comes near a face of the other
(their bounding boxes stay apart) and neither part contains a vertex of the other. The result is
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


RAYS = [(0.267, 0.535, 0.802), (-0.631, 0.742, 0.226), (0.811, -0.324, 0.487), (-0.172, -0.413, 0.894), (0.557, 0.371, -0.743)]


def holds(shape, vertex):
    """Is the vertex inside the shape? Majority of the ray-crossing parities in five directions."""
    from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
    caster, votes = IntCurvesFace_ShapeIntersector(), 0
    caster.Load(shape.wrapped, 1e-6)
    for direction in RAYS:
        caster.Perform(gp_Lin(gp_Pnt(vertex.X, vertex.Y, vertex.Z), gp_Dir(*direction)), 0.0, 1e9)
        votes += caster.NbPnt() % 2
    return votes > len(RAYS) / 2


def separate(a, b):
    """True when the two parts cannot share volume: no faces near each other and neither inside the other."""
    near = [f.bounding_box() for f in b.faces()]
    if any(boxes_overlap(box, other, gap=-0.01) for box in (f.bounding_box() for f in a.faces()) for other in near):
        return False
    return not any(holds(b, s.vertices()[0]) for s in a.solids()) and not any(holds(a, s.vertices()[0]) for s in b.solids())


def check(step, tolerance=1.0):
    """{"parts", "faces", "volume_l", "envelope_mm", "invalid", "pairs_tested", "intersecting", "cleared"} for a STEP file."""
    from cadgen import read_step
    from compare import common_volume, volume
    leaves = list(read_step(str(step)).leaves)
    volumes = {c.label: volume(c) for c in leaves}
    boxes = {c.label: c.bounding_box() for c in leaves}
    close = [(a, b) for a, b in itertools.combinations(leaves, 2) if boxes_overlap(boxes[a.label], boxes[b.label])]
    found = [(a, b, round(v, 1)) for a, b in close if (v := common_volume(a, b, fuzz=1e-4)) > tolerance]
    cleared = [(a.label, b.label, v) for a, b, v in found if separate(a, b)]
    hits = [(a.label, b.label, v) for a, b, v in found if (a.label, b.label, v) not in cleared]
    return {
        "step": str(pathlib.Path(step).resolve().relative_to(ROOT).as_posix()), "parts": len(leaves),
        "faces": sum(len(c.faces()) for c in leaves), "volume_l": sum(volumes.values()) / 1e6,
        "envelope_mm": [[round(min(getattr(b.min, k) for b in boxes.values()), 2) for k in "XYZ"],
                        [round(max(getattr(b.max, k) for b in boxes.values()), 2) for k in "XYZ"]],
        "invalid": [c.label for c in leaves if not c.is_valid or volumes[c.label] <= 0],
        "pairs_tested": len(close), "intersecting": hits, "cleared": cleared, "tolerance_mm3": tolerance,
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
    for a, b, v in result["cleared"]:
        print(f"CLEARED   {a} / {b}: the boolean reported {v} mm3, but no faces come near and neither contains the other")
    for a, b, v in result["intersecting"]:
        print(f"INTERSECT {a} / {b}: {v} mm3")
    ok = not result["invalid"] and not result["intersecting"]
    print("ALL OK" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
