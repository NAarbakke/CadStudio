"""Rocketdyne F-1 (Saturn V S-IC) rocket engine: thrust chamber, nozzle extension, turbopump, ducts, 12 parts.

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
  Not modelled: fuel inlet elbows, GG ducting, lines, wiring and insulation; the duct routing is simplified.
Axis = +X from the gimbal centre toward the nozzle exit (flow direction); the turbopump is at +Y.
"""
from cadgen import glb, step, stl
from lib.shapes import assemble, interp

IN = 25.4  # the sources are in inches; profiles below are written in inches and scaled once


def mm(points):
    return [(x * IN, r * IN) for x, r in points]


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

PUMP_Y = 50.0                      # turbopump axis offset (View B-B inlet centre 50.00 above the gimbal centre)
# turbopump (x along the engine axis, r about its own axis): LOX inlet, LOX volute Ø48, fuel pump Ø40,
# bearing / gear housing, two-stage turbine Ø42; 60 in long
PUMP = [(-9, 0), (-9, 8.5), (-2, 8.5), (-2, 13), (0, 20), (4, 24), (10, 24), (14, 20), (28, 20), (28, 14),
        (38, 14), (38, 18), (42, 21), (51, 21), (51, 0)]
MANIFOLD_X, MANIFOLD_R, MANIFOLD_TUBE = 141.5, 62.5, 7.0   # turbine exhaust manifold torus: Fig 2-22 7.00 radius arc
X_INJ = 6.0                        # injector back face: ~8 in thick (heroicrelics), the LOX dome bolts onto it
X_OXV = -4.5                       # oxidizer valves on the dome's horizontal inlet elbows (LOX dome/injector section)
# high-pressure ducts (x, y, z), mirrored to -Z: LOX volute outlet (x 7) and fuel volute outlet (x 17) at ±Z on the
# pump, across and down to the valves (R-3896-1 Fig 1-13 outlets, heroicrelics HP duct drawing; routing assumed)
OX_DUCT = [(7, PUMP_Y, 24.2), (7, PUMP_Y, 47), (X_OXV, 25, 47), (X_OXV, 0, 47), (X_OXV, 0, 40.2)]
FUEL_DUCT = [(17, PUMP_Y, 20.2), (17, PUMP_Y, 37), (17, 5.8, 37)]


