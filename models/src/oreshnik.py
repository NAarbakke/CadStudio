"""Oreshnik IRBM: external-shape display model, as reconstructed from open sources.

Source: Luftlage, "The missile that came in from the cold" (2026), reconstruction
profile_builder/Oreshnik/resources/article/fig01.jpeg: ~13 m long, Ø1.61 m, two solid-propellant
stages (most plausibly Yars 2nd/3rd-stage derived), ogive nose fairing, instrumentation band.
Stations read off the drawing at 12.2 mm/px (its body reads Ø1.65 m, ~±50 mm). Which joint mark is
the stage separation is not stated; 6.92 m from the tip is assumed. Only the outer shape is
modelled (no post-boost stage, payload or internals). Axis = +X from the nose tip. Units mm.
"""
from cadgen import glb, step, stl
from lib.shapes import assemble

R = 805.0              # Ø1.61 m
LENGTH = 13000.0
FAIRING_END = 3111.0   # px 1040
BAND_END = 3233.0      # light instrumentation-compartment band, px 1030
STAGE_JOINT = 6917.0   # assumed stage separation (joint mark at px 728)
SKIRT = 11651.0        # aft skirt line, px 340


def body(name, x0, x1):
    return ("revolve", name, [(x0, 0), (x1, 0), (x1, R), (x0, R)])


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    return [
        ("nose_fairing", "#5A564B", [  # ogive over the post-boost stage; small blunt tip
            ("spline", "Fairing", [(0, 0), (80, 95), (400, 330), (793, 490), (1403, 653), (2135, 772), (2700, 800), (FAIRING_END, R)])]),
        ("instrument_compartment", "#D8D2C0", [body("InstrumentBand", FAIRING_END, BAND_END)]),
        ("second_stage", "#6B6759", [body("Stage2", BAND_END, STAGE_JOINT)]),
        ("first_stage", "#625E52", [body("Stage1", STAGE_JOINT, SKIRT)]),
        ("aft_skirt", "#4E4B42", [  # skirt around the first-stage nozzle
            body("AftSkirt", SKIRT, LENGTH),
            ("cut", "NozzleCavity", [(12300, 0), (12300, 300), (LENGTH, 700), (LENGTH, 0)])]),
    ]


@glb(out="../GLB/oreshnik.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/oreshnik.stl")
@step(out="../STEP/oreshnik.step")
def oreshnik():
    return assemble(parts(), "oreshnik")


if __name__ == "__main__":
    oreshnik()
