"""Rocketdyne F-1 (Saturn V S-IC) rocket engine: thrust chamber, nozzle extension, turbopump, ducts.

42 parts in 8 sub-assemblies (GROUPS) plus the injector, turbine exhaust manifold and heat exchanger.

Sources (profile_builder/F1/resources/, dimensions in inches as published, converted to mm here):
  - R-3896-1 F-1 Technical Manual, Engine Data (Rocketdyne, 1967-72), Figure 2-22 Engine Envelope
    Dimensions: gimbal centre = datum, gimbal block to 14.50 above it, thrust chamber exit flange
    150.00 below it at Ø125.00, nozzle-extension exit 215.50 below it at Ø147.00, envelope R30.00 at
    62.50 (section A-A), turbopump envelope to 75.73 off-axis, turbine exhaust manifold radii 7.00-13.50.
  - Same manual, Figures 1-7/1-16 and paragraph text: throat area 961.4 in² (Ø35.0), expansion 10:1 at
    the chamber exit and 16:1 at the extension exit, 3:1 plane ~30 in below the throat, 178 primary /
    356 secondary tubes (Ø1.09 / Ø1.00), turbopump 5 ft long x 4 ft, heat exchanger Ø40 -> Ø24 x 58 in,
    gas generator envelope 18 x 24 x 28 in, valve inlets Ø8 (oxidizer) / Ø6 (fuel).
  - heroicrelics.org thrust chamber / injector pages: injector Ø44 in (39 in exposed to the chamber), ~8 in
    thick, thrust chamber ~11 ft long; "Injector Cross Section With LOX Dome" (flat-topped dome, ring manifold,
    two elbow inlets 180° apart); "Propellant High-Pressure Ducts" drawing (two oxidizer and two fuel ducts
    from the turbopump outlets to the valves); R-3896-1 Fig 1-13 (outlets on either side of the pump volutes).
  Not modelled: fuel inlet elbows, lines, wiring and insulation; the duct routing is simplified.
  Assumed for appearance, not taken from the sources: flange widths and thicknesses, bolt counts and sizes, corner
  radii, the split of the turbopump, valves and gas generator into housings and flanges, the fuel inlet stubs,
  the gas generator duct, the outrigger struts, and the finishes (lib/materials.py), including the heat-tint
  bands below the jacket. Fasteners are a nut and stud end standing on a flange face; no holes are cut.
Axis = +X from the gimbal centre toward the nozzle exit (flow direction); the turbopump is at +Y.
"""
from math import cos, radians, sin

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # models/, for the shared lib/

from cadgen import glb, step, stl
from lib.materials import colour, materials
from lib.shapes import assemble, flange_bolts, interp, segment

IN = 25.4  # the sources are in inches; profiles below are written in inches and scaled once


def mm(points):
    return [(x * IN, r * IN) for x, r in points]


def at(*xyz):
    """A point given in inches, in mm."""
    return tuple(c * IN for c in xyz)


def polar(x, r, angle):
    """(x, y, z) in inches at radius r, `angle` degrees about the engine axis from +Y toward +Z."""
    return x, r * cos(radians(angle)), r * sin(radians(angle))


def bezier(p0, p1, p2, n=16):
    """Quadratic Bezier (Rao thrust-optimised bell approximation) from p0 to p2 with control point p1."""
    return [tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2))
            for t in (i / n for i in range(n + 1))]


R_THROAT = 17.5                    # 961.4 in² throat area
X_FACE, R_CHAMBER = 14.0, 19.5     # injector face; Ø39 exposed injector
X_THROAT = 35.0                    # 3:1 plane ~30 in below the throat falls at ~x 65 (envelope R30 at 62.5)
X_EXIT, R_EXIT = 150.0, 55.33      # 10:1 plane = chamber exit flange (Fig 2-22)
X_NOZ, R_NOZ = 215.5, 70.0         # 16:1 plane = nozzle extension exit, Ø147 over its outer ring
TUBE = 1.1                         # Ø1.09 primary tubes: wall thickness of the tube bundle

