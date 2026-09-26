"""NASA Lewis small expendable turbojet (1977), digitized from its published cross-section.

Source: resources/small_expendable_turbojet_1977.pdf, Figure 1 (see resources/README.md).
Published: axial single-spool, 4-stage compressor, annular combustor, 1-stage turbine,
fixed-area nozzle; Ø292 mm max, 965 mm long, 59 kg, 37 000 rpm, 3.1 kN thrust.
Radii/stations below are read off the figure (~±5 mm); blade counts and airfoils are assumed.
Axis = +X from the nose-cone tip. Units mm.
"""
from cadgen import glb, step, stl
from lib.shapes import assemble, interp, stage, tip_radius, tube_profile

GAP = 1.5              # rotor tip / stator hub clearance
SHAFT_R = 20.0
GAS_OUTER = [(295, 105), (487, 105), (742, 97), (820, 97)]   # casing inner wall
GAS_HUB = [(295, 65), (487, 85), (742, 63), (820, 63)]       # rotor hub / inner wall

# (name, kind, x, chord, thickness, count, stagger°)
COMPRESSOR = [st for i in range(4) for st in ((f"Comp{i + 1}Rotor", "R", 312 + 48 * i, 20, 3, 23, 40),
                                               (f"Comp{i + 1}Stator", "S", 336 + 48 * i if i < 3 else 474, 18, 3, 30, -35))]
TURBINE = [("TurbNozzle", "S", 765, 22, 5, 25, -50), ("TurbRotor", "R", 795, 22, 4, 35, 55)]


def rows(stages, kind, bore=0):
    return [op for st in stages if st[1] == kind
            for op in stage(*st, bore=bore, outer=GAS_OUTER, hub=GAS_HUB, gap=GAP)]


def combustor_liner():
    """Annular liner (open aft) with 12 fuel nozzles on stems from the housing.

    The dome sits 20 mm aft of the compressor exit so air can pass around it into the housing.
    """
    r_nozzle, x_stem = 96.0, 510.0
    r_wall = tip_radius(interp([(487, 105), (495, 105), (565, 136)], x_stem), 0, 6, 0)
    return [("revolve", "Liner", [(520, 82), (540, 64), (700, 61), (735, 64), (735, 97), (700, 128), (540, 128), (520, 110)]),
            ("cut", "LinerInside", [(528, 85), (546, 70), (700, 67), (745, 70), (745, 92), (700, 122), (546, 122), (528, 106)]),
            ("axial_pins", "FuelNozzles", 516, r_nozzle, 8, 18, 12),
            ("pins", "NozzleStems", x_stem, r_nozzle, r_wall, 6, 12)]


def tail_cone():
    """Tail cone on 3 struts inside the exhaust casing."""
    wall = min(interp([(820, 97), (965, 84)], x) for x in (840, 860))
    return [("revolve", "TailCone", [(822, 0), (822, 60), (870, 55), (930, 30), (965, 0)]),
            ("ring", "TailStruts", 850, 50, tip_radius(wall, 20, 6, 0), 20, 6, 3, 0)]


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    return [
        ("nose_cone", "#2B2F36", [  # static bullet on the inlet struts, running into the compressor hub line
            ("spline", "NoseTip", [(0, 0), (40, 33), (100, 52), (188, 57)]),
            ("revolve", "NoseBody", [(188, 0), (295, 0), (295, 65), (188, 57)])]),
        ("inlet_housing", "#C9CED6", [
            ("revolve", "InletCasing", [(140, 112), (160, 122), (295, 122), (295, 105), (160, 105)]),
            ("ring", "InletStruts", 205, 58, 110, 30, 8, 4, 0)]),  # root on the nose hub (r=57.5), tip into the wall
        ("compressor_casing", "#AEB5BF", [("revolve", "CompCasing", [(295, 105), (295, 122), (487, 122), (487, 105)])]),
        ("compressor_stators", "#7F8893", rows(COMPRESSOR, "S")),
        ("rotor", "#9AA3AD", [  # single spool: shaft, 4 compressor disks + blades, turbine disk + blades
            ("revolve", "Shaft", tube_profile(298, 815, 0, SHAFT_R)), *rows(COMPRESSOR + TURBINE, "R", SHAFT_R)]),
        ("combustor_housing", "#6B717A", [
            ("revolve", "Housing", [(487, 122), (560, 146), (730, 146), (742, 125),
                                    (742, 112), (725, 136), (565, 136), (495, 105), (487, 105)]),
            ("revolve", "InnerCasing", tube_profile(487, 742, 32, 45))]),
        ("combustor_liner", "#A0522D", combustor_liner()),
        ("turbine_nozzle", "#8B5A3C", rows(TURBINE, "S")),
        ("turbine_casing", "#5B636E", [("revolve", "TurbCasing", [(742, 97), (742, 125), (820, 125), (820, 97)])]),
        ("exhaust_casing", "#3A3F47", [("revolve", "ExhaustCasing", [(820, 97), (820, 125), (965, 100), (965, 84)])]),
        ("tail_cone", "#2B2F36", tail_cone()),
    ]


@glb(out="../GLB/turbojet.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/turbojet.stl")
@step(out="../STEP/turbojet.step")
def turbojet():
    return assemble(parts(), "turbojet")


if __name__ == "__main__":
    turbojet()
