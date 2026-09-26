"""Simplified axisymmetric ramjet (display model, not aero-accurate).

Axis = +X, flow enters at the spike tip (x<0) and exits at x=2900. Units mm, Ø400 airframe.
Inlet spike + cowl -> subsonic diffuser -> fuel injector ring -> V-gutter flame holders
-> combustion chamber -> convergent-divergent nozzle. No moving parts.

parts() is the single description of the geometry: cadgen builds the STEP/STL/GLB from it and
integrations/sw_build.py builds the same parts as native SolidWorks features.
"""
from cadgen import glb, step, stl
from lib.shapes import assemble, interp, tip_radius

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


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    strut_x, strut_chord = 450, 150  # spike struts: root on the spike waist, tip seated into the diffuser wall
    gutter_chord, gutter_thick = 50, 8
    arm_tip = tip_radius(interp(DUCT, INJECTOR_X), 0, 2 * ARM_R, 0)  # flat Ø10 arm end kept inside the curved wall
    return [
        ("inlet", "#C9CED6", [
            ("revolve", "Cowl", COWL),
            ("ring", "SpikeStruts", strut_x, 90, interp(DUCT, strut_x + strut_chord / 2) + 5, strut_chord, 12, 4, 0)]),
        ("spike", "#2B2F36", [("revolve", "Spike", SPIKE)]),
        ("fuel_injectors", "#B08D57", [  # toroidal spray ring on 4 feed arms from the chamber wall
            ("torus", "SprayRing", INJECTOR_X, RING_R, RING_TUBE_R),
            ("pins", "FeedArms", INJECTOR_X, RING_R, arm_tip, 2 * ARM_R, 4)]),
        ("flame_holder", "#8B5A3C", [  # two concentric V-gutter rings tied to the wall by 4 radial struts
            ("revolve", "InnerGutter", gutter_profile(GUTTER_RADII[0])),
            ("revolve", "OuterGutter", gutter_profile(GUTTER_RADII[1])),
            ("ring", "GutterStruts", GUTTER_X + 30, 55, tip_radius(interp(DUCT, GUTTER_X), gutter_chord, gutter_thick, 0),
             gutter_chord, gutter_thick, 4, 0)]),
        ("combustion_chamber", "#6B717A", [("revolve", "Chamber", duct_profile(INLET_END, CHAMBER_END))]),
        ("cd_nozzle", "#3A3F47", [("revolve", "Nozzle", duct_profile(CHAMBER_END, EXIT))]),
    ]


@glb(out="../GLB/ramjet.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/ramjet.stl")
@step(out="../STEP/ramjet.step")
def ramjet():
    return assemble(parts(), "ramjet")


if __name__ == "__main__":
    ramjet()