# gas-side contour: chamber cylinder, convergent section, throat, bell (theta_n 27 deg -> theta_e 12.5 deg)
BELL = bezier((38.0, 18.24), (80.5, 39.5), (X_EXIT, R_EXIT))
GAS = [(X_FACE, R_CHAMBER), (24, R_CHAMBER), (28, 19.2), (31, 18.4), (33, 17.8), (X_THROAT, R_THROAT),
       (36.5, 17.66)] + BELL
JACKET_R, JACKET_END = 23.0, 32.0  # heavy jacket around the combustion chamber
JACKET_CONE = 36.0                 # the jacket closes onto the tube bundle here; heat tint from here to TINT_END
TINT_END, TINT = 48.0, ("tint_blue", "tint_purple", "tint_bronze", "tint_straw")   # hottest next to the throat

X_AXIS = (1, 0, 0)
BEVEL = ((0, 0, 0), X_AXIS, True)   # lathe arguments: on the engine axis, corners chamfered (large thin rings)
PUMP_Y = 50.0                      # turbopump axis offset (View B-B inlet centre 50.00 above the gimbal centre)
PUMP_AXIS = (0, PUMP_Y, 0)         # a point on the turbopump's own axis, which is parallel to the engine axis
GG_ANGLE, GG_R = 40, 48            # gas generator axis: parallel to the engine axis, beside the turbine
MANIFOLD_X, MANIFOLD_R, MANIFOLD_TUBE = 141.5, 62.5, 7.0   # turbine exhaust manifold torus: Fig 2-22 7.00 radius arc
X_INJ = 6.0                        # injector back face: ~8 in thick (heroicrelics), the LOX dome bolts onto it
X_OXV = -4.5                       # oxidizer valves on the dome's horizontal inlet elbows (LOX dome/injector section)
# high-pressure ducts (x, y, z), mirrored to -Z: LOX volute outlet (x 7) and fuel volute outlet (x 20) at ±Z on the
# pump, across and down to the valves (R-3896-1 Fig 1-13 outlets, heroicrelics HP duct drawing; routing assumed)
OX_DUCT = [(7, PUMP_Y, 24.2), (7, PUMP_Y, 47), (X_OXV, 25, 47), (X_OXV, 0, 47), (X_OXV, 0, 40.2)]
FUEL_DUCT = [(20, PUMP_Y, 20.2), (20, PUMP_Y, 37), (20, 4.25, 37)]


def chamber_outer():
    """Tube-bundle outer surface: jacket to JACKET_END, then the gas contour offset by one tube."""
    wall = [(x, r + TUBE) for x, r in GAS if x > JACKET_END + 6]
    return [(X_FACE, JACKET_R), (JACKET_END, JACKET_R), (JACKET_CONE, 19.2)] + wall


def foot(surface, x0, x1):
    """The stretch of an (x, r) surface table from x0 to x1."""
    return [(x0, interp(surface, x0))] + [p for p in surface if x0 < p[0] < x1] + [(x1, interp(surface, x1))]


def band(surface, x0, width, height):
    """(x, r) profile of a band standing on a surface table from x0, `height` proud of it at both ends."""
    base = foot(surface, x0, x0 + width)
    return base + [(x0 + width, base[-1][1] + height), (x0, base[0][1] + height)]


def bolts(name, origin, axis, r, size, n, faces):
    """flange_bolts() with every length in inches."""
    return flange_bolts(name, at(*origin), axis, r * IN, size * IN, n, [(a * IN, side) for a, side in faces])


