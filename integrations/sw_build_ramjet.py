"""Build the ramjet as native, parametric SolidWorks parts + assembly (feature tree, named dimensions).

    .venv\\Scripts\\python integrations\\sw_build_ramjet.py [--out models/SolidWorks/ramjet_native]

Geometry comes from models/src/ramjet.py (same profiles and strut rows as the STEP export).
Each revolved profile is a sketch "<Feature>Profile" whose vertex i is driven by dimensions
x<i>/r<i> (mm from the origin); strut rows are one extruded blade + a circular pattern whose
count is the global variable "<Feature>_count". Edit them with integrations/sw_edit.py.
SolidWorks must be open.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "models" / "src"))
import ramjet as rj  # noqa: E402  (model data only; nothing is built on import)

from sw_api import PartBuilder, build_assembly, connect, no_dimension_prompts  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("models/SolidWorks/ramjet_native"))
    out = ap.parse_args().out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sw = connect()

    def part(name, color, build):
        b = PartBuilder(sw)
        build(b)
        b.color(color)
        path = b.save(out / f"{name}.SLDPRT")
        print("built", path.name)
        return path

    def inlet(b):
        b.revolve(rj.COWL, "Cowl")
        b.blade_ring(*rj.spike_struts(), name="SpikeStruts")

    def fuel_injectors(b):
        b.revolve_circle(rj.INJECTOR_X, rj.RING_R, rj.RING_TUBE_R, "SprayRing")
        r0, r1 = rj.arm_span()
        b.blade_ring(rj.INJECTOR_X, r0, r1, 2 * rj.ARM_R, 0, 4, 0, name="FeedArms", round_section=True)

    def flame_holder(b):
        b.revolve(rj.gutter_profile(rj.GUTTER_RADII[0]), "InnerGutter")
        b.revolve(rj.gutter_profile(rj.GUTTER_RADII[1]), "OuterGutter")
        b.blade_ring(*rj.gutter_struts(), name="GutterStruts")

    with no_dimension_prompts(sw):
        parts = [
            part("inlet", "#C9CED6", inlet),
            part("spike", "#2B2F36", lambda b: b.revolve(rj.SPIKE, "Spike")),
            part("fuel_injectors", "#B08D57", fuel_injectors),
            part("flame_holder", "#8B5A3C", flame_holder),
            part("combustion_chamber", "#6B717A", lambda b: b.revolve(rj.duct_profile(rj.INLET_END, rj.CHAMBER_END), "Chamber")),
            part("cd_nozzle", "#3A3F47", lambda b: b.revolve(rj.duct_profile(rj.CHAMBER_END, rj.EXIT), "Nozzle")),
        ]
    build_assembly(sw, parts, out / "ramjet.SLDASM")
    print("built", out / "ramjet.SLDASM")


if __name__ == "__main__":
    main()
