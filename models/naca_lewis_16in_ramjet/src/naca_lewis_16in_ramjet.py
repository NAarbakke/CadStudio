"""NACA Lewis 16-inch ram jet (altitude wind tunnel free-jet engine, 1951), 15 parts in 4 sub-assemblies.

Sources (profile_builder/Ramjet/RM-E51C16_16in_ramjet_free_jet_1951.pdf):
  - NACA RM E51C16 (Perchonok and Farley), Table I: shell inside diameters, diffuser inner-body and spike
    coordinates in inches; spike tip 4.27 in ahead of the lip at M 1.73 (2.63 at M 1.35). Figure 1: diffuser
    91 in, combustion chamber 81 in (Ø16), nozzle 9 in to Ø13.75, movable tail plug. Text: external cowl at 11°,
    fuel injected upstream 74 in behind the lip; Figure 2: four dual-arc fuel bars on a 5.22 in radius, four
    nozzles each, fed by a stem from the centre body; Figure 3 and text: corrugated-gutter grid flame holder 17 in behind the injector, 2 in
    chord, 35-53° included angle, inner rim around the pilot exit, 54 % blockage; tail plug sets the exit
    area to 51-74 % of the chamber area; chamber and plug water-cooled.
  - NACA RM E52D08 (same 16-inch engine): centre body held by three struts, 17 % thick.
Stations x in inches from the inlet lip (Table I), converted to mm here; axis = +X (flow direction).
Read from Figure 1 (~±0.5 in): flange stations, tail-plug shape and position, plug struts, cooling coil.
Assumed: wall and flange thicknesses, centre-body strut station and chord, gutter pitch (5 corrugated
gutters and 4 connecting gutters counted from the photo). Straight gutters at 40° included angle stand in
for the corrugated ones (40° gives the reported 54 % blockage). Not modelled: rakes, pressure lines,
pilot air elbows and spark plug, water and fuel lines outside the shell, tunnel mounts.
Assumed for appearance, not taken from the sources: the bolt circles (24 x 5/16 in on a 9 in radius at each
of the five flange joints), flange edge chamfers, the collar's corner radius, elliptical strut sections in
place of the 17 % thick airfoils, and the finishes (lib/materials.py), including copper for the cooling
coil. Fasteners are a nut and stud end standing on a flange face; no holes are cut.
"""
from math import asin, cos, degrees, radians, sin, tan

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # models/, for the shared lib/

from cadgen import glb, step, stl
from lib.materials import finishes, groups, recipes
from lib.shapes import assemble, flange_bolts, interp, tip_radius

IN = 25.4  # the source is in inches; geometry below is written in inches and scaled once


def mm(points):
    return [tuple(v * IN for v in p) for p in points]


SPIKE_TIP = -4.27              # M 1.73 spike position (Table I)
WALL, FLANGE_R = 0.1875, 9.5   # shell wall and flange outer radius (assumed)
SHELL_ID = [(0, 4.50), (1, 4.64), (1.5, 4.68), (2, 4.72), (2.5, 4.76), (3, 4.80), (3.5, 4.83), (4, 4.86),
            (4.5, 4.88), (5, 4.91), (6, 4.96), (65, 8.00)]            # Table I shell inside radius, 16° lip cone
CENTREBODY = [(4.75, 2.00), (5.75, 2.08), (6, 2.095), (6.25, 2.11), (6.5, 2.125), (6.75, 2.14), (9.75, 2.28),
              (10, 2.28), (65, 4.00), (75, 4.00), (91, 3.00)]         # Table I inner body, pilot exit Ø6 at 91
# Table I spike (distance from apex, radius): 46° cone to 3 in, then the ogive to the Ø4 sliding cylinder
SPIKE = [(0, 0), (3, 3 * tan(radians(23))), (3.5, 1.47), (3.75, 1.58), (4, 1.67), (4.25, 1.75), (4.5, 1.82),
         (4.75, 1.86), (5, 1.91), (5.25, 1.94), (5.5, 1.96), (5.75, 1.97), (6.25, 1.98), (9.75, 1.98)]
