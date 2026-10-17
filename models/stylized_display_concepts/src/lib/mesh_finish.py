"""Close sub-0.005 mm tessellation seams in the decorative binary STL exports."""
from __future__ import annotations

import json
import math
import struct
from collections import defaultdict
from itertools import product
from pathlib import Path

WELD_TOLERANCE_MM = 0.005


def finish_print_mesh(path: Path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise ValueError(f"Not a binary STL: {path}")
    bins = defaultdict(list)
    representatives = []
    offsets = tuple(product((-1, 0, 1), repeat=3))
    maximum_shift = 0.0
    changed_vertices = 0
    output = bytearray(b"Decorative display mesh; seams welded within 0.005 mm".ljust(80, b" "))
    output.extend(struct.pack("<I", count))
    for face_id in range(count):
        record = struct.unpack_from("<12fH", data, 84 + face_id * 50)
        triangle = []
        for offset in (3, 6, 9):
            point = tuple(record[offset:offset + 3])
            cell = tuple(math.floor(value / WELD_TOLERANCE_MM) for value in point)
            best = None
            for delta in offsets:
                neighbour = tuple(cell[axis] + delta[axis] for axis in range(3))
                for index in bins.get(neighbour, ()):
                    distance = math.dist(point, representatives[index])
                    if distance <= WELD_TOLERANCE_MM and (best is None or distance < best[0]):
                        best = (distance, index)
            if best is None:
                bins[cell].append(len(representatives))
                representatives.append(point)
                triangle.append(point)
            else:
                distance, index = best
                triangle.append(representatives[index])
                maximum_shift = max(maximum_shift, distance)
                changed_vertices += distance > 0
        a, b, c = triangle
        u, v = tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3))
        normal = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        magnitude = math.sqrt(sum(value*value for value in normal))
        if magnitude <= 1e-10:
            raise ValueError(f"Welding would collapse a triangle in {path.name}")
        normal = tuple(value/magnitude for value in normal)
        output.extend(struct.pack("<12fH", *normal, *a, *b, *c, 0))
    path.write_bytes(output)
    return {"tolerance_mm": WELD_TOLERANCE_MM, "maximum_vertex_shift_mm": maximum_shift,
            "changed_vertex_occurrences": changed_vertices, "triangle_count": count}


def finish_print_meshes(project: Path):
    report = {}
    for name in ("delta_display", "dart_display"):
        report[name] = finish_print_mesh(project / "STL" / f"{name}.stl")
    (project / "profile").mkdir(exist_ok=True)
    (project / "profile" / "mesh_finish.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"mesh_finishing": report}, indent=2), flush=True)
    return report
