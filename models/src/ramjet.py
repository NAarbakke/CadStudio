"""Simplified axisymmetric ramjet (display model, not aero-accurate).

Axis = +X, flow enters at the spike tip (x<0) and exits at x=2900. Units mm, Ø400 airframe.
Inlet spike + cowl -> subsonic diffuser -> fuel injector ring -> V-gutter flame holders
-> combustion chamber -> convergent-divergent nozzle. No moving parts.
"""
from cadgen import build123d as bd
from cadgen import glb, srgb, step, stl
from lib.shapes import blade_ring, interp, revolved, tip_radius

OUTER_R = 200.0
# Duct inner wall (x, r): cowl lip -> diffuser -> chamber -> throat -> exit.
DUCT = [(0, 150), (250, 165), (700, 190), (2300, 190), (2600, 130), (2900, 175)]
INLET_END, CHAMBER_END = 700, 2300
STRUT_X = 450          # spike support struts
INJECTOR_X = 1000
GUTTER_X = 1300


def labelled(shape, label, color):
    shape.label = label
    shape.color = srgb(color)
    return shape


def duct_section(x0, x1, outer_front):
    """Revolved wall between stations x0..x1: outer skin at OUTER_R, inner wall following DUCT."""
    inner = [(x, r) for x, r in DUCT if x0 < x < x1]
    return revolved([(x0, outer_front), (x1, OUTER_R), (x1, interp(DUCT, x1)),
                     *reversed(inner), (x0, interp(DUCT, x0))])


def inlet():
    """Cowl lip, diffuser and the 4 struts that carry the spike."""
    cowl = revolved([(0, 150), (150, OUTER_R), (INLET_END, OUTER_R), (INLET_END, 190), (250, 165)])
    chord, thick = 150, 12
    tip = interp(DUCT, STRUT_X + chord / 2) + 5  # seat into the wall at the strut's aft (widest) edge
    body = cowl + blade_ring(STRUT_X, 90, tip, chord, thick, 4, 0)
    return labelled(body, "inlet", "#C9CED6")


def spike():
    """Conical centrebody: ~10° half-angle cone, cylindrical waist on the struts, faired tail."""
    return labelled(revolved([(-250, 0), (250, 90), (560, 90), (900, 0)]), "spike", "#2B2F36")


def fuel_injectors():
    """Toroidal spray ring on 4 feed arms from the chamber wall."""
    ring_r, tube_r = 140.0, 8.0
    ring = bd.Pos(INJECTOR_X, 0, 0) * bd.Torus(ring_r, tube_r, rotation=(0, 90, 0))
    wall = tip_radius(interp(DUCT, INJECTOR_X), 0, 10, 0)  # flat Ø10 arm end stays inside the curved wall
    arm = bd.Pos(INJECTOR_X, (ring_r + wall) / 2, 0) * bd.Cylinder(5, wall - ring_r, rotation=(90, 0, 0))
    body = ring + [bd.Rot(90 * i + 45, 0, 0) * arm for i in range(4)]
    return labelled(body, "fuel_injectors", "#B08D57")


def flame_holder():
    """Two concentric V-gutter rings (open aft) tied to the wall by 4 radial struts."""
    def gutter(r):
        x = GUTTER_X
        return revolved([(x, r), (x + 60, r + 25), (x + 60, r + 19), (x + 6, r), (x + 60, r - 19), (x + 60, r - 25)])
    chord, thick = 50, 8
    body = gutter(80) + gutter(150) + blade_ring(GUTTER_X + 30, 55, tip_radius(interp(DUCT, GUTTER_X), chord, thick, 0), chord, thick, 4, 0)
    return labelled(body, "flame_holder", "#8B5A3C")


def combustor():
    return labelled(duct_section(INLET_END, CHAMBER_END, OUTER_R), "combustion_chamber", "#6B717A")


def nozzle():
    return labelled(duct_section(CHAMBER_END, 2900, OUTER_R), "cd_nozzle", "#3A3F47")


@glb(out="../GLB/ramjet.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/ramjet.stl")
@step(out="../STEP/ramjet.step")
def ramjet():
    return bd.Compound(children=[inlet(), spike(), fuel_injectors(), flame_holder(), combustor(), nozzle()],
                       label="ramjet")


if __name__ == "__main__":
    ramjet()