X_INJ, R_BAR, BAR_DIA = 74.0, 5.22, 0.25    # fuel bars (Figure 2)
FOOT = degrees(asin(1.125 / R_BAR))          # nozzles at the Ø2.25 hoop's feet ...
END = FOOT + degrees(1.875 / R_BAR)          # ... and at the ends of the 1 7/8 in arms (degrees from the bar centre)
X_FH = 91.2                                  # flame-holder gutter apex (combustion-chamber inlet, station 3)
X_NOZ, X_EXIT, R_EXIT = 172.0, 181.0, 6.875  # nozzle: Ø16 -> Ø13.75 over 9 in
COIL = [x for lo, hi in ((100, 108), (113, 119), (123, 153), (157, 169)) for x in range(lo, hi + 1)]  # Fig 1 turns


def flange(name, x0, x1):
    """Flange ring from inside the shell wall out to FLANGE_R, edges chamfered (large thin ring)."""
    return ("lathe", name, mm([(x0, 8.08), (x1, 8.08), (x1, FLANGE_R), (x0, FLANGE_R)]), 0.06 * IN, (0, 0, 0), (1, 0, 0), True)


def joint_bolts(name, x0, x1):
    """Bolt circle through a flange joint: nuts on the faces at x0 (forward) and x1 (aft)."""
    return flange_bolts(name, (0, 0, 0), (1, 0, 0), 9.0 * IN, 0.3125 * IN, 24, [(x0 * IN, -1), (x1 * IN, 1)])


def struts(name, x, r0, r1, chord, thick, n=3):
    """n radial struts of elliptical section, their tip corners inside radius r1 (inches)."""
    tip = tip_radius(r1, chord, thick, 0)
    return ("loft", name, x * IN, [(r * IN, chord * IN, thick * IN, 0) for r in (r0, tip)], n)


def gutter(y0, leg, half, x0=X_FH, t=0.06):
    """V-gutter section (x, y), apex upstream at (x0, y0), sheet t thick; extruded along Z by the fins op."""
    a = radians(half)
    d, h, e, ht = leg * cos(a), leg * sin(a), t / sin(a), leg * sin(a) - t / cos(a)
    return [(x0, y0), (x0 + d, y0 + h), (x0 + d, y0 + ht), (x0 + e, y0), (x0 + d, y0 - ht), (x0 + d, y0 - h)]


def polar(r, deg, x=X_INJ):
    return (x, r * cos(radians(deg)), r * sin(radians(deg)))


def fuel_bar(c):
    """One dual-arc bar centred at c° (from +Y toward +Z): arm on R_BAR, Ø2.25 hoop out to the feed stem, arm."""
    mid, cr = R_BAR * cos(radians(FOOT)), radians(c)          # hoop centre radius
    arm = [c - END + (END - FOOT) * i / 4 for i in range(5)]
    hoop = [(X_INJ, mid * cos(cr) + 1.125 * sin(radians(p) - cr), mid * sin(cr) + 1.125 * cos(radians(p) - cr))
            for p in range(160, 0, -20)]                      # φ = 180° is foot 1, 0° foot 2 (both on the arms)
    return [polar(R_BAR, a) for a in arm] + hoop + [polar(R_BAR, 2 * c - a) for a in reversed(arm)]


