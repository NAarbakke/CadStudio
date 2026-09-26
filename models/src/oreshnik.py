"""Oreshnik IRBM: cutaway display model, as reconstructed from open sources.

Sources (profile_builder/Oreshnik/resources/, see its README.md):
  - Luftlage, "The missile that came in from the cold" (2026): reconstruction article/fig01.jpeg
    (~13 m, Ø1.61 m, two solid stages, most plausibly Yars 2nd/3rd-stage derived; stations read at
    12.2 mm/px), post-boost control system reconstruction fig02.jpeg (attachment ring, central
    solid-propellant gas generator, thrusters), instrumentation compartment fig03.jpeg (sealed drum
    with a lattice end plate, as on Topol / START-1), 36 objects in six clusters (fig04.jpeg).
  - RU2743670 (solid motor with two exhaust flow modes, the post-boost gas generator type).
Illustration level: the post-boost stage shows layout only (no valve internals), the six payload
objects are plain cones on a mounting plate, grains are plain cylindrical-bore cartridges. Where the
stage separation lies is not stated; 6.92 m from the tip is assumed. Axis = +X from the tip. Units mm.
"""
from cadgen import glb, step, stl
from lib.rocket import motor, shell, sphere, tube
from lib.shapes import assemble

R = 805.0              # Ø1.61 m
LENGTH = 13000.0
FAIRING_END = 3111.0   # px 1040
BAND_END = 3233.0      # instrumentation compartment band, px 1030
STAGE_JOINT = 6917.0   # assumed stage separation (joint mark at px 728)
SKIRT = 11651.0        # aft skirt line, px 340
FAIRING = [(0, 0), (80, 95), (400, 330), (793, 490), (1403, 653), (2135, 772), (2700, 800), (FAIRING_END, R)]

STAGE2 = motor("S2", xe0=3690, xe1=6300, r=R, t=15, a=400, port_fwd=150, port_aft=250, bore=300,
               throat=(6800, 180), exit=(7350, 560), t_nozzle=15, skirts=[(BAND_END, 3690), (6300, STAGE_JOINT)])
STAGE1 = motor("S1", xe0=7850, xe1=11500, r=R, t=15, a=400, port_fwd=150, port_aft=300, bore=300,
               throat=(12000, 220), exit=(12950, 700), t_nozzle=15, skirts=[(STAGE_JOINT, 7850), (11500, SKIRT)])
PBCS_X = 2950.0        # centre of the post-boost gas generator


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    return [
        ("nose_fairing", "#5A564B", [("revolve", "Fairing", shell(FAIRING, 15))]),
        ("payload", "#8C5A5A", [  # six cones on a mounting plate (36 objects in six clusters observed)
            ("offset_ring", "PayloadCones", [(1300, 0), (2650, 190), (2650, 0)], 400, 6),
            ("revolve", "MountPlate", [(2650, 0), (2700, 0), (2700, 650), (2650, 650)])]),
        ("post_boost_stage", "#9A9C8E", [  # fig02 layout: gas generator, radial struts, attachment ring, thrusters
            ("revolve", "GasGenerator", sphere(PBCS_X, 200)),
            ("ring", "Struts", 3000, 180, 710, 60, 30, 4, 0),
            ("revolve", "AttachRing", [(3000, 700), (3100, 700), (3100, 780), (3000, 780)]),
            ("axial_pins", "Thrusters", 2900, 550, 100, 120, 4, 45)]),
        ("instrument_compartment", "#D8D2C0", [
            ("revolve", "InstrumentShell", tube(FAIRING_END, BAND_END, R, 20)),
            ("revolve", "LatticePlate", [(3150, 0), (3190, 0), (3190, R - 20), (3150, R - 20)])]),
        ("stage2_case", "#6B6759", STAGE2["case"]),
        ("stage2_grain", "#B89A6A", STAGE2["grain"]),
        ("stage2_igniter", "#D05A3A", STAGE2["igniter"]),
        ("stage2_nozzle", "#8A8F96", STAGE2["nozzle"]),
        ("stage1_case", "#625E52", STAGE1["case"]),
        ("stage1_grain", "#B89A6A", STAGE1["grain"]),
        ("stage1_igniter", "#D05A3A", STAGE1["igniter"]),
        ("stage1_nozzle", "#8A8F96", STAGE1["nozzle"]),
        ("aft_skirt", "#4E4B42", [("revolve", "AftSkirt", tube(SKIRT, LENGTH, R, 20))]),
    ]


@glb(out="../GLB/oreshnik.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/oreshnik.stl")
@step(out="../STEP/oreshnik.step")
def oreshnik():
    return assemble(parts(), "oreshnik")


if __name__ == "__main__":
    oreshnik()
