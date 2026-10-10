"""Recipe builder shared by the three SpaceX Raptor models (op format: lib/shapes.py). Units mm.

Axis = +X from the top of the engine toward the nozzle exit. Layout read from the photographs in
profile_builder/Raptor/ (README.md there lists what was measured): the oxygen inlet, pump and preburner
stand on the chamber axis; below them the main injector carries a wide hot-gas manifold disc; the methane
turbopump hangs under that disc beside the chamber, on PUMP; the coolant manifold sits just below the
throat at the top of a short, wide bell. spec() takes what differs between the versions: the throat
radius, the top of the engine, the finishes, which joints are bolted or welded, how the methane pump
feeds the coolant manifold, and what dresses the outside: valves, small lines, engine controllers with
their wiring, the oxygen line, igniter and sensor ports.

From published figures: 3.1 m long, Ø1.3 m exit, 34.34:1 sea-level expansion on the Raptor 1 throat.
From the photographs (about ±5 %): the axial stations and diameters of the main masses. Assumed for
appearance: housing shapes, duct routing and diameters, the number and routing of lines and wiring,
controller and actuator sizes, flange and bolt sizes, corner radii, wall thicknesses and the heat-tint bands.
"""
from math import cos, radians, sin, sqrt, tan

from lib.shapes import flange_bolts, interp, segment

X_AXIS = (1, 0, 0)
BEVEL = ((0, 0, 0), X_AXIS, True)       # lathe arguments: on the engine axis, corners chamfered (large thin rings)
X_EXIT, R_EXIT = 3100.0, 650.0          # overall length and exit diameter (outside the exit ring)
R_GAS_EXIT, WALL = 628.0, 12.0          # gas-side exit radius and nozzle wall
X_PUMP, X_PREBURNER, X_DISC, X_INJ = 600.0, 800.0, 1000.0, 1215.0   # on-axis stack: stations of the joints
R_VOLUTE = 240.0                        # oxygen pump volute
R_DISC = 435.0                          # hot-gas manifold disc, Ø870 (photographs)
R_INJ, R_WAIST = 265.0, 232.0           # main injector flanges, Ø530 (photographs: Ø520), and the waist between them
X_FACE, R_CHAMBER, JACKET_R = 1335.0, 185.0, 215.0   # injector face, chamber bore, jacket Ø430 (photographs)
X_THROAT = 1690.0                       # 55 % of the length from the top (photographs)
JACKET_END, JACKET_CONE = 1570.0, 1650.0
TINT = ("tint_blue", "tint_purple", "tint_bronze", "tint_straw")   # hottest next to the throat
TINT_STEP = 35.0
X_MANIFOLD, MANIFOLD_TUBE = 1880.0, 52.0   # coolant inlet manifold at the top of the bell (photographs)
X_COLLECTOR, COLLECTOR_TUBE = 1415.0, 30.0  # coolant outlet collector around the chamber
PUMP = (0.0, 400.0, 0.0)                # a point on the methane turbopump axis (photographs: ~370 off the axis)
X_TURBINE, X_FUEL_PB, X_FUEL_PUMP, X_PUMP_END = 1175.0, 1335.0, 1495.0, 1700.0   # methane stack, top to bottom
R_STACK, R_FUEL_PB = 125.0, 100.0       # largest radius of the methane turbopump; its preburner body
FEED_ANGLE, FEED_R = -40.0, 520.0       # methane inlet duct: degrees about the axis from +Y toward +Z, radius
LINE_ANGLE, LINE_R = 20.0, 480.0        # preburner oxygen line
WRAP_X, WRAP_R = 1590.0, 340.0          # pump discharge duct wrapped around the chamber
X_LINE_END = 1275.0                     # small lines and wiring end in the injector waist, between the stud rings
BOX = (640.0, 780.0, 370.0, 180.0)      # engine controller: x0, x1, outer radius, width
LOOK = {"body": "cast_alloy", "hot": "hot_alloy", "duct": "machined_steel", "nozzle": "nozzle_alloy", "tint": True}


