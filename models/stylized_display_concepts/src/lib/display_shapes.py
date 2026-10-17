"""Original decorative solids. All proportions are invented, in millimetres."""
from __future__ import annotations

from cadgen import build123d as bd


def beveled_plate(outline: tuple[tuple[float, float], ...], height: float):
    """A thick, flat-bottomed polygon with a small decorative top bevel."""
    plate = bd.extrude(bd.Polygon(*outline, align=None), amount=height)
    top_edges = plate.edges().group_by(bd.Axis.Z)[-1]
    return bd.chamfer(top_edges, length=1.2)


def raised_panel(lower, upper, bottom: float, top: float):
    """A faceted relief panel on a toy; these are not measured sections."""
    bottom_face = bd.Pos(0, 0, bottom) * bd.Polygon(*lower, align=None)
    top_face = bd.Pos(0, 0, top) * bd.Polygon(*upper, align=None)
    return bd.loft([bottom_face, top_face], ruled=True)


def shallow_bars(body, x: float, y: float, z: float):
    """Add two recessed graphic stripes, mirrored across the centre line."""
    for side in (-1, 1):
        cutter = bd.Pos(x, side * y, z) * bd.Box(3.0, 8.0, 1.6)
        body = body - cutter
    return body