def spec():
    """[(sub-assembly, part label, finish, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    w = 8.0 + WALL
    inlet = [(0, 4.5), (6.4, 4.5 + 6.4 * tan(radians(11))), (6.4, interp(SHELL_ID, 6.4) + WALL),
             (64.5, interp(SHELL_ID, 64.5) + WALL), (65, w), (65, 8.0),
             *[p for p in reversed(SHELL_ID) if 0 < p[0] < 65]]
    corrugated, connecting = (2.0, 20), (0.75, 20, X_FH + 0.3)   # (leg, half-angle°[, apex x]); connectors sit aft
    return [
        ("inlet", "inlet_diffuser", "machined_steel", [     # sharp lip, 11° cowl, 65 in cone
            ("revolve", "Diffuser", mm(inlet)), flange("DiffuserFlange", 64.5, 65)]),
        ("inlet", "spike", "dark_steel", [  # translating spike with its actuator rod, sliding in the centre-body sleeve
            ("revolve", "Spike", mm([(SPIKE_TIP + d, r) for d, r in SPIKE]
                                    + [(SPIKE_TIP + 9.75, 0.625), (12.0, 0.625), (12.0, 0)]))]),
        ("inlet", "centre_body", "nozzle_alloy", [  # Table I inner body, bored for the spike, pilot-burner cup at the tail
            ("revolve", "InnerBody", mm([(4.75, 1.99), *CENTREBODY, (91, 2.75), (80, 2.75), (80, 0), (12.5, 0),
                                         (12.5, 0.7), (10.5, 0.7), (10.5, 1.99)])),
            ("axial_pins", "PilotNozzle", 80.65 * IN, 0, 0.5 * IN, 1.5 * IN, 1),
            struts("Struts", 68.5, 3.8, 7.98, 5.0, 0.85)]),
        ("inlet", "diffuser_joint_bolts", "fastener", joint_bolts("DiffuserJoint", 64.5, 65.5)),

        ("fuel_system", "injector_section", "machined_steel", [  # spool 65-72 and the duct to the flame-holder flange at 91
            ("revolve", "InjectorSection", mm([(65, 8.0), (91, 8.0), (91, w), (65, w)])),
            flange("SpoolFwdFlange", 65, 65.5), flange("SpoolJointFlanges", 71.5, 72.5), flange("DuctAftFlange", 90.5, 91)]),
        ("fuel_system", "spool_joint_bolts", "fastener", joint_bolts("SpoolJoint", 71.5, 72.5)),
        ("fuel_system", "fuel_injector", "brass", [  # 4 dual-arc bars x 4 spray nozzles pointing upstream, stems from the centre body
            *[("pipe", f"FuelBar{i + 1}", mm(fuel_bar(90 * i)), BAR_DIA * IN) for i in range(4)],
            *[("axial_pins", f"SprayNozzles{j + 1}", (X_INJ - 0.4) * IN, R_BAR * IN, 0.4 * IN, 1.2 * IN, 4, a)
              for j, a in enumerate((-END, -FOOT, FOOT, END))],
            ("pins", "FeedStems", X_INJ * IN, 4.01 * IN, 6.22 * IN, 0.3 * IN, 4),   # 0.01 in clear of the centre body
            ("pins", "StemNuts", X_INJ * IN, 5.2 * IN, 5.7 * IN, 0.5 * IN, 4)]),
        ("fuel_system", "flame_holder", "tint_bronze", [  # gutter grid: 5 gutters along Z, 4 connecting gutters along Y, two rims
            ("fins", "CentreGutter", mm(gutter(0, *corrugated)), 16 * IN, 1),
            ("fins", "InnerGutters", mm(gutter(3.2, *corrugated)), 16 * IN, 2),
            ("fins", "OuterGutters", mm(gutter(6.4, *corrugated)), 16 * IN, 2),
            ("fins", "InnerConnectors", mm(gutter(3.2, *connecting)), 16 * IN, 2, 90),
            ("fins", "OuterConnectors", mm(gutter(6.4, *connecting)), 16 * IN, 2, 90),
            ("cut", "TrimOuter", mm([(91, 7.93), (93.3, 7.93), (93.3, 12), (91, 12)])),
            ("cut", "TrimInner", mm([(91, 0), (93.3, 0), (93.3, 3.08), (91, 3.08)])),
            ("revolve", "OuterRim", mm([(91.1, 7.90), (93.1, 7.90), (93.1, 7.98), (91.1, 7.98)])),
            ("revolve", "InnerRim", mm([(91.1, 3.02), (93.1, 3.02), (93.1, 3.12), (91.1, 3.12)]))]),
        ("fuel_system", "flame_holder_joint_bolts", "fastener", joint_bolts("FlameHolderJoint", 90.5, 91.5)),

        ("combustor", "combustion_chamber", "hot_alloy", [  # Ø16 x 81 in, flanged at 91 / 110.75 / 172
            ("revolve", "Chamber", mm([(91, 8.0), (X_NOZ, 8.0), (X_NOZ, w), (91, w)])),
            flange("ChamberFwdFlange", 91, 91.5), flange("ChamberJointFlanges", 110.25, 111.25),
            flange("ChamberAftFlange", X_NOZ - 0.5, X_NOZ)]),
        # ponytail: water-cooling coil turns as separate rings standing on the wall; a helix needs a native sweep op
        ("combustor", "cooling_coil", "copper", [
            ("torus", f"CoolingCoil{i + 1}", x * IN, (w + 0.405) * IN, 0.4 * IN) for i, x in enumerate(COIL)]),
        ("combustor", "chamber_joint_bolts", "fastener", joint_bolts("ChamberJoint", 110.25, 111.25)),

        ("exhaust", "exhaust_nozzle", "nozzle_alloy", [  # water-jacketed convergent nozzle, minimum area at the exit
            ("lathe", "Nozzle", mm([(X_NOZ, 8.0), (X_EXIT, R_EXIT), (X_EXIT, 7.5), (X_NOZ + 0.5, 8.6),
                                    (X_NOZ + 0.5, FLANGE_R), (X_NOZ, FLANGE_R)]), 0.06 * IN, (0, 0, 0), (1, 0, 0), True)]),
        ("exhaust", "nozzle_joint_bolts", "fastener", joint_bolts("NozzleJoint", X_NOZ - 0.5, X_NOZ + 0.5)),
        ("exhaust", "tail_plug", "machined_steel", [  # movable plug (Ø7.67 = 74 -> 51 % exit area) on a rod held by 2 x 3 struts
            ("spline", "Plug", mm([(X_EXIT, 0), (179, 1.35), (176, 2.65), (173, 3.45), (170, 3.8), (167.5, 3.835),
                                   (165, 3.6), (162.5, 2.9), (160.5, 1.95), (159.3, 1.5)])),
            ("lathe", "Collar", mm([(158.5, 0), (158.5, 1.6), (159.5, 1.6), (159.5, 0)]), 0.12 * IN),
            ("revolve", "Rod", mm([(117.5, 0), (158.6, 0), (158.6, 1.375), (117.5, 1.375)])),
            ("revolve", "RodNose", mm([(117.5 - 1.625 * cos(radians(a)), 1.625 * sin(radians(a))) for a in range(0, 91, 15)]
                                      + [(118.5, 1.625), (118.5, 0)])),
            *[struts(f"PlugStruts{i + 1}", x, 1.2, 7.98, 2.4, 0.5) for i, x in enumerate((121.3, 155.4))]]),
    ]


SPEC = spec()
GROUPS = groups(SPEC)
MATERIALS = finishes(SPEC)


def parts():
    """[(label, colour, ops)] for assemble() and the native CAD builders."""
    return recipes(SPEC)


@glb(out="../GLB/naca_lewis_16in_ramjet.glb", mesh_tolerance=6e-4, mesh_angular_tolerance=0.25)
@stl(out="../STL/naca_lewis_16in_ramjet.stl")
@step(out="../STEP/naca_lewis_16in_ramjet.step", materials=MATERIALS)
def naca_lewis_16in_ramjet():
    return assemble(parts(), "NACA Lewis 16-inch ramjet", GROUPS)


if __name__ == "__main__":
    naca_lewis_16in_ramjet()