def bezier(p0, p1, p2, n=16):
    return [tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2))
            for t in (i / n for i in range(n + 1))]


def gas_contour(r_throat):
    """Gas-side (x, r): chamber, convergent section, throat, bell from 38 deg at the throat to 8 deg at the exit."""
    start, t_n, t_e = (X_THROAT + 25, r_throat + 7), tan(radians(38)), tan(radians(8))
    x_c = (R_GAS_EXIT - t_e * X_EXIT - start[1] + t_n * start[0]) / (t_n - t_e)   # where the two tangents meet
    bell = bezier(start, (x_c, start[1] + t_n * (x_c - start[0])), (X_EXIT, R_GAS_EXIT))
    return [(X_FACE, R_CHAMBER), (1560, R_CHAMBER), (1610, 165), (1650, r_throat + 28), (1675, r_throat + 7),
            (X_THROAT, r_throat), (1705, r_throat + 2)] + bell


def outer_contour(gas):
    """Outside of the chamber and nozzle: jacket, then the gas contour plus a wall thinning from 28 to WALL."""
    def wall(x):
        return interp([(JACKET_CONE, 28), (1900, WALL)], x)
    return ([(X_FACE, JACKET_R), (JACKET_END, JACKET_R), (JACKET_CONE, interp(gas, JACKET_CONE) + 28)]
            + [(x, r + wall(x)) for x, r in gas if x > JACKET_CONE + 1])


def foot(surface, x0, x1):
    """The stretch of an (x, r) surface table from x0 to x1."""
    return [(x0, interp(surface, x0))] + [p for p in surface if x0 < p[0] < x1] + [(x1, interp(surface, x1))]


def spool(a0, a1, r, flanged=True, lip=28.0, thick=22.0):
    """(a, r) profile of a solid housing of radius r from a0 to a1, with a bolting flange at each end if flanged."""
    if not flanged:
        return [(a0, 0), (a0, r), (a1, r), (a1, 0)]
    return [(a0, 0), (a0, r + lip), (a0 + thick, r + lip), (a0 + thick, r), (a1 - thick, r), (a1 - thick, r + lip),
            (a1, r + lip), (a1, 0)]


def bolts(name, origin, r, n, faces, size=10.0):
    return flange_bolts(name, origin, X_AXIS, r, size, n, faces)


def polar(r, angle):
    """(y, z) at radius r, `angle` degrees about the engine axis from +Y toward +Z."""
    return r * cos(radians(angle)), r * sin(radians(angle))


def away(origin, target, d):
    """The (y, z) point `d` from origin on the way to target."""
    v = (target[0] - origin[0], target[1] - origin[1])
    k = d / sqrt(v[0] ** 2 + v[1] ** 2)
    return origin[0] + v[0] * k, origin[1] + v[1] * k


def lane(angle, radius, x0, x1, r0, r1):
    """Path of a line that leaves radius r0 at x0, runs along the engine at `radius` and turns in to r1 at x1."""
    return [(x0, *polar(r0, angle)), (x0, *polar(radius, angle)), (x1, *polar(radius, angle)), (x1, *polar(r1, angle))]

def sleeve(name, origin, a0, a1, r_pipe):
    """Valve body around a duct of radius r_pipe along X: it touches the duct without cutting into it."""
    return ("lathe", name, [(a0, r_pipe), (a0, r_pipe + 30), (a1, r_pipe + 30), (a1, r_pipe)], 5, origin, X_AXIS)


