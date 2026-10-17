"""Broad delta sculpture: invented 120 x 68 x 18 mm display geometry."""
from cadgen import build123d as bd
from cadgen import glb, srgb, step, stl

from lib.display_shapes import beveled_plate, raised_panel, shallow_bars

LENGTH_MM = 120.0
WIDTH_MM = 68.0
HEIGHT_MM = 18.0


@step(out="../STEP/delta_display.step")
@stl(out="../STL/delta_display.stl")
@glb(out="../GLB/delta_display.glb")
def delta_display():
    outline = (
        (-60, -4), (-37, -12), (37, -34), (60, -26),
        (60, 26), (37, 34), (-37, 12), (-60, 4),
    )
    lower = ((-48, -4), (12, -19), (53, -17), (53, 17), (12, 19), (-48, 4))
    upper = ((-28, -3), (15, -8), (45, -8), (45, 8), (15, 8), (-28, 3))
    body = beveled_plate(outline, height=6.0)
    body = body + raised_panel(lower, upper, bottom=5.0, top=HEIGHT_MM)
    body = shallow_bars(body, x=38.0, y=25.0, z=6.0)
    body = body.clean()
    body.label = "delta_display_invented"
    body.color = srgb("#D87838")
    return body


if __name__ == "__main__":
    delta_display()
