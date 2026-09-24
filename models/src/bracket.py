from cadgen import build123d as bd
from cadgen import step, stl

WIDTH = 40.0
LEG = 30.0
THICK = 5.0
HOLE_D = 5.5  # M5 clearance


@stl(out="../STL/bracket.stl")
@step(out="../STEP/bracket.step")
def bracket():
    base = bd.Box(LEG, WIDTH, THICK, align=bd.Align.MIN)
    wall = bd.Box(THICK, WIDTH, LEG, align=bd.Align.MIN)
    body = base + wall
    for y in (WIDTH / 4, 3 * WIDTH / 4):
        body -= bd.Pos(LEG * 0.6, y, 0) * bd.Cylinder(HOLE_D / 2, THICK, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        body -= bd.Pos(0, y, LEG * 0.6) * bd.Rot(0, 90, 0) * bd.Cylinder(HOLE_D / 2, THICK, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    body.label = "bracket"
    return body


if __name__ == "__main__":
    bracket()
