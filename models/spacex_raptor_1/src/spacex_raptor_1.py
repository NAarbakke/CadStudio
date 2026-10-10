"""SpaceX Raptor 1 (2019-21) sea-level engine: full-flow staged combustion methane/oxygen engine.

The first flight generation, shown with its gimbal mount plate and block on a thrust frame, bolted flange
joints throughout, the pump discharge duct wrapped around the chamber, valves with actuators, seven small
lines, two engine controllers with wiring, a torch igniter and sensor ports on the injector and jacket.
Sources (profile_builder/Raptor/; public figures and photographs, no drawings):
  - Wikipedia "SpaceX Raptor": length 3.1 m, diameter 1.3 m, sea-level nozzle expansion ratio 34.34:1.
  - SpaceX photographs of Raptor 1, 2 and 3 (web/nse_img_1300-1302.jpg) and of a sea-level Raptor at
    Hawthorne: the stations and diameters of the main masses, read at about ±5 %.
  - Wikipedia: Raptor 1 thrust 185 tf, mass 2,080 kg, chamber pressure 250 bar.
  - Everyday Astronaut, "Raptor 1 vs Raptor 2: What did SpaceX change?": Raptor 1 is the flanged, heavily
    instrumented version.
Taken from the sources: overall length, exit diameter, the expansion ratio (which gives the Ø214 throat),
and from the photographs the layout: oxygen inlet, pump and preburner on the chamber axis, the Ø870
hot-gas manifold disc on the main injector, the methane turbopump under that disc beside the Ø430
chamber, the throat at 55 % of the length, and the coolant manifold just below it on a short, wide bell.
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
from lib.raptor import spec, top_gimbal
from lib.shapes import assemble

R_THROAT = 107.2                                 # 34.34:1 on the Ø1256 gas-side exit
BOLTED = {"disc", "preburners", "injector", "inlet"}
VALVES = {"fuel", "discharge"}
LINES = (60, 80, 100, 120, 240, 260, 280)       # small lines: degrees about the axis from +Y toward +Z
CONTROLLERS = (150, 210)                         # engine controller boxes, each with a wiring harness

SPEC = spec(R_THROAT, top_gimbal, bolted=BOLTED, valves=VALVES, ports=True, igniter=True, lines=LINES,
            controllers=CONTROLLERS, actuator=True)
GROUPS = groups(SPEC)
MATERIALS = finishes(SPEC)


def parts():
    """[(label, colour, ops)] for assemble() and the native CAD builders."""
    return recipes(SPEC)


@glb(out="../GLB/spacex_raptor_1.glb", mesh_tolerance=6e-4, mesh_angular_tolerance=0.25)
@stl(out="../STL/spacex_raptor_1.stl")
@step(out="../STEP/spacex_raptor_1.step", materials=MATERIALS)
def spacex_raptor_1():
    return assemble(parts(), "SpaceX Raptor 1", GROUPS)


if __name__ == "__main__":
    spacex_raptor_1()