def chamber_outer():
    """Tube-bundle outer surface: jacket to JACKET_END, then the gas contour offset by one tube."""
    wall = [(x, r + TUBE) for x, r in GAS if x > JACKET_END + 6]
    return [(X_FACE, JACKET_R), (JACKET_END, JACKET_R), (JACKET_END + 4, 19.2)] + wall


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    outer = chamber_outer()
    bands = [("revolve", f"Band{i + 1}", mm([(x, interp(outer, x) - 0.2), (x + 1.5, interp(outer, x + 1.5) - 0.2),
                                             (x + 1.5, interp(outer, x + 1.5) + 0.6), (x, interp(outer, x) + 0.6)]))
             for i, x in enumerate(range(42, 133, 10))]
    ext_in = [(X_EXIT + 1.5, R_EXIT), (180, 61.9), (X_NOZ, R_NOZ)]  # continues the bell at ~12.5 deg
    ext_out = [(x, r + 3.2) for x, r in ext_in]  # wall gap: outer skin reaches the Ø147 exit envelope
    hoops = [("revolve", f"Hoop{i + 1}", mm([(x, interp(ext_out, x)), (x + 1.2, interp(ext_out, x)),
                                             (x + 1.2, interp(ext_out, x) + 1.2), (x, interp(ext_out, x) + 1.2)]))
             for i, x in enumerate(range(160, 211, 10))]
    return [
        ("gimbal_bearing", "#B8BCC4", [
            ("revolve", "Gimbal", mm([(-14.5, 0), (-14.5, 9), (-6, 9), (-6, 12), (-3.5, 12), (-3.5, 0)]))]),
        ("oxidizer_dome", "#C9CED6", [  # flat-topped casting, ring manifold fed by two elbow inlets 180° apart
            ("revolve", "DomeBody", mm([(-3.5, 0), (-3.5, 15), (X_INJ, 15), (X_INJ, 13), (-1.5, 13), (-1.5, 0)])),
            ("torus", "LoxManifold", 1 * IN, 18.5 * IN, 4 * IN),
            ("revolve", "DomeFlange", mm([(4, 15), (X_INJ, 15), (X_INJ, 22.5), (4, 22.5)])),
            *[("pipe", f"OxidizerInlet{i + 1}", [(x * IN, 0, s * z * IN) for x, z in ((X_OXV, 26), (X_OXV, 21), (0, 19))],
               8 * IN) for i, s in enumerate((1, -1))]]),
        ("injector", "#B08D57", [  # Ø44 x 8 in injector; 13 compartments: centre baffle ring + 12 radial baffles
            ("revolve", "InjectorPlate", mm([(X_INJ, 0), (X_FACE, 0), (X_FACE, 22), (X_INJ, 22)])),
            ("revolve", "CentreBaffle", mm([(X_FACE, 8.7), (X_FACE + 3, 8.7), (X_FACE + 3, 9.3), (X_FACE, 9.3)])),
            ("ring", "RadialBaffles", (X_FACE + 1.5) * IN, 9 * IN, (R_CHAMBER - 0.2) * IN, 3 * IN, 0.6 * IN, 12, 0)]),
        ("thrust_chamber", "#5E5A55", [  # regeneratively cooled tube bundle to the 10:1 plane
            ("revolve", "TubeBundle", mm(outer + list(reversed(GAS)))),
            ("revolve", "ExitFlange", mm([(X_EXIT - 1.5, R_EXIT), (X_EXIT, R_EXIT), (X_EXIT, R_EXIT + 4.5),
                                          (X_EXIT - 1.5, R_EXIT + 4.5)])),  # with the fuel return manifold
            ("torus", "FuelInletManifold", 17 * IN, 26 * IN, 3 * IN),
            *bands,
            ("pins", "GimbalOutriggers", 40 * IN, 20 * IN, 44 * IN, 4 * IN, 2, 90),   # actuator attach, +-Z
            ("pins", "PumpOutriggerA", 30 * IN, 22 * IN, 40 * IN, 4 * IN, 1, 30),
            ("pins", "PumpOutriggerB", 30 * IN, 22 * IN, 40 * IN, 4 * IN, 1, -30)]),
        ("turbine_exhaust_manifold", "#8A8F96", [
            ("torus", "ExhaustManifold", MANIFOLD_X * IN, MANIFOLD_R * IN, MANIFOLD_TUBE * IN)]),
        ("nozzle_extension", "#3A3F47", [  # double-walled, turbine-exhaust film cooled, 10:1 -> 16:1
            ("revolve", "InnerWall", mm(ext_in + [(x, r + 0.3) for x, r in reversed(ext_in)])),
            ("revolve", "OuterWall", mm([(x, r - 0.3) for x, r in ext_out] + list(reversed(ext_out)))),
            ("revolve", "AttachFlange", mm([(X_EXIT, R_EXIT), (X_EXIT + 1.5, R_EXIT), (X_EXIT + 1.5, R_EXIT + 4.5),
                                            (X_EXIT, R_EXIT + 4.5)])),
            ("revolve", "ExitRing", mm([(X_NOZ - 1.5, R_NOZ), (X_NOZ, R_NOZ), (X_NOZ, 73.5), (X_NOZ - 1.5, 73.5)])),
            *hoops]),
        ("turbopump", "#9A7B4F", [("offset_revolve", "Turbopump", mm(PUMP), PUMP_Y * IN)]),
        ("heat_exchanger", "#7C8288", [  # turbine exhaust duct with the heat exchanger, Ø40 -> Ø24, to the manifold
            ("duct", "HeatExchanger", [(51 * IN, 50 * IN, 20 * IN), (70 * IN, 54 * IN, 19 * IN),
                                       (90 * IN, 58 * IN, 16 * IN), (110 * IN, 63 * IN, 13 * IN),
                                       (126 * IN, 67 * IN, 12 * IN), (134.3 * IN, 65 * IN, 11 * IN)], 0.3 * IN)]),
        ("gas_generator", "#D05A3A", [  # 18 x 24 x 28 in envelope beside the turbine
            ("axial_pins", "GGCombustor", 45 * IN, 48 * IN, 16 * IN, 24 * IN, 1, 40)]),
        ("oxidizer_valves", "#6B8FB0", [("pins", "OxidizerValves", X_OXV * IN, 26 * IN, 40 * IN, 17 * IN, 2, 90)]),
        ("fuel_valves", "#B0A06B", [("pins", "FuelValves", 20 * IN, 29 * IN, 45 * IN, 11 * IN, 2, 90)]),
        ("high_pressure_ducts", "#A8ADB4", [  # pump volute outlets to the valves (HP duct drawing), both sides
            *[("pipe", f"OxidizerDuct{i + 1}", [(x * IN, y * IN, s * z * IN) for x, y, z in OX_DUCT], 8 * IN)
              for i, s in enumerate((1, -1))],
            *[("pipe", f"FuelDuct{i + 1}", [(x * IN, y * IN, s * z * IN) for x, y, z in FUEL_DUCT], 6 * IN)
              for i, s in enumerate((1, -1))]]),
    ]


@glb(out="../GLB/f1.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/f1.stl")
@step(out="../STEP/f1.step")
def f1():
    return assemble(parts(), "f1")


if __name__ == "__main__":
    f1()
