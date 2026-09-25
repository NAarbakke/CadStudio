"""Simplified axisymmetric ramjet (display model, not aero-accurate).

Axis = +X, flow enters at the spike tip (x<0) and exits at x=2900. Units mm, Ø400 airframe.
Inlet spike + cowl -> subsonic diffuser -> fuel injector ring -> V-gutter flame holders
-> combustion chamber -> convergent-divergent nozzle. No moving parts.

The profiles and strut rows below are plain data so integrations/sw_build_ramjet.py builds the
same geometry as native SolidWorks features.
"""
from cadgen import build123d as bd
from cadgen import glb, step, stl
from lib.shapes import blade_ring, interp, labelled, revolved, tip_radius

OUTER_R = 200.0
# Duct inner wall (x, r): cowl lip -> diffuser -> chamber -> throat -> exit.
DUCT = [(0, 150), (250, 165), (700, 190), (2300, 190), (2600, 130), (2900, 175)]
INLET_END, CHAMBER_END, EXIT = 700, 2300, 2900
INJECTOR_X, RING_R, RING_TUBE_R, ARM_R = 1000, 140.0, 8.0, 5.0
GUTTER_X, GUTTER_RADII = 1300, (80, 150)

COWL = [(0, 150), (150, OUTER_R), (INLET_END, OUTER_R), (INLET_END, 190), (250, 165)]
SPIKE = [(-250, 0), (250, 90), (560, 90), (900, 0)]  # ~10° cone, waist on the struts, faired tail


def duct_profile(x0, x1):
    """Wall between stations x0..x1: outer skin at OUTER_R, inner wall following DUCT."""
    inner = [(x, r) for x, r in DUCT if x0 < x < x1]
    return [(x0, OUTER_R), (x1, OUTER_R), (x1, interp(DUCT, x1)), *reversed(inner), (x0, interp(DUCT, x0))]


def gutter_profile(r):
    """V-gutter cross-section (open aft) with its apex at (GUTTER_X, r)."""
    x = GUTTER_X
    return [(x, r), (x + 60, r + 25), (x + 60, r + 19), (x + 6, r), (x + 60, r - 19), (x + 60, r - 25)]


def spike_struts():
    """(x, r0, r1, chord, thick, n, stagger): root on the spike waist, tip seated into the diffuser wall."""
    x, chord = 450, 150
    return (x, 90, interp(DUCT, x + chord / 2) + 5, chord, 12, 4, 0)


def gutter_struts():
    chord, thick = 50, 8
    return (GUTTER_X + 30, 55, tip_radius(interp(DUCT, GUTTER_X), chord, thick, 0), chord, thick, 4, 0)


def arm_span():
    """Feed arms run from the ring centreline to the wall (flat Ø10 end kept inside the curved wall)."""
    return RING_R, tip_radius(interp(DUCT, INJECTOR_X), 0, 2 * ARM_R, 0)


def inlet():
    return labelled(revolved(COWL) + blade_ring(*spike_struts()), "inlet", "#C9CED6")


def spike():
    return labelled(revolved(SPIKE), "spike", "#2B2F36")


def fuel_injectors():
    """Toroidal spray ring on 4 feed arms from the chamber wall."""
    ring = bd.Pos(INJECTOR_X, 0, 0) * bd.Torus(RING_R, RING_TUBE_R, rotation=(0, 90, 0))
    r0, r1 = arm_span()
    arm = bd.Pos(INJECTOR_X, (r0 + r1) / 2, 0) * bd.Cylinder(ARM_R, r1 - r0, rotation=(90, 0, 0))
    return labelled(ring + [bd.Rot(90 * i, 0, 0) * arm for i in range(4)], "fuel_injectors", "#B08D57")


def flame_holder():
    """Two concentric V-gutter rings tied to the wall by 4 radial struts."""
    body = revolved(gutter_profile(GUTTER_RADII[0])) + revolved(gutter_profile(GUTTER_RADII[1]))
    return labelled(body + blade_ring(*gutter_struts()), "flame_holder", "#8B5A3C")


def combustor():
    return labelled(revolved(duct_profile(INLET_END, CHAMBER_END)), "combustion_chamber", "#6B717A")


def nozzle():
    return labelled(revolved(duct_profile(CHAMBER_END, EXIT)), "cd_nozzle", "#3A3F47")


@glb(out="../GLB/ramjet.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/ramjet.stl")
@step(out="../STEP/ramjet.step")
def ramjet():
    return bd.Compound(children=[inlet(), spike(), fuel_injectors(), flame_holder(), combustor(), nozzle()],
                       label="ramjet")


if __name__ == "__main__":
    ramjet()