def top_gimbal(look):
    """Raptor 1: square mount plate and gimbal block on a conical thrust frame down to the oxygen pump."""
    return [
        ("engine_top", "mount_plate", "machined_steel", [
            ("fins", "MountPlate", [(0, -260), (40, -260), (40, 260), (0, 260)], 520, 1)]),
        ("engine_top", "gimbal_block", "machined_steel", [
            ("lathe", "GimbalBlock", [(40, 0), (40, 160), (200, 160), (230, 110), (330, 110), (330, 0)], 12)]),
        ("engine_top", "thrust_frame", "dark_steel", [
            ("lathe", "ThrustFrame", [(330, 80), (330, 150), (350, 150), (350, 112), (575, 195), (575, 225), (X_PUMP, 225),
                                      (X_PUMP, 175), (580, 175), (350, 80)], 4, *BEVEL),
            ("fins", "FrameRibs", [(352, 113), (573, 196), (573, 222), (352, 148)], 14, 8, 22.5)]),
        ("engine_top", "engine_top_bolts", "fastener", [
            *bolts("MountPlate", (0, 0, 0), 225, 12, [(40, 1)]), *bolts("ThrustFrame", (0, 0, 0), 210, 24, [(575, -1)])]),
    ]


def top_bellows(look):
    """Raptor 2: oxygen inlet bellows on the axis, on a housing down to the oxygen pump."""
    ribs = [p for x in range(30, 230, 20) for p in ((x, 105), (x + 5, 118), (x + 10, 118), (x + 15, 105))]
    return [
        ("engine_top", "oxygen_inlet", "machined_steel", [
            ("revolve", "InletBellows", [(0, 0), (0, 105), *ribs, (240, 105), (240, 150), (275, 150), (275, 0)])]),
        ("engine_top", "inlet_housing", look["body"], [
            ("lathe", "InletHousing", [(275, 0), (275, 150), (420, 150), (460, 225), (X_PUMP, 225), (X_PUMP, 0)], 10),
            ("pins", "HousingBosses", 350, 145, 185, 70, 6, 30)]),
        ("engine_top", "engine_top_bolts", "fastener", bolts("InletBellows", (0, 0, 0), 132, 16, [(240, -1)])),
    ]


def top_flange(look):
    """Raptor 3: flanged oxygen inlet on the axis, studded onto a plain housing with round bosses."""
    return [
        ("engine_top", "oxygen_inlet", "machined_steel", [
            ("lathe", "InletSpool", [(0, 0), (0, 115), (25, 115), (25, 100), (135, 100), (135, 115), (160, 115), (160, 0)], 3)]),
        ("engine_top", "inlet_housing", look["body"], [
            ("lathe", "InletHousing", [(160, 0), (160, 190), (195, 190), (195, 160), (520, 160), (560, 225), (X_PUMP, 225),
                                       (X_PUMP, 0)], 10),
            ("pins", "HousingBosses", 300, 155, 195, 90, 6, 30), ("pins", "HousingPlugs", 430, 155, 180, 50, 6, 0)]),
        ("engine_top", "engine_top_bolts", "fastener", bolts("InletSpool", (0, 0, 0), 150, 20, [(160, -1)])),
    ]