def spec():
    """[(sub-assembly or None, part label, finish, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    outer = chamber_outer()
    ext_in = [(X_EXIT + 1.5, R_EXIT), (180, 61.9), (X_NOZ, R_NOZ)]  # continues the bell at ~12.5 deg
    ext_out = [(x, r + 3.2) for x, r in ext_in]  # wall gap: outer skin reaches the Ø147 exit envelope
    gg = polar(0, GG_R, GG_ANGLE)
    to_pump = (PUMP_Y - gg[1], -gg[2])                                # from the gas generator axis to the pump axis
    reach = 1 - 21.05 / (to_pump[0] ** 2 + to_pump[1] ** 2) ** 0.5    # the duct stops 0.05 short of the turbine (r 21)
    sides = ((1, 1), (2, -1))                                         # (number, sign of Z) for the two engine sides
    return [
        ("gimbal", "gimbal_block", "machined_steel", [
            ("lathe", "Gimbal", mm([(-14.5, 0), (-14.5, 9), (-6, 9), (-6, 12), (-3.5, 12), (-3.5, 0)]), 0.6 * IN)]),
        ("gimbal", "gimbal_bolts", "fastener", bolts("Gimbal", (0, 0, 0), X_AXIS, 10.6, 0.6, 16, [(-6, -1)])),

        # flat-topped casting, ring manifold fed by two elbow inlets 180° apart
        ("oxidizer_dome", "dome_casting", "cast_alloy", [
            ("lathe", "DomeBody", mm([(-3.5, 0), (-3.5, 15), (X_INJ, 15), (X_INJ, 13), (-1.5, 13), (-1.5, 0)]), 0.5 * IN),
            ("torus", "LoxManifold", 1 * IN, 18.5 * IN, 4 * IN),
            ("lathe", "DomeFlange", mm([(4, 15), (X_INJ, 15), (X_INJ, 23.5), (4, 23.5)]), 0.15 * IN, *BEVEL),
            *[("pipe", f"OxidizerInlet{i}", [at(x, 0, s * z) for x, z in ((X_OXV, 26), (X_OXV, 21), (0, 19))], 8 * IN)
              for i, s in sides]]),
        ("oxidizer_dome", "dome_bolts", "fastener",
         bolts("Dome", (0, 0, 0), X_AXIS, 22.8, 0.5, 48, [(4, -1), (X_INJ, 1)])),

        # Ø44 x 8 in injector; 13 compartments: centre baffle ring + 12 radial baffles
        (None, "injector", "copper", [
            ("revolve", "InjectorPlate", mm([(X_INJ, 0), (X_FACE, 0), (X_FACE, 22), (X_INJ, 22)])),
            ("revolve", "CentreBaffle", mm([(X_FACE, 8.7), (X_FACE + 3, 8.7), (X_FACE + 3, 9.3), (X_FACE, 9.3)])),
            ("ring", "RadialBaffles", (X_FACE + 1.5) * IN, 9 * IN, (R_CHAMBER - 0.2) * IN, 3 * IN, 0.6 * IN, 12, 0)]),

        # regeneratively cooled tube bundle to the 10:1 plane; the outriggers are welded to the jacket
        ("thrust_chamber", "chamber_jacket", "hot_alloy", [
            ("revolve", "Jacket", mm(segment(outer, GAS, X_FACE, JACKET_CONE))),
            *[op for i, s in sides for op in (
                ("pipe", f"GimbalOutrigger{i}", [at(*polar(28, 22, s * 90 - 25)), at(*polar(40, 44, s * 90)),
                                                 at(*polar(28, 22, s * 90 + 25))], 3 * IN),   # V strut to the actuator
                ("pin_circle", f"GimbalOutrigger{i}Lug", at(*polar(40, 45.5, s * 90)), X_AXIS, 0, 5 * IN, 2.4 * IN, 1),
                ("pins", f"PumpOutrigger{i}", 30 * IN, 22 * IN, 40 * IN, 4 * IN, 1, s * 30),
                ("pin_circle", f"PumpOutrigger{i}Lug", at(*polar(30, 40, s * 30)), X_AXIS, 0, 5.5 * IN, 3 * IN, 1))]]),
        *[("thrust_chamber", f"throat_tint_{i + 1}", finish, [
            ("revolve", f"Tint{i + 1}", mm(segment(outer, GAS, JACKET_CONE + 3 * i, JACKET_CONE + 3 * i + 3)))])
          for i, finish in enumerate(TINT)],
        ("thrust_chamber", "tube_bundle", "tube_bundle", [
            ("revolve", "TubeBundle", mm(segment(outer, GAS, TINT_END, X_EXIT)))]),
        ("thrust_chamber", "hatbands", "machined_steel", [
            ("lathe", f"Band{i + 1}", mm(band(outer, x, 1.5, 0.6)), 0.12 * IN, *BEVEL) for i, x in enumerate(range(42, 133, 10))]),
        ("thrust_chamber", "fuel_inlet_manifold", "cast_alloy", [("torus", "FuelInletManifold", 17 * IN, 26 * IN, 3 * IN)]),
        ("thrust_chamber", "exit_flange", "machined_steel", [  # with the fuel return manifold
            ("lathe", "ExitFlange", mm(foot(outer, X_EXIT - 1.5, X_EXIT) + [(X_EXIT, R_EXIT + 4.5),
                                                                             (X_EXIT - 1.5, R_EXIT + 4.5)]), 0.2 * IN, *BEVEL)]),
        ("thrust_chamber", "exit_flange_bolts", "fastener",
         bolts("ExitFlange", (0, 0, 0), X_AXIS, 58.3, 0.55, 90, [(X_EXIT - 1.5, -1)])),

        (None, "turbine_exhaust_manifold", "hot_alloy", [
            ("torus", "ExhaustManifold", MANIFOLD_X * IN, MANIFOLD_R * IN, MANIFOLD_TUBE * IN)]),

        # double-walled, turbine-exhaust film cooled, 10:1 -> 16:1
        ("nozzle_extension", "extension_shell", "nozzle_alloy", [
            ("revolve", "InnerWall", mm(ext_in + [(x, r + 0.3) for x, r in reversed(ext_in)])),
            ("revolve", "OuterWall", mm([(x, r - 0.3) for x, r in ext_out] + list(reversed(ext_out)))),
            ("lathe", "AttachFlange", mm([(X_EXIT, R_EXIT), (X_EXIT + 1.5, R_EXIT), (X_EXIT + 1.5, R_EXIT + 4.5),
                                          (X_EXIT, R_EXIT + 4.5)]), 0.2 * IN, *BEVEL),
            ("lathe", "ExitRing", mm([(X_NOZ - 1.5, R_NOZ), (X_NOZ, R_NOZ), (X_NOZ, 73.5), (X_NOZ - 1.5, 73.5)]), 0.2 * IN, *BEVEL)]),
        ("nozzle_extension", "extension_hoops", "machined_steel", [
            ("lathe", f"Hoop{i + 1}", mm(band(ext_out, x, 1.2, 1.2)), 0.15 * IN, *BEVEL) for i, x in enumerate(range(160, 211, 10))]),

        # turbopump on its own axis (a = engine x): LOX inlet, LOX volute Ø48, fuel pump Ø40 with two inlet stubs,
        # bearing / gear housing, two-stage turbine with the flange to the heat exchanger
        ("turbopump", "lox_inlet", "cast_alloy", [
            ("lathe", "LoxInlet", mm([(-9, 7.3), (-9, 10.5), (-8, 10.5), (-8, 8.5), (-2, 8.5), (-2, 0), (-4, 0), (-4, 7.3)]),
             0.4 * IN, at(*PUMP_AXIS))]),
        ("turbopump", "lox_inlet_bolts", "fastener", bolts("LoxInlet", PUMP_AXIS, X_AXIS, 9.6, 0.5, 24, [(-8, 1)])),
        ("turbopump", "lox_volute", "cast_alloy", [
            ("lathe", "LoxVolute", mm([(-2, 0), (-2, 13), (0, 20), (4, 24), (10, 24), (14, 20), (14, 0)]), 2 * IN,
             at(*PUMP_AXIS))]),
        ("turbopump", "fuel_volute", "cast_alloy", [
            ("lathe", "FuelVolute", mm([(14, 0), (14, 20), (28, 20), (28, 0)]), 1.5 * IN, at(*PUMP_AXIS)),
            *[("lathe", f"FuelInlet{i}", mm([(12, 0), (12, 5), (29, 5), (29, 6.5), (30, 6.5), (30, 0)]), 0.3 * IN,
               at(21, PUMP_Y, 0), (0, 0.5, s * 0.866)) for i, s in sides]]),
        ("turbopump", "fuel_inlet_bolts", "fastener", [
            op for i, s in sides
            for op in bolts(f"FuelInlet{i}", (21, PUMP_Y, 0), (0, 0.5, s * 0.866), 5.8, 0.4, 16, [(29, -1)])]),
        ("turbopump", "bearing_housing", "machined_steel", [
            ("lathe", "BearingHousing", mm([(28, 0), (28, 16.5), (29, 16.5), (29, 14), (37, 14), (37, 16.5), (38, 16.5),
                                           (38, 0)]), 0.3 * IN, at(*PUMP_AXIS))]),
        ("turbopump", "bearing_housing_bolts", "fastener",
         bolts("BearingHousing", PUMP_AXIS, X_AXIS, 15.3, 0.5, 30, [(29, 1), (37, -1)])),
        ("turbopump", "turbine", "hot_alloy", [
            ("lathe", "Turbine", mm([(38, 0), (38, 18), (42, 21), (49.5, 21), (49.5, 22.8), (51, 22.8), (51, 0)]), 0.5 * IN,
             at(*PUMP_AXIS))]),
        ("turbopump", "turbine_bolts", "fastener", bolts("Turbine", PUMP_AXIS, X_AXIS, 22.05, 0.5, 36, [(49.5, -1)])),

        (None, "heat_exchanger", "hot_alloy", [  # turbine exhaust duct with the heat exchanger, Ø40 -> Ø24, to the manifold
            ("duct", "HeatExchanger", [(51 * IN, 50 * IN, 20 * IN), (70 * IN, 54 * IN, 19 * IN),
                                       (90 * IN, 58 * IN, 16 * IN), (110 * IN, 63 * IN, 13 * IN),
                                       (126 * IN, 67 * IN, 12 * IN), (134.3 * IN, 65 * IN, 11 * IN)], 0.3 * IN)]),

        # 18 x 24 x 28 in envelope beside the turbine: injector head, flange, combustor, outlet neck, duct to the turbine
        ("gas_generator", "gg_combustor", "hot_alloy", [
            ("lathe", "GGCombustor", mm([(33, 0), (33, 5), (37, 5), (37, 8), (39, 8), (39, 6.8), (51, 6.8), (54, 4.5),
                                        (57, 4.5), (57, 0)]), 0.6 * IN, at(*gg)),
            ("pipe", "GGDuct", [at(45, gg[1], gg[2]), at(45, gg[1] + to_pump[0] * reach, gg[2] + to_pump[1] * reach)],
             6 * IN)]),
        ("gas_generator", "gg_bolts", "fastener", bolts("GG", gg, X_AXIS, 7.45, 0.4, 20, [(37, -1)])),

        # flanged valve bodies in line with the dome inlets (oxidizer) and on the fuel inlet manifold, with actuators
        *[("valves", f"oxidizer_valve_{i}", "machined_steel", [
            ("lathe", f"OxidizerValve{i}", mm([(26, 0), (26, 8.6), (27.2, 8.6), (27.2, 6.5), (38.8, 6.5), (38.8, 8.6),
                                               (40, 8.6), (40, 0)]), 0.3 * IN, at(X_OXV, 0, 0), (0, 0, s)),
            ("pin_circle", f"OxidizerActuator{i}", at(X_OXV, -9.5, s * 33), (0, 1, 0), 0, 6 * IN, 9 * IN, 1)])
          for i, s in sides],
        ("valves", "oxidizer_valve_bolts", "fastener", [
            op for i, s in sides
            for op in bolts(f"OxidizerValve{i}", (X_OXV, 0, 0), (0, 0, s), 7.6, 0.55, 16, [(27.2, 1), (38.8, -1)])]),
        *[("valves", f"fuel_valve_{i}", "machined_steel", [
            ("lathe", f"FuelValve{i}", mm([(29, 0), (29, 5.5), (30, 5.5), (30, 4.2), (44, 4.2), (44, 5.5), (45, 5.5),
                                           (45, 0)]), 0.2 * IN, at(20, 0, 0), (0, 0, s)),
            ("pin_circle", f"FuelActuator{i}", at(20, -6.5, s * 37), (0, 1, 0), 0, 4 * IN, 6 * IN, 1)])
          for i, s in sides],
        ("valves", "fuel_valve_bolts", "fastener", [
            op for i, s in sides
            for op in bolts(f"FuelValve{i}", (20, 0, 0), (0, 0, s), 4.85, 0.35, 12, [(30, 1), (44, -1)])]),

        # pump volute outlets to the valves (HP duct drawing), both sides, with a flange at each pump outlet
        *[("high_pressure_ducts", f"oxidizer_duct_{i}", "machined_steel", [
            ("pipe", f"OxidizerDuct{i}", [at(x, y, s * z) for x, y, z in OX_DUCT], 8 * IN)]) for i, s in sides],
        *[("high_pressure_ducts", f"fuel_duct_{i}", "machined_steel", [
            ("pipe", f"FuelDuct{i}", [at(x, y, s * z) for x, y, z in FUEL_DUCT], 6 * IN)]) for i, s in sides],
        ("high_pressure_ducts", "duct_flanges", "machined_steel", [
            op for i, s in sides for op in (
                ("lathe", f"OxidizerDuctFlange{i}", mm([(25, 4), (25, 5.8), (26.2, 5.8), (26.2, 4)]), 0.15 * IN,
                 at(7, PUMP_Y, 0), (0, 0, s)),
                ("lathe", f"FuelDuctFlange{i}", mm([(21, 3), (21, 4.6), (22, 4.6), (22, 3)]), 0.15 * IN,
                 at(20, PUMP_Y, 0), (0, 0, s)))]),
        ("high_pressure_ducts", "duct_flange_bolts", "fastener", [
            op for i, s in sides for op in (
                *bolts(f"OxidizerDuct{i}", (7, PUMP_Y, 0), (0, 0, s), 4.95, 0.5, 12, [(25, -1), (26.2, 1)]),
                *bolts(f"FuelDuct{i}", (20, PUMP_Y, 0), (0, 0, s), 3.85, 0.4, 10, [(21, -1), (22, 1)]))]),
    ]


SPEC = spec()
GROUPS = {}
for _group, _label, _finish, _ops in SPEC:
    if _group:
        GROUPS.setdefault(_group, []).append(_label)
MATERIALS = materials({label: finish for _, label, finish, _ in SPEC})


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    return [(label, colour(finish), ops) for _, label, finish, ops in SPEC]


@glb(out="../GLB/rocketdyne_f1.glb", mesh_tolerance=6e-4, mesh_angular_tolerance=0.25)
@stl(out="../STL/rocketdyne_f1.stl")
@step(out="../STEP/rocketdyne_f1.step", materials=MATERIALS)
def rocketdyne_f1():
    return assemble(parts(), "rocketdyne_f1", GROUPS)


if __name__ == "__main__":
    rocketdyne_f1()
