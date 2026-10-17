"""Check saved decorative STEP/STL files, not weapon fidelity or performance."""
from __future__ import annotations

import json
import math
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "delta_display": (120.0, 68.0, 18.0),
    "dart_display": (136.0, 60.0, 22.0),
}
TOLERANCE_MM = 0.01


def inspect_binary_stl(path: Path):
    """Check triangle connectivity, orientation, volume and bounds without extra packages."""
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert count > 0 and len(data) == 84 + count * 50, "invalid binary STL size"
    vertices = []
    ids = {}
    edges = defaultdict(list)
    volume = 0.0
    for face_id in range(count):
        record = struct.unpack_from("<12fH", data, 84 + face_id * 50)
        points = [tuple(record[offset:offset + 3]) for offset in (3, 6, 9)]
        triangle = []
        for point in points:
            key = tuple(round(value, 5) for value in point)
            if key not in ids:
                ids[key] = len(vertices)
                vertices.append(point)
            triangle.append(ids[key])
        assert len(set(triangle)) == 3, "degenerate STL triangle"
        a, b, c = points
        cross = (b[1]*c[2]-b[2]*c[1], b[2]*c[0]-b[0]*c[2], b[0]*c[1]-b[1]*c[0])
        volume += sum(a[axis] * cross[axis] for axis in range(3)) / 6.0
        for start, end in zip(triangle, triangle[1:] + triangle[:1]):
            edges[tuple(sorted((start, end)))].append((face_id, 1 if start < end else -1))
    bad_edges = [(edge, adjacent) for edge, adjacent in edges.items() if len(adjacent) != 2]
    if bad_edges:
        print(json.dumps({"file": path.name, "unmatched_edge_count": len(bad_edges),
                          "sample": [{"points": [vertices[index] for index in edge], "uses": len(adjacent)}
                                     for edge, adjacent in bad_edges[:10]]}, indent=2), flush=True)
    assert not bad_edges, "STL has open or nonmanifold edges"
    assert all(sum(sign for _, sign in adjacent) == 0 for adjacent in edges.values()), "STL winding inconsistent"
    neighbours = defaultdict(set)
    for adjacent in edges.values():
        a, b = adjacent[0][0], adjacent[1][0]
        neighbours[a].add(b)
        neighbours[b].add(a)
    reached, pending = set(), [0]
    while pending:
        current = pending.pop()
        if current not in reached:
            reached.add(current)
            pending.extend(neighbours[current] - reached)
    assert len(reached) == count, "STL contains disconnected shells"
    assert math.isfinite(volume) and volume > 0, "STL non-positive volume"
    extents = tuple(max(p[axis] for p in vertices) - min(p[axis] for p in vertices) for axis in range(3))
    return extents, volume, count


def main():
    if "--finish-meshes" in sys.argv:
        sys.path.insert(0, str(ROOT / "src"))
        from lib.mesh_finish import finish_print_meshes
        finish_print_meshes(ROOT)
    if "--mesh-only" in sys.argv:
        for name in EXPECTED:
            print(name, inspect_binary_stl(ROOT / "STL" / f"{name}.stl"), flush=True)
        return
    from cadgen import read_step

    results = {}
    for name, expected in EXPECTED.items():
        print(f"Checking {name}...", flush=True)
        step_path = ROOT / "STEP" / f"{name}.step"
        shape = read_step(step_path)
        solids = shape.solids()
        bounds = shape.bounding_box()
        size = tuple(bounds.size)
        assert len(solids) == 1, (name, "expected one solid", len(solids))
        assert shape.is_valid, (name, "invalid STEP geometry")
        assert solids[0].volume > 0, (name, "non-positive volume")
        assert abs(bounds.min.Z) <= TOLERANCE_MM, (name, "bottom not at Z=0")
        assert all(abs(a-b) <= TOLERANCE_MM for a, b in zip(size, expected)), (name, size)
        extents, mesh_volume, triangles = inspect_binary_stl(ROOT / "STL" / f"{name}.stl")
        assert all(abs(a-b) <= TOLERANCE_MM for a, b in zip(extents, expected)), (name, extents)
        assert abs(mesh_volume - solids[0].volume) / solids[0].volume < 0.001, (name, "mesh volume differs from solid")
        results[name] = {
            "size_mm": [round(value, 4) for value in size],
            "step_valid": True,
            "solid_count": len(solids),
            "volume_mm3": round(solids[0].volume, 3),
            "stl_watertight": True,
            "stl_winding_consistent": True,
            "stl_component_count": 1,
            "stl_triangles": triangles,
            "stl_volume_mm3": round(mesh_volume, 3),
            "bottom_z_mm": round(bounds.min.Z, 4),
        }
    pair = read_step(ROOT / "STEP" / "display_pair.step")
    assert pair.is_valid and len(pair.solids()) == 2, "pair must contain two valid solids"
    results["display_pair"] = {"step_valid": True, "solid_count": 2}
    for name in (*EXPECTED, "display_pair"):
        data = (ROOT / "GLB" / f"{name}.glb").read_bytes()
        magic, version, length = struct.unpack_from("<4sII", data)
        assert magic == b"glTF" and version == 2 and length == len(data), (name, "invalid GLB container")
        results[name]["glb_container_valid"] = True
    report = {"tolerance_mm": TOLERANCE_MM, "scope": "decorative geometry only", "models": results}
    (ROOT / "profile").mkdir(exist_ok=True)
    (ROOT / "profile" / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
