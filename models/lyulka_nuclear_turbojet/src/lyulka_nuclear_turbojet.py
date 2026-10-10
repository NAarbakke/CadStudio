"""OKB-165 (Lyulka) direct-cycle nuclear turbojet with an offset reactor, from a period illustration.

23 parts in 5 sub-assemblies (GROUPS) plus the shaft tunnel.

Source: profile_builder/Nuclear_turbojet/ (side view, 290x105 px).
Layout from the drawing: compressor and turbine/nozzle on one axis, joined by a long shaft tunnel;
compressor air rises through an S-duct into a reactor vessel above the axis (the core is cooled
directly by the engine air) and falls through a second S-duct to the turbine.
Scale: no dimensions are published; the compressor module is sized to Lyulka's contemporary AL-7
(Ø1300 mm, 9-stage compressor, 2-stage turbine), giving 32.5 mm/px and ~8.9 m overall.
x_mm = (x_px - 5) * 32.5, r_mm = |y_px - 67| * 32.5. Blade counts, airfoils, wall thicknesses and
the reactor internals (a plain core with end grids) are assumptions.
Assumed for appearance, not taken from the drawing: the intake lip, every flange and bolt circle (M16
studs at the casing, duct, vessel and nozzle joints), the split of the casings, vessel and rotor into
separate parts, the vessel stiffening bands, the four control drive housings on top of the vessel, edge
chamfers, and the finishes (lib/materials.py). Fasteners are a nut and stud end standing on a flange
face; no holes are cut. The flanges take the casing from Ø1300 to Ø1420 and the vessel from Ø1500 to Ø1620.
Axis = +X, units mm.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # models/, for the shared lib/

from cadgen import glb, step, stl
from lib.materials import finishes, groups, recipes
from lib.shapes import assemble, duct_stations, flange_bolts, interp, stage, tip_radius, tube_profile

REACTOR_Y = 975.0      # reactor axis above the engine axis (px 37 vs 67)
WALL = 50.0            # duct and vessel wall
GAP = 3.0              # rotor tip / stator hub clearance
SHAFT_R = 100.0
TUNNEL = (120.0, 160.0)  # static shaft tunnel under the reactor: r_in, r_out
STUD = 16.0            # bolt circles: stud diameter (assumed)
X_AXIS = (1, 0, 0)
ENGINE, REACTOR = (0, 0, 0), (0, REACTOR_Y, 0)   # a point on the engine axis and on the reactor axis

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
X_PLENUM, X_VESSEL, X_CLOSURE, X_OUTLET = 2950, 3850, 5620, 5800
R_PLENUM, R_VESSEL, R_OUTLET = 455, 750, 560
BANDS = (4330, 4760, 5190)           # vessel stiffening bands (assumed)
DRIVES = (4150, 4550, 4950, 5350)    # control drive housings on top of the vessel (assumed)
# S-ducts (x, y_centre, r_outer): compressor exit -> plenum, vessel outlet -> turbine inlet.
INLET_DUCT = duct_stations((2110, 0, 530), (X_PLENUM, REACTOR_Y, R_PLENUM))
OUTLET_DUCT = duct_stations((X_OUTLET, REACTOR_Y, R_OUTLET), (7475, 0, 650))


def rows(stages, kind, outer, hub, bore=0):
    return [op for st in stages if st[1] == kind
            for op in stage(*st, bore=bore, outer=outer, hub=hub, gap=GAP)]


def turned(name, points, origin=ENGINE):
    """Casing or ring with chamfered edges (large thin rings: a rounded edge meshes very finely)."""
    return ("lathe", name, points, 5, origin, X_AXIS, True)


def flange(name, x0, x1, r0, r1, origin=ENGINE):
    return turned(name, [(x0, r0), (x1, r0), (x1, r1), (x0, r1)], origin)


def bolts(name, r, n, faces, origin=ENGINE):
    return flange_bolts(name, origin, X_AXIS, r, STUD, n, faces)


def ducted(name, stations, flanges):
    """S-duct with its end flanges and a passage cut where the shaft tunnel runs through its lower wall."""
    return [("duct", name, stations, WALL), *flanges,
            ("cut", f"{name}TunnelPassage", tube_profile(2010, 7510, 0, TUNNEL[1]))]


def spec():
    """[(sub-assembly or None, part label, finish, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    strut_tip = tip_radius(min(interp(C_OUTER, 755), interp(C_OUTER, 785)), 30, 8, 0)
    tail_tip = tip_radius(min(interp(NOZZLE_INNER, 8030), interp(NOZZLE_INNER, 8070)), 40, 8, 0)
    rv, rp = R_VESSEL, R_PLENUM
    return [
        ("intake", "nose_cone", "paint_grey", [  # static bullet carried by 4 inlet struts (px 5-28)
            ("spline", "NoseTip", [(0, 0), (150, 150), (400, 215), (750, 230)]),
            ("revolve", "NoseBody", [(750, 0), (790, 0), (790, 245), (750, 230)]),
            ("ring", "InletStruts", 770, 200, strut_tip, 30, 8, 4, 0)]),
        ("intake", "intake_lip", "machined_steel", [
            ("lathe", "IntakeLip", [(690, 612), (750, 600), (750, 650), (690, 640)], 12)]),

        ("compressor", "compressor_casing", "cast_alloy", [
            turned("CompCasing", [(750, 650), (1700, 650), (2000, 530), (2110, 530), *reversed(C_OUTER)]),
            flange("CompFrontFlange", 750, 780, 650, 710),
            flange("CompSplitFlange", 1425, 1485, 650, 710),
            flange("CompRearFlange", 2080, 2110, 530, 590)]),
        ("compressor", "compressor_bolts", "fastener", [
            *bolts("CompFront", 680, 36, [(780, 1)]), *bolts("CompSplit", 680, 36, [(1425, -1), (1485, 1)]),
            *bolts("CompRear", 560, 30, [(2080, -1)])]),
        ("compressor", "compressor_stators", "machined_steel", rows(COMPRESSOR, "S", C_OUTER, C_HUB)),

        # single spool: the shaft runs ~7 m under the reactor to the turbine
        ("rotor", "shaft", "dark_steel", [("revolve", "Shaft", tube_profile(800, 7880, 0, SHAFT_R))]),  # 20 mm clear of the tail cone
        ("rotor", "compressor_rotor", "machined_steel", rows(COMPRESSOR, "R", C_OUTER, C_HUB, SHAFT_R)),
        ("rotor", "turbine_rotor", "hot_alloy", rows(TURBINE, "R", T_OUTER, T_HUB, SHAFT_R)),

        ("reactor", "inlet_duct", "nozzle_alloy", ducted("InletDuct", INLET_DUCT, [
            flange("InletDuctFrontFlange", 2110, 2140, 500, 590),
            flange("InletDuctRearFlange", X_PLENUM - 30, X_PLENUM, rp - 30, rp + 70, REACTOR)])),
        ("reactor", "inlet_plenum", "paint_olive", [
            turned("Plenum", [(X_PLENUM, rp - WALL), (X_PLENUM, rp), (X_VESSEL, rp), (X_VESSEL, rp - WALL)], REACTOR),
            flange("PlenumFlange", X_PLENUM, X_PLENUM + 30, rp - 30, rp + 70, REACTOR)]),
        ("reactor", "pressure_vessel", "paint_olive", [
            turned("Vessel", [(X_VESSEL, rp), (3900, rv), (X_CLOSURE, rv), (X_CLOSURE, rv - WALL), (3900, rv - WALL),
                              (X_VESSEL, rp - WALL)], REACTOR),
            flange("VesselFrontFlange", 3900, 3960, rv, rv + 60, REACTOR),
            flange("VesselRearFlange", X_CLOSURE - 60, X_CLOSURE, rv, rv + 60, REACTOR),
            *[flange(f"VesselBand{i + 1}", x, x + 40, rv, rv + 25, REACTOR) for i, x in enumerate(BANDS)]]),
        ("reactor", "outlet_closure", "paint_olive", [
            turned("Closure", [(X_CLOSURE, rv), (X_OUTLET, R_OUTLET), (X_OUTLET, R_OUTLET - WALL), (X_CLOSURE, rv - WALL)],
                   REACTOR),
            flange("ClosureFlange", X_CLOSURE, X_CLOSURE + 30, rv - WALL, rv + 60, REACTOR)]),
        ("reactor", "control_drives", "machined_steel", [
            ("lathe", f"ControlDrive{i + 1}", [(rv, 0), (rv, 55), (rv + 210, 55), (rv + 210, 70), (rv + 260, 70), (rv + 260, 0)],
             6, (x, REACTOR_Y, 0), (0, 1, 0)) for i, x in enumerate(DRIVES)]),
        ("reactor", "reactor_core", "graphite", [  # core seated on end grids against the vessel wall
            ("offset_revolve", "Core", [(3950, 0), (3950, 700), (3980, 700), (3980, 660), (5570, 660),
                                        (5570, 700), (5600, 700), (5600, 0)], REACTOR_Y)]),
        ("reactor", "outlet_duct", "hot_alloy", ducted("OutletDuct", OUTLET_DUCT, [
            flange("OutletDuctFrontFlange", X_OUTLET, X_OUTLET + 30, R_OUTLET - 30, R_OUTLET + 70, REACTOR),
            flange("OutletDuctRearFlange", 7445, 7475, 620, 710)])),
        ("reactor", "reactor_bolts", "fastener", [
            *bolts("InletDuctFront", 560, 30, [(2140, 1)]),
            *bolts("PlenumJoint", rp + 37, 30, [(X_PLENUM - 30, -1), (X_PLENUM + 30, 1)], REACTOR),
            *bolts("VesselFront", rv + 30, 48, [(3900, -1), (3960, 1)], REACTOR),
            *bolts("VesselRear", rv + 30, 48, [(X_CLOSURE - 60, -1), (X_CLOSURE + 30, 1)], REACTOR),
            *bolts("OutletJoint", R_OUTLET + 38, 36, [(X_OUTLET + 30, 1)], REACTOR),
            *bolts("OutletDuctRear", 680, 36, [(7445, -1)])]),

        (None, "shaft_tunnel", "dark_steel", [  # static tunnel with fairings into the compressor and turbine hubs
            ("revolve", "Tunnel", [(2010, TUNNEL[0]), (7510, TUNNEL[0]), (7510, 330), (7475, 330),
                                   (7200, TUNNEL[1]), (2300, TUNNEL[1]), (2010, 360)])]),

        ("turbine", "turbine_casing", "hot_alloy", [
            turned("TurbCasing", [(7475, 650), (7960, 650), *reversed(T_OUTER)]),
            flange("TurbFrontFlange", 7475, 7505, 650, 710),
            flange("TurbRearFlange", 7930, 7960, 650, 710)]),
        ("turbine", "turbine_bolts", "fastener", [
            *bolts("TurbFront", 680, 36, [(7505, 1)]), *bolts("TurbRear", 680, 36, [(7930, -1)])]),
        ("turbine", "turbine_nozzles", "tint_bronze", rows(TURBINE, "S", T_OUTER, T_HUB)),
        ("turbine", "exhaust_nozzle", "nozzle_alloy", [
            turned("Nozzle", [(7960, 650), (8450, 560), *reversed(NOZZLE_INNER)]),
            flange("NozzleFlange", 7960, 7990, 615, 710)]),
        ("turbine", "exhaust_nozzle_bolts", "fastener", bolts("Nozzle", 680, 36, [(7990, 1)])),
        ("turbine", "tail_cone", "hot_alloy", [
            ("revolve", "TailCone", [(7900, 0), (7900, 360), (8100, 360), (8940, 0)]),
            ("ring", "TailStruts", 8050, 300, tail_tip, 40, 8, 4, 0)]),
    ]


SPEC = spec()
GROUPS = groups(SPEC)
MATERIALS = finishes(SPEC)


def parts():
    """[(label, colour, ops)] for assemble() and the native CAD builders."""
    return recipes(SPEC)


@glb(out="../GLB/lyulka_nuclear_turbojet.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/lyulka_nuclear_turbojet.stl")
@step(out="../STEP/lyulka_nuclear_turbojet.step", materials=MATERIALS)
def lyulka_nuclear_turbojet():
    return assemble(parts(), "lyulka_nuclear_turbojet", GROUPS)


if __name__ == "__main__":
    lyulka_nuclear_turbojet()
