"""Narrow dart sculpture: invented 136 x 60 x 22 mm display geometry."""
from cadgen import glb, srgb, step, stl

from lib.display_shapes import beveled_plate, raised_panel, shallow_bars

LENGTH_MM = 136.0
WIDTH_MM = 60.0
HEIGHT_MM = 22.0


@step(out="../STEP/dart_display.step")
@stl(out="../STL/dart_display.stl")
@glb(out="../GLB/dart_display.glb")
def dart_display():
    outline = (
        (-68, -4), (-52, -13), (18, -18), (49, -30), (62, -30),
        (58, -16), (68, -12), (68, 12), (58, 16), (62, 30),
        (49, 30), (18, 18), (-52, 13), (-68, 4),
    )
    lower = (
        (-52, -4), (-28, -12), (36, -13), (56, -8),
        (56, 8), (36, 13), (-28, 12), (-52, 4),
    )
    upper = (
        (-28, -3), (-16, -5), (32, -5), (44, -3),
        (44, 3), (32, 5), (-16, 5), (-28, 3),
    )
    body = beveled_plate(outline, height=6.0)
    body = body + raised_panel(lower, upper, bottom=5.0, top=HEIGHT_MM)
    body = shallow_bars(body, x=52.0, y=23.5, z=6.0)
    body = body.clean()
    body.label = "dart_display_invented"
    body.color = srgb("#3C8FAD")
    return body


if __name__ == "__main__":
    dart_display()
