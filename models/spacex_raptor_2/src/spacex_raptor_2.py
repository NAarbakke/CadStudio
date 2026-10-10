"""SpaceX Raptor 2 (2022-25) sea-level engine: full-flow staged combustion methane/oxygen engine.

The simplified second generation, shown with its oxygen inlet bellows on the axis, welded preburners, the
pump discharge duct wrapped around the chamber, three small lines, one engine controller with its
wiring, the green-grey oxidised nozzle of the photographs, and bolt circles only at the inlets, the manifold disc and the main injector.
Sources (profile_builder/Raptor/; public figures and photographs, no drawings):
  - Wikipedia "SpaceX Raptor": length 3.1 m, diameter 1.3 m, sea-level nozzle expansion ratio 34.34:1.
  - SpaceX photographs of Raptor 1, 2 and 3 (web/nse_img_1300-1302.jpg) and of a sea-level Raptor at
    Hawthorne: the stations and diameters of the main masses, read at about ±5 %.
  - Wikipedia: Raptor 2 thrust 230 tf, mass 1,630 kg, chamber pressure 300 bar.
  - Everyday Astronaut, "Raptor 1 vs Raptor 2: What did SpaceX change?": same nozzle exit diameter as
    Raptor 1, throat opened up, flanges turned into welds, parts and sensors deleted.
Taken from the sources: overall length, exit diameter, and from the photographs the layout: oxygen inlet,
pump and preburner on the chamber axis, the Ø870 hot-gas manifold disc on the main injector, the methane
turbopump under that disc beside the Ø430 chamber, the throat at 55 % of the length, and the coolant
manifold just below it on a short, wide bell. The Ø218 throat is an estimate: the Raptor 1 throat area
scaled by thrust over chamber pressure (230/185 over 300/250), a constant thrust coefficient.
Everything else is assumed for appearance (lib/raptor.py): housing shapes, the chamber and bell contour,
duct routing and diameters, flange and bolt sizes and counts, corner radii, and the finishes
(lib/materials.py). The small lines, controllers, wiring and actuators shown are indicative: their number,
size and routing are not from the sources, and the real powerhead is far denser. The gimbal actuators are
not modelled. Fasteners are a nut and stud end standing on
a flange face; no holes are cut.
Axis = +X from the top of the engine toward the nozzle exit; the methane turbopump is at +Y. Units mm.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # models/, for the shared lib/

from cadgen import glb, step, stl
from lib.materials import finishes, groups, recipes
from lib.raptor import LOOK, spec, top_bellows
from lib.shapes import assemble

R_THROAT = 109.1                                 # Raptor 1 throat area x (230 / 185) / (300 / 250)
FINISHES = {**LOOK, "nozzle": "nozzle_oxide"}    # the green-grey bell of the photographs
BOLTED = {"disc", "injector", "inlet"}
WELDED = {"preburners"}
VALVES = {"fuel"}
LINES = (80, 240, 280)                           # small lines: degrees about the axis from +Y toward +Z
CONTROLLERS = (150,)                             # engine controller box with its wiring harness

SPEC = spec(R_THROAT, top_bellows, FINISHES, BOLTED, WELDED, valves=VALVES, lines=LINES, controllers=CONTROLLERS,
            actuator=True)
GROUPS = groups(SPEC)
MATERIALS = finishes(SPEC)


def parts():
    """[(label, colour, ops)] for assemble() and the native CAD builders."""
    return recipes(SPEC)


@glb(out="../GLB/spacex_raptor_2.glb", mesh_tolerance=6e-4, mesh_angular_tolerance=0.25)
@stl(out="../STL/spacex_raptor_2.stl")
@step(out="../STEP/spacex_raptor_2.step", materials=MATERIALS)
def spacex_raptor_2():
    return assemble(parts(), "SpaceX Raptor 2", GROUPS)


if __name__ == "__main__":
    spacex_raptor_2()
