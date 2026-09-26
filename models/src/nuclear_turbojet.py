"""OKB-165 (Lyulka) direct-cycle nuclear turbojet with an offset reactor, from a period illustration.

Source: resources/illustrations/direct_cooling_offset_reactor_nuclear_turbojet/ (side view, 290x105 px).
Layout from the drawing: compressor and turbine/nozzle on one axis, joined by a long shaft tunnel;
compressor air rises through an S-duct into a reactor vessel above the axis (the core is cooled
directly by the engine air) and falls through a second S-duct to the turbine.
Scale: no dimensions are published; the compressor module is sized to Lyulka's contemporary AL-7
(Ø1300 mm, 9-stage compressor, 2-stage turbine), giving 32.5 mm/px and ~8.9 m overall.
x_mm = (x_px - 5) * 32.5, r_mm = |y_px - 67| * 32.5. Blade counts, airfoils, wall thicknesses and
the reactor internals (a plain core with end grids) are assumptions. Axis = +X, units mm.
"""
from cadgen import glb, step, stl
from lib.shapes import assemble, duct_stations, interp, stage, tip_radius, tube_profile

REACTOR_Y = 975.0      # reactor axis above the engine axis (px 37 vs 67)
WALL = 50.0            # duct and vessel wall
GAP = 3.0              # rotor tip / stator hub clearance
SHAFT_R = 100.0
TUNNEL = (120.0, 160.0)  # static shaft tunnel under the reactor: r_in, r_out

# Compressor, px 28-70 -> x 750-2110; casing Ø1300 stepping down to Ø1060 (px 50-70).
C_OUTER = [(750, 600), (1460, 585), (2110, 470)]
C_HUB = [(750, 250), (2110, 360)]
# Turbine, px 235-250 -> x 7475-7960; nozzle to px 265 (x 8450); tail cone to px 280 (x 8940).
T_OUTER = [(7475, 600), (7960, 610)]
T_HUB = [(7475, 330), (7960, 360)]
NOZZLE_INNER = [(7960, 610), (8450, 520)]

# (name, kind, x, chord, thickness, count, stagger°): AL-7-like 9 compressor + 2 turbine stages
COMPRESSOR = [st for i in range(9) for st in ((f"C{i + 1}Rotor", "R", 830 + 135 * i, 60, 4, 32, 40),
                                              (f"C{i + 1}Stator", "S", 897 + 135 * i, 55, 4, 44, -35))]
TURBINE = [("T1Nozzle", "S", 7540, 60, 8, 40, -50), ("T1Rotor", "R", 7640, 60, 6, 60, 55),
           ("T2Nozzle", "S", 7740, 60, 8, 40, -50), ("T2Rotor", "R", 7850, 60, 6, 60, 55)]

# Reactor vessel about the offset axis (px 82-180): inlet plenum Ø910, pressure vessel Ø1500.
VESSEL = [(2950, 455), (3850, 455), (3900, 750), (5620, 750), (5800, 560),
          (5800, 560 - WALL), (5620, 750 - WALL), (3900, 750 - WALL), (3850, 455 - WALL), (2950, 455 - WALL)]
# S-ducts (x, y_centre, r_outer): compressor exit -> plenum, vessel outlet -> turbine inlet.
INLET_DUCT = duct_stations((2110, 0, 530), (2950, REACTOR_Y, 455))
OUTLET_DUCT = duct_stations((5800, REACTOR_Y, 560), (7475, 0, 650))


def rows(stages, kind, outer, hub, bore=0):
    return [op for st in stages if st[1] == kind
            for op in stage(*st, bore=bore, outer=outer, hub=hub, gap=GAP)]


def ducted(name, stations):
    """S-duct with a passage cut where the shaft tunnel runs through its lower wall."""
    return [("duct", name, stations, WALL), ("cut", f"{name}TunnelPassage", tube_profile(2010, 7510, 0, TUNNEL[1]))]


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    strut_tip = tip_radius(min(interp(C_OUTER, 755), interp(C_OUTER, 785)), 30, 8, 0)
    tail_tip = tip_radius(min(interp(NOZZLE_INNER, 8030), interp(NOZZLE_INNER, 8070)), 40, 8, 0)
    return [
        ("nose_cone", "#2B2F36", [  # static bullet carried by 4 inlet struts (px 5-28)
            ("spline", "NoseTip", [(0, 0), (150, 150), (400, 215), (750, 230)]),
            ("revolve", "NoseBody", [(750, 0), (790, 0), (790, 245), (750, 230)]),
            ("ring", "InletStruts", 770, 200, strut_tip, 30, 8, 4, 0)]),
        ("compressor_casing", "#AEB5BF", [
            ("revolve", "CompCasing", [(750, 650), (1700, 650), (2000, 530), (2110, 530), *reversed(C_OUTER)])]),
        ("compressor_stators", "#7F8893", rows(COMPRESSOR, "S", C_OUTER, C_HUB)),
        ("rotor", "#9AA3AD", [  # single spool: the shaft runs ~7 m under the reactor to the turbine
            ("revolve", "Shaft", tube_profile(800, 7880, 0, SHAFT_R)),  # 20 mm clear of the tail cone
            *rows(COMPRESSOR, "R", C_OUTER, C_HUB, SHAFT_R), *rows(TURBINE, "R", T_OUTER, T_HUB, SHAFT_R)]),
        ("inlet_duct", "#C9CED6", ducted("InletDuct", INLET_DUCT)),
        ("reactor_vessel", "#5B636E", [("offset_revolve", "Vessel", VESSEL, REACTOR_Y)]),
        ("reactor_core", "#B8860B", [  # core seated on end grids against the vessel wall
            ("offset_revolve", "Core", [(3950, 0), (3950, 700), (3980, 700), (3980, 660), (5570, 660),
                                        (5570, 700), (5600, 700), (5600, 0)], REACTOR_Y)]),
        ("outlet_duct", "#C9CED6", ducted("OutletDuct", OUTLET_DUCT)),
        ("shaft_tunnel", "#6E7782", [  # static tunnel with fairings into the compressor and turbine hubs
            ("revolve", "Tunnel", [(2010, TUNNEL[0]), (7510, TUNNEL[0]), (7510, 330), (7475, 330),
                                   (7200, TUNNEL[1]), (2300, TUNNEL[1]), (2010, 360)])]),
        ("turbine_casing", "#5B636E", [("revolve", "TurbCasing", [(7475, 650), (7960, 650), *reversed(T_OUTER)])]),
        ("turbine_nozzles", "#8B5A3C", rows(TURBINE, "S", T_OUTER, T_HUB)),
        ("nozzle", "#3A3F47", [("revolve", "Nozzle", [(7960, 650), (8450, 560), *reversed(NOZZLE_INNER)])]),
        ("tail_cone", "#2B2F36", [
            ("revolve", "TailCone", [(7900, 0), (7900, 360), (8100, 360), (8940, 0)]),
            ("ring", "TailStruts", 8050, 300, tail_tip, 40, 8, 4, 0)]),
    ]


@glb(out="../GLB/nuclear_turbojet.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/nuclear_turbojet.stl")
@step(out="../STEP/nuclear_turbojet.step")
def nuclear_turbojet():
    return assemble(parts(), "nuclear_turbojet")


if __name__ == "__main__":
    nuclear_turbojet()
