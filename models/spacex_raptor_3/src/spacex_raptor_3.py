"""SpaceX Raptor 3 (2024-) sea-level engine: full-flow staged combustion methane/oxygen engine.

The third generation: secondary flow circuits, sensors and much of the plumbing are inside the housing
walls and the engine needs no heat shield. Shown as in the photograph: a flanged oxygen inlet studded onto
smooth dark welded housings, the methane pump dropping straight into the coolant manifold, a bare dark
nozzle, one thin service line, no visible valves, igniter or oxygen line.
Sources (profile_builder/Raptor/; public figures and photographs, no drawings):
  - Wikipedia "SpaceX Raptor": length 3.1 m, diameter 1.3 m, sea-level nozzle expansion ratio 34.34:1.
  - SpaceX photographs of Raptor 1, 2 and 3 (web/nse_img_1300-1302.jpg) and of a sea-level Raptor at
    Hawthorne: the stations and diameters of the main masses, read at about ±5 %.
  - Wikipedia: Raptor 3 mass 1,525 kg. SpaceX and Elon Musk, 2024: target thrust 280 tf at 350 bar chamber
    pressure; integral cooling and secondary flow circuits in the walls; no engine heat shield.
Taken from the sources: overall length, exit diameter, and from the photographs the layout: oxygen inlet,
pump and preburner on the chamber axis, the Ø870 hot-gas manifold disc on the main injector, the methane
turbopump under that disc beside the Ø430 chamber, the throat at 55 % of the length, and the coolant
manifold just below it on a short, wide bell. The Ø223 throat is an estimate: the Raptor 1 throat area
scaled by thrust over chamber pressure (280/185 over 350/250), a constant thrust coefficient.
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
from lib.raptor import spec, top_flange
from lib.shapes import assemble

R_THROAT = 111.5                                 # Raptor 1 throat area x (280 / 185) / (350 / 250)
FINISHES = {"body": "dark_steel", "hot": "dark_steel", "duct": "dark_steel", "nozzle": "dark_steel", "tint": False}
BOLTED = {"disc", "inlet"}
WELDED = {"preburners", "injector"}

SPEC = spec(R_THROAT, top_flange, FINISHES, BOLTED, WELDED, feed="elbow", lox_line=False, service_line=True)
GROUPS = groups(SPEC)
MATERIALS = finishes(SPEC)


def parts():
    """[(label, colour, ops)] for assemble() and the native CAD builders."""
    return recipes(SPEC)


@glb(out="../GLB/spacex_raptor_3.glb", mesh_tolerance=6e-4, mesh_angular_tolerance=0.25)
@stl(out="../STL/spacex_raptor_3.stl")
@step(out="../STEP/spacex_raptor_3.step", materials=MATERIALS)
def spacex_raptor_3():
    return assemble(parts(), "SpaceX Raptor 3", GROUPS)


if __name__ == "__main__":
    spacex_raptor_3()
