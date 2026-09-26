"""3M22 Tsirkon (Zircon): external-shape display model, as reconstructed from open sources.

Sources (profile_builder/Tsirkon/resources/, see its README.md):
  - Luftlage, "Not quite a diamond" (2026), reconstruction article/fig01.jpeg: ~8.5 m long, Ø0.67 m,
    two solid-propellant stages; composite second-stage casing, alloy rear section carrying four
    folding control fins, first stage with cable raceways / actuator-rod housings.
  - Kyiv forensic institute (KNDISE) side-view sketch, debris/twz_wreckage_2024-02-07.jpg: stations
    read off it (length 1485 px -> 8500 mm, 5.72 mm/px; diameter 135 px -> 670 mm).
The two agree on proportions (KNDISE L/D 12.3; 8.5 m / 0.67 m = 12.7). Only the outer shape is
modelled; station positions are ~±50 mm, fin planforms and raceway sizes are estimates, and the
larger first-stage fins in the KNDISE sketch are left out as in the newer Luftlage reconstruction.
Axis = +X from the nose tip. Units mm.
"""
from cadgen import glb, step, stl
from lib.shapes import assemble

R = 335.0              # body radius (Ø670)
LENGTH = 8500.0
NOSE_END = 1970.0      # ogive ends (KNDISE px 1545), r 263
BAND_END = 2720.0      # conical band out to full diameter (px 1415)
FINS_START = 5050.0    # alloy rear section of the second stage (fins px 935-1005)
STAGE_JOINT = 5500.0   # first/second stage joint (px 928)


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    return [
        ("nose_section", "#E6E8EB", [  # radome / seeker section with the flared band behind it
            ("spline", "Radome", [(0, 0), (60, 45), (400, 150), (1100, 230), (NOSE_END, 263)]),
            ("revolve", "Band", [(NOSE_END, 0), (BAND_END, 0), (BAND_END, R), (NOSE_END, 263)])]),
        ("second_stage", "#6B6655", [  # wound-composite motor casing
            ("revolve", "Casing2", [(BAND_END, 0), (FINS_START, 0), (FINS_START, R), (BAND_END, R)])]),
        ("control_section", "#B9BEC4", [  # heat-resistant alloy rear section with 4 folding control fins
            ("revolve", "ControlBody", [(FINS_START, 0), (STAGE_JOINT, 0), (STAGE_JOINT, R), (FINS_START, R)]),
            ("fins", "ControlFins", [(5080, R - 5), (5300, R + 260), (5440, R + 260), (5460, R - 5)], 14, 4)]),
        ("first_stage", "#C9CED6", [  # booster: raceways between the fin planes, nozzle cavity at the base
            ("revolve", "Casing1", [(STAGE_JOINT, 0), (LENGTH, 0), (LENGTH, R), (STAGE_JOINT, R)]),
            ("ring", "Raceways", 6950, R - 5, R + 25, 2800, 60, 4, 0, 45),
            ("cut", "NozzleCavity", [(8150, 0), (8150, 120), (LENGTH, 270), (LENGTH, 0)])]),
    ]


@glb(out="../GLB/tsirkon.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/tsirkon.stl")
@step(out="../STEP/tsirkon.step")
def tsirkon():
    return assemble(parts(), "tsirkon")


if __name__ == "__main__":
    tsirkon()
