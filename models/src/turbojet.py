"""NASA Lewis small expendable turbojet (1977), digitized from its published cross-section.

Source: resources/small_expendable_turbojet_1977.pdf, Figure 1 (see resources/README.md).
Published: axial single-spool, 4-stage compressor, annular combustor, 1-stage turbine,
fixed-area nozzle; Ø292 mm max, 965 mm long, 59 kg, 37 000 rpm, 3.1 kN thrust.
Radii/stations below are read off the figure (~±5 mm); blade counts and airfoils are assumed.
Axis = +X from the nose-cone tip. Units mm.
"""
from cadgen import build123d as bd
from cadgen import glb, step, stl
from lib.shapes import blade_ring, interp, labelled, revolved, stage, tip_radius, tube

GAP = 1.5              # rotor tip / stator hub clearance
SHAFT_R = 20.0
GAS_OUTER = [(295, 105), (487, 105), (742, 97), (820, 97)]   # casing inner wall
GAS_HUB = [(295, 65), (487, 85), (742, 63), (820, 63)]       # rotor hub / inner wall

# (kind, x, chord, thickness, count, stagger°)
COMPRESSOR = [st for i in range(4) for st in (("R", 312 + 48 * i, 20, 3, 23, 40),
                                               ("S", 336 + 48 * i if i < 3 else 474, 18, 3, 30, -35))]
TURBINE = [("S", 765, 22, 5, 25, -50), ("R", 795, 22, 4, 35, 55)]


def row(st, bore=0):
    return stage(*st, bore=bore, outer=GAS_OUTER, hub=GAS_HUB, gap=GAP)


def nose_cone():
    """Static bullet on the inlet struts, running into the compressor hub line."""
    body = revolved([(0, 0), (40, 33), (100, 52), (188, 57)], spline=True) + revolved([(188, 0), (295, 0), (295, 65), (188, 57)])
    return labelled(body, "nose_cone", "#2B2F36")


def inlet_housing():
    casing = revolved([(140, 112), (160, 122), (295, 122), (295, 105), (160, 105)])
    struts = blade_ring(205, 58, 110, 30, 8, 4, 0)  # root on the nose hub surface (r=57.5), tip into the casing wall
    return labelled(casing + struts, "inlet_housing", "#C9CED6")


def compressor_casing():
    casing = revolved([(295, 105), (295, 122), (487, 122), (487, 105)])
    return labelled(casing, "compressor_casing", "#AEB5BF")


def compressor_stators():
    return labelled(bd.Part() + [v for st in COMPRESSOR if st[0] == "S" for v in row(st)], "compressor_stators", "#7F8893")


def rotor():
    """Single spool: shaft, 4 compressor disks + blades, turbine disk + blades."""
    parts = [tube(298, 815, 0, SHAFT_R)]
    for st in COMPRESSOR + TURBINE:
        if st[0] == "R":
            parts += row(st, bore=SHAFT_R)
    return labelled(bd.Part() + parts, "rotor", "#9AA3AD")


def combustor_housing():
    outer = [(487, 122), (560, 146), (730, 146), (742, 125)]
    inner = [(742, 112), (725, 136), (565, 136), (495, 105), (487, 105)]
    return labelled(revolved(outer + inner) + tube(487, 742, 32, 45), "combustor_housing", "#6B717A")


def combustor_liner():
    """Annular liner (open aft) with 12 fuel nozzles on stems from the housing.

    The dome sits 20 mm aft of the compressor exit so air can pass around it into the housing.
    """
    liner = (revolved([(520, 82), (540, 64), (700, 61), (735, 64), (735, 97), (700, 128), (540, 128), (520, 110)])
             - revolved([(528, 85), (546, 70), (700, 67), (745, 70), (745, 92), (700, 122), (546, 122), (528, 106)]))
    r_nozzle, x_stem = 96.0, 510.0
    r_wall = tip_radius(interp([(487, 105), (495, 105), (565, 136)], x_stem), 0, 6, 0)
    nozzle = bd.Pos(516, r_nozzle, 0) * bd.Cylinder(4, 18, rotation=(0, 90, 0))
    stem = bd.Pos(x_stem, (r_nozzle + r_wall) / 2, 0) * bd.Cylinder(3, r_wall - r_nozzle, rotation=(90, 0, 0))
    body = liner + [bd.Rot(30 * i, 0, 0) * s for i in range(12) for s in (nozzle, stem)]
    return labelled(body, "combustor_liner", "#A0522D")


def turbine_nozzle():
    return labelled(bd.Part() + [v for st in TURBINE if st[0] == "S" for v in row(st)], "turbine_nozzle", "#8B5A3C")


def turbine_casing():
    return labelled(revolved([(742, 97), (742, 125), (820, 125), (820, 97)]), "turbine_casing", "#5B636E")


def exhaust():
    """Exhaust casing + fixed convergent nozzle; tail cone on 3 struts."""
    casing = revolved([(820, 97), (820, 125), (965, 100), (965, 84)])
    cone = revolved([(822, 0), (822, 60), (870, 55), (930, 30), (965, 0)])
    wall = min(interp([(820, 97), (965, 84)], x) for x in (840, 860))
    struts = blade_ring(850, 50, tip_radius(wall, 20, 6, 0), 20, 6, 3, 0)
    return (labelled(casing, "exhaust_casing", "#3A3F47"),
            labelled(cone + struts, "tail_cone", "#2B2F36"))


@glb(out="../GLB/turbojet.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/turbojet.stl")
@step(out="../STEP/turbojet.step")
def turbojet():
    return bd.Compound(children=[
        nose_cone(), inlet_housing(), compressor_casing(), compressor_stators(), rotor(),
        combustor_housing(), combustor_liner(), turbine_nozzle(), turbine_casing(), *exhaust(),
    ], label="turbojet")


if __name__ == "__main__":
    turbojet()