def spec(r_throat, top, look=LOOK, bolted=(), welded=(), feed="wrap", valves=(), ports=False, igniter=False,
         lox_line=True, lines=(), controllers=(), actuator=False, service_line=False):
    """[(sub-assembly or None, part label, finish, ops)] for one Raptor version.

    top: top_gimbal, top_bellows or top_flange. look: finishes by role (see LOOK). bolted: joints that carry
    a bolt circle, from {"disc", "preburners", "injector", "inlet"}. welded: joints made without flanges,
    from {"preburners", "injector"}. feed: "wrap" runs the pump discharge around the chamber to the far
    side of the coolant manifold, "elbow" drops it straight in. valves: from {"fuel", "discharge"}.
    lines: angles (degrees about the axis) of small lines from the oxygen pump past the disc to the
    injector. controllers: angles of engine controller boxes on the oxygen pump, each with a wiring
    harness to the injector. actuator: valve actuator on the oxygen preburner. service_line: one thin line
    from the inlet housing to the methane turbine (Raptor 3).
    """
    weld_pb, weld_inj = "preburners" in welded, "injector" in welded
    gas = gas_contour(r_throat)
    outer = outer_contour(gas)
    stack = PUMP[1:]
    r_ox_pb = 200 if weld_pb else 190

    slope = (interp(outer, X_MANIFOLD + 20) - interp(outer, X_MANIFOLD - 20)) / 40
    r_ring = interp(outer, X_MANIFOLD) + MANIFOLD_TUBE * sqrt(1 + slope ** 2) + 2   # torus clear of the sloping wall
    leg = polar(WRAP_R + 15, 180)                                      # where the wrapped duct turns down
    if feed == "wrap":   # pump side, round the chamber (corners at 60 and 120 degrees, swept to WRAP_R), down into the manifold
        corners = [polar(WRAP_R / cos(radians(30)), a) for a in (60, 120)]
        discharge = ([(WRAP_X, *p) for p in (away(stack, corners[0], R_STACK + 1), *corners, leg)] + [(X_MANIFOLD, *leg)], WRAP_R)
    else:                # straight down from the pump's lower end onto the manifold
        discharge = None
    inlet = polar(FEED_R, FEED_ANGLE)                                  # methane inlet duct, down past the disc
    line = polar(LINE_R, LINE_ANGLE)

    parts = [
        *top(look),

        ("oxygen_powerhead", "oxygen_pump", look["body"], [
            ("lathe", "OxygenPump", [(X_PUMP, 0), (X_PUMP, 225), (622, 225), (622, 205), (650, R_VOLUTE), (760, R_VOLUTE),
                                     (X_PREBURNER, 200), (X_PREBURNER, 0)], 8)]),
        ("oxygen_powerhead", "oxygen_preburner", look["hot"], [
            ("lathe", "OxygenPreburner", spool(X_PREBURNER, X_DISC, r_ox_pb, not weld_pb, 32), 5)]),
        ("oxygen_powerhead", "hot_gas_manifold", look["body"], [   # the wide disc on the main injector
            ("lathe", "HotGasManifold", [(X_DISC, 0), (X_DISC, 250), (1050, 250), (1050, R_DISC), (1170, R_DISC),
                                         (1170, R_INJ), (X_INJ, R_INJ), (X_INJ, 0)], 30)]),
        ("oxygen_powerhead", "main_injector", look["duct"], [
            ("lathe", "Injector", [(X_INJ, 0), (X_INJ, R_INJ), (1260, R_INJ), (1300, 240), (X_FACE, 240), (X_FACE, 0)], 12) if weld_inj
            else ("lathe", "Injector", [(X_INJ, 0), (X_INJ, R_INJ), (1250, R_INJ), (1250, R_WAIST), (1300, R_WAIST),
                                        (1300, R_INJ), (X_FACE, R_INJ), (X_FACE, 0)], 5)]),

        # methane turbopump under the disc: turbine on top (its exhaust goes up into the disc), pump at the bottom
        ("methane_powerhead", "methane_turbine", look["hot"], [
            ("lathe", "MethaneTurbine", [(X_TURBINE, 0), (X_TURBINE, 105), (1200, R_STACK), (1300, R_STACK),
                                         (X_FUEL_PB, 105), (X_FUEL_PB, 0)], 12, PUMP),
            ("lathe", "HotGasNeck", [(1171, 0), (1171, 60), (1180, 60), (1180, 0)], 0, PUMP)]),
        ("methane_powerhead", "methane_preburner", look["hot"], [
            ("lathe", "MethanePreburner", spool(X_FUEL_PB, X_FUEL_PUMP, R_FUEL_PB, not weld_pb), 5, PUMP)]),
        ("methane_powerhead", "methane_pump", look["body"], [
            ("lathe", "MethanePump", [(X_FUEL_PUMP, 0), (X_FUEL_PUMP, 105), (1520, R_STACK), (1660, R_STACK),
                                      (X_PUMP_END, 90), (X_PUMP_END, 0)], 12, PUMP)]),
        ("methane_powerhead", "methane_inlet", look["duct"], [   # from the vehicle, past the disc, into the pump
            ("sweep", "MethaneInlet", [(450, *inlet), (1600, *inlet), (1600, *away(stack, inlet, R_STACK + 1))], 100, 120),
            ("lathe", "MethaneInletFlange", [(450, 50), (450, 85), (475, 85), (475, 50)], 3, (0, *inlet))]),

        # regeneratively cooled chamber and nozzle; the gimbal actuator lugs are on the jacket
        ("thrust_chamber", "chamber_jacket", look["duct"], [
            ("revolve", "Jacket", segment(outer, gas, X_FACE, JACKET_CONE)),
            *([] if weld_inj else [("lathe", "JacketFlange", [(X_FACE, JACKET_R), (X_FACE, R_INJ), (1370, R_INJ),
                                                              (1370, JACKET_R)], 3, *BEVEL)]),
            ("pins", "ActuatorLugs", 1500, JACKET_R - 5, 290, 50, 2, 120)]),
        ("thrust_chamber", "coolant_collector", look["body"], [   # coolant leaves the jacket here for the preburner
            ("torus", "CoolantCollector", X_COLLECTOR, JACKET_R + COLLECTOR_TUBE, COLLECTOR_TUBE),
            ("pipe", "CollectorOutlet", [(X_COLLECTOR, JACKET_R + COLLECTOR_TUBE, 0),
                                         (X_COLLECTOR, stack[0] - R_FUEL_PB - 1, 0)], 50)]),
        *([("thrust_chamber", f"throat_tint_{i + 1}", finish, [
            ("revolve", f"Tint{i + 1}", segment(outer, gas, JACKET_CONE + TINT_STEP * i, JACKET_CONE + TINT_STEP * (i + 1)))])
           for i, finish in enumerate(TINT)] if look["tint"] else
          [("thrust_chamber", "throat", look["nozzle"], [
              ("revolve", "Throat", segment(outer, gas, JACKET_CONE, JACKET_CONE + TINT_STEP * len(TINT)))])]),
        ("thrust_chamber", "nozzle_upper", look["hot"], [
            ("revolve", "NozzleUpper", segment(outer, gas, JACKET_CONE + TINT_STEP * len(TINT), X_MANIFOLD))]),
        ("thrust_chamber", "nozzle_skirt", look["nozzle"], [
            ("revolve", "NozzleSkirt", segment(outer, gas, X_MANIFOLD, X_EXIT))]),
        ("thrust_chamber", "coolant_manifold", look["body"], [   # fed by the methane pump discharge duct
            ("torus", "CoolantManifold", X_MANIFOLD, r_ring, MANIFOLD_TUBE),
            ("sweep", "PumpDischarge", discharge[0], 100, discharge[1]) if discharge
            else ("pipe", "PumpDischarge", [(X_PUMP_END + 1, *stack), (X_MANIFOLD, *stack)], 100)]),
        ("thrust_chamber", "exit_ring", look["duct"], [
            ("lathe", "ExitRing", foot(outer, X_EXIT - 40, X_EXIT) + [(X_EXIT, R_EXIT), (X_EXIT - 40, R_EXIT)], 3, *BEVEL)]),
    ]

    def add(group, label, finish, ops):
        parts.append((group, label, finish, ops))

    if lox_line:   # oxygen pump volute, past the disc, to the methane preburner
        add("ducts_and_valves", "preburner_oxygen_line", look["duct"], [
            ("sweep", "PreburnerOxygen", [(700, *polar(R_VOLUTE + 1, LINE_ANGLE)), (700, *line), (X_COLLECTOR, *line),
                                          (X_COLLECTOR, *away(stack, line, R_FUEL_PB + 1))], 50, 60)])
    if "fuel" in valves:
        t = (sin(radians(FEED_ANGLE)), -cos(radians(FEED_ANGLE)))   # across the inlet duct
        add("ducts_and_valves", "main_fuel_valve", "machined_steel", [
            sleeve("FuelValve", (0, *inlet), 800, 930, 50),
            ("pin_circle", "FuelActuator", (865, inlet[0] + 110 * t[0], inlet[1] + 110 * t[1]), (0, *t), 0, 60, 110, 1)])
    if "discharge" in valves and feed == "wrap":
        add("ducts_and_valves", "discharge_valve", "machined_steel", [
            sleeve("DischargeValve", (0, *leg), 1740, 1820, 50),
            ("pin_circle", "DischargeActuator", (1780, leg[0] - 110, 0), (0, 1, 0), 0, 60, 110, 1)])
    if actuator:   # stands 1 mm off the oxygen preburner body
        add("ducts_and_valves", "oxygen_valve_actuator", "machined_steel", [
            ("pins", "OxygenActuator", 900, r_ox_pb + 1, 300, 70, 1, 100),
            ("pins", "OxygenActuatorCap", 900, 300, 318, 90, 1, 100)])
    if lines:      # from the oxygen pump volute, outside the disc, into the injector waist
        add("ducts_and_valves", "small_lines", "fastener", [
            ("sweep", f"Line{i + 1}", lane(a, 450 + 20 * (i % 2), 670 + 25 * (i % 3), X_LINE_END, R_VOLUTE + 1, R_WAIST + 1), 16, 40)
            for i, a in enumerate(lines)])
    if controllers:
        x0, x1, r_out, width = BOX
        add("ducts_and_valves", "engine_controllers", "paint_grey", [
            ("fins", f"Controller{i + 1}", [(x0, R_VOLUTE + 2), (x1, R_VOLUTE + 2), (x1, r_out), (x0, r_out)], width, 1, a)
            for i, a in enumerate(controllers)])
        add("ducts_and_valves", "wiring_harness", "radome", [
            ("sweep", f"Harness{i + 1}", lane(a, 475, (x0 + x1) / 2, X_LINE_END, r_out + 1, R_WAIST + 1), 24, 50)
            for i, a in enumerate(controllers)])
    if service_line:
        tube = polar(450, 25)
        add("ducts_and_valves", "service_line", "fastener", [
            ("sweep", "ServiceLine", [(300, *polar(197, 25)), (300, *tube), (1240, *tube),
                                      (1240, *away(stack, tube, R_STACK + 1))], 16, 60)])
    if ports:
        add("ducts_and_valves", "sensor_ports", "brass", [
            ("pins", "InjectorPorts", X_LINE_END, R_WAIST, R_INJ - 5, 16, 8, 22.5),
            ("pins", "JacketPorts", 1465, JACKET_R, 240, 20, 12, 15)])
    if igniter:
        add("ducts_and_valves", "torch_igniter", "brass", [
            ("lathe", "Igniter", [(R_DISC + 1, 0), (R_DISC + 1, 22), (500, 22), (500, 30), (520, 30), (520, 0)], 3,
             (1110, 0, 0), (0, -1, 0))])

    if "disc" in bolted:
        add("oxygen_powerhead", "manifold_bolts", "fastener", bolts("HotGasManifold", (0, 0, 0), 300, 36, [(1050, -1)]))
    if "preburners" in bolted and not weld_pb:
        add("oxygen_powerhead", "oxygen_preburner_bolts", "fastener",
            bolts("OxygenPreburner", (0, 0, 0), 207, 24, [(X_PREBURNER + 22, 1), (X_DISC - 22, -1)]))
        add("methane_powerhead", "methane_preburner_bolts", "fastener",
            bolts("MethanePreburner", PUMP, R_FUEL_PB + 16, 16, [(X_FUEL_PB + 22, 1), (X_FUEL_PUMP - 22, -1)], 8))
    if "injector" in bolted and not weld_inj:
        add("oxygen_powerhead", "injector_bolts", "fastener",
            bolts("Injector", (0, 0, 0), (R_INJ + R_WAIST) / 2, 36, [(1250, 1), (1300, -1), (1370, 1)], 8))
    if "inlet" in bolted:
        add("methane_powerhead", "methane_inlet_bolts", "fastener", bolts("MethaneInlet", (0, *inlet), 68, 12, [(475, 1)]))
    return parts
