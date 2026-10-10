"""GE/NASA Energy Efficient Engine (E3) flight propulsion system: two-spool, long-duct mixed-flow turbofan.

Sources (see profile_builder/Turbofan/README.md):
  - profile_builder/Turbofan/E3_energy_efficient_engine_1981.pdf, Table I: fan Ø2108 mm, max nacelle Ø2489 mm,
    inlet length from fan face 1590 mm, nacelle length 6033 mm, exhaust nozzle Ø1590 mm,
    turbomachinery length 3180 mm, 162.4 kN takeoff thrust.
  - Same report, Figure 2 (cross-section): 32-blade fan with quarter-stage booster, 10-stage
    23:1 HPC, double-annular combustor, 2-stage HPT, 5-stage LPT, lobed mixer, centre plug.
  - E3 component design reports (profile_builder/Turbofan/): fan CR-165148 (part-span shrouds at 50 %
    span, 64 swept and leaned bypass OGVs, 56-blade quarter-stage rotor, chord 63.5-71.1 mm), HPC
    CR-165558 (airfoil counts per row; stators 2 and 5 read from a poor scan), HPT CR-167955 (46/76 and
    48/70 vanes/blades), LPT CR-167956 Figure 6 (nozzle/rotor counts per stage), FPS CR-168219 (mixer:
    18 scalloped lobes with radial sidewalls).
Stations and radii are digitized from Figure 2 (scale from the fan diameter, ~±15 mm).
Airfoil shapes (flat plates), the mixer lobes (radial sidewalls only) and internal structure are simplified.
Axis = +X, x = 0 at the fan leading edge (fan face). Units mm.
18 parts in 4 sub-assemblies (fan_module, static_structure, spools, core_stators) plus the nacelle.
Assumed for appearance, not taken from the sources: the rounding of the nacelle lip and trailing edge, of
the fan frame hub and of the plug's forward corner, the plug mounting bolts and the tie bolts between the
two HPT disks (counts, sizes, radii), the split of each spool into a shaft and its rotors, and the finishes
(lib/materials.py). Fasteners are a nut and stud end standing on a face; no holes are cut.
"""
from math import cos, radians

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # models/, for the shared lib/

from cadgen import glb, step, stl
from lib.materials import finishes, groups, recipes
from lib.shapes import assemble, flange_bolts, interp, stage, tip_radius, tube_profile, x_half

FAN_TIP_R = 1054.0     # Table I: fan Ø2108
FAN_CASE_R = 1059.0    # 5 mm tip clearance
FAN_BLADES = 32        # Figure 2
GAP = 3.0              # core rotor tip / stator hub clearance
LP_SHAFT_R = 60.0
HP_SHAFT = (1150.0, 2460.0, 80.0, 120.0)  # x0, x1, r_in, r_out

# Core gas path (x, r) digitized from Figure 2: casing inner wall and hub.
GAS_OUTER = [(240, 685), (450, 680), (680, 600), (900, 480), (1100, 395), (1190, 377), (1880, 318),
             (1970, 410), (2200, 410), (2220, 377), (2450, 377), (2540, 480), (3060, 630), (3537, 462)]
GAS_HUB = [(186, 318), (470, 436), (800, 360), (1100, 250), (1190, 227), (1880, 241), (2220, 240),
           (2450, 245), (2540, 331), (3060, 331)]
BYPASS_COWL = [(240, 690), (500, 700), (800, 655), (1200, 630), (2000, 620), (2600, 650), (3060, 640), (3537, 470)]


def rows(prefix, xs, last_pitch, r_stagger, s_stagger, r_n, s_n, thick=3):
    """Rotor at each x, stator half a pitch behind it; chords scale with the local pitch. r_n/s_n: counts per row."""
    out, before = [], None
    for i, (x, nxt) in enumerate(zip(xs, xs[1:] + [xs[-1] + last_pitch]), 1):
        p = nxt - x
        rp, before = min(p, before or p), p   # rotor chord from the shorter pitch either side: clears the stator ahead
        out += [(f"{prefix}{i}Rotor", "R", x, 0.4 * rp / cos(radians(r_stagger)), thick, r_n[i - 1], r_stagger),
                (f"{prefix}{i}Stator", "S", x + p / 2, 0.4 * p / cos(radians(s_stagger)), thick, s_n[i - 1], s_stagger)]
    return out


# (name, kind, x, chord, thickness, count, stagger°)
HPC = rows("HPC", [1190, 1303, 1412, 1494, 1566, 1644, 1698, 1771, 1825, 1880], 55, 45, -40,
           [28, 48, 50, 60, 70, 80, 82, 84, 88, 96], [50, 68, 82, 93, 92, 120, 112, 104, 118, 140])  # CR-165558
HPT = [("HPT1Nozzle", "S", 2220, 40, 8, 46, -50), ("HPT1Rotor", "R", 2280, 42, 6, 76, 55),  # CR-167955
       ("HPT2Nozzle", "S", 2340, 40, 8, 48, -50), ("HPT2Rotor", "R", 2400, 42, 6, 70, 55)]
LPT = [st for i, (x, nn, nr) in enumerate(zip((2592, 2688, 2792, 2901, 3015), (72, 102, 96, 114, 120),
                                              (120, 122, 122, 156, 110)), 1)  # CR-167956 Figure 6
       for st in ((f"LPT{i}Nozzle", "S", x - 47, 45, 6, nn, -50), (f"LPT{i}Rotor", "R", x, 48, 6, nr, 55))]


def row_ops(stages, kind, bore=0):
    return [op for st in stages if st[1] == kind
            for op in stage(*st, bore=bore, outer=GAS_OUTER, hub=GAS_HUB, gap=GAP)]


def nacelle():
    """Long-duct mixed-flow nacelle: highlight 1590 mm ahead of the fan, 6033 mm long, Ø1590 exit."""
    outer = [(-1590, 1080), (-1400, 1190), (-900, 1240), (0, 1244.5), (1500, 1244.5), (3000, 1100), (4443, 820)]
    inner = [(4443, 795), (2500, 1000), (1000, FAN_CASE_R), (0, FAN_CASE_R), (-400, 1040), (-1400, 1010), (-1560, 1040), (-1590, 1060)]
    # lathe rounds the lip, the forebody knuckle and the trailing edge; the lip keeps a 4 mm land at the highlight station
    return [("lathe", "Nacelle", outer + inner, 60)]


def fan():
    """32 twisted blades on the fan hub; leading edge at x=0, trailing edge at x=186 (Figure 2)."""
    root, tip = (300, 190, 30, 25), (tip_radius(FAN_TIP_R, 330, 0, 58), 330, 8, 58)  # (r, chord, thick, twist°)
    sections = [tuple(p + (q - p) * i / 7 for p, q in zip(root, tip)) for i in range(8)]  # ~5° of twist per step
    return [("revolve", "FanHub", [(0, 0), (0, 330), (186, 318), (186, 0)]),
            ("loft", "FanBlades", 93, sections, FAN_BLADES),
            ("revolve", "PartSpanShroud", [(78, 670), (108, 670), (108, 680), (78, 680)])]  # clappers at 50 % span


def booster():
    """Booster drum on the LP shaft with the 56 quarter-stage blades."""
    booster_tip = tip_radius(interp(GAS_OUTER, 425) - GAP, 67, 4, 40)
    return [("revolve", "BoosterDrum", [(186, LP_SHAFT_R), (186, 318), (470, 436), (470, LP_SHAFT_R)]),
            ("ring", "BoosterRotor", 400, interp(GAS_HUB, 400) - 10, booster_tip, 67, 4, 56, 40)]


def hpt_tie_bolts():
    """Bolt circle between the two HPT disks: nuts on the facing disk faces."""
    dx = x_half(*HPT[1][3:5], HPT[1][6]) + 2   # stage(): the disk stands 2 mm past the blade row on both sides
    return flange_bolts("HPTTie", (0, 0, 0), (1, 0, 0), 180, 12, 30, [(HPT[1][2] + dx, 1), (HPT[3][2] - dx, -1)])


def core_casing():
    """Splitter, core cowl and casing to the mixer exit, 64 bypass OGVs (integrated vane-frame), 18 mixer lobes."""
    ogv_x, chord, thick, stagger = 760, 140, 8, 20
    return [("revolve", "CoreCasing", BYPASS_COWL + GAS_OUTER[:0:-1] + [(240, 685)]),
            ("ring", "BypassOGVs", ogv_x, 640, tip_radius(FAN_CASE_R, chord, thick, stagger), chord, thick, 64, stagger),
            ("fins", "MixerLobes", [(3250, 565), (3537, 380), (3537, 560)], 8, 18)]  # lobe sidewalls, crests not modelled


def combustor():
    """Double-annular liner (open aft) with two rows of 20 fuel nozzles on stems from the casing."""
    x_stem = 1985  # casing is flat (r=410) from 1970, so the Ø12 stems seat without clipping the diffuser slope
    r_wall = tip_radius(interp(GAS_OUTER, x_stem), 0, 12, 0)
    ops = [("revolve", "Liner", [(1975, 290), (1995, 262), (2190, 255), (2190, 400), (1995, 395), (1975, 370)]),
           ("cut", "LinerInside", [(1985, 293), (2003, 268), (2200, 262), (2200, 393), (2003, 389), (1985, 366)]),
           ("revolve", "CentreBody", tube_profile(1985, 2080, 326, 332))]  # splits the two annuli
    for row, (r, angle) in (("Inner", (300, 0)), ("Outer", (358, 9))):  # outer row staggered by half a pitch
        ops += [("axial_pins", f"{row}Nozzles", 1980, r, 14, 30, 20, angle),
                ("pins", f"{row}Stems", x_stem, r, r_wall, 12, 20, angle)]
    return ops


def exhaust_plug():
    """Centre plug held by 8 LPT aft-frame struts."""
    x, chord, thick = 3110, 50, 12
    tip = tip_radius(min(interp(GAS_OUTER, x - chord / 2), interp(GAS_OUTER, x + chord / 2)), chord, thick, 0)
    return [("lathe", "Plug", [(3080, 0), (3080, 309), (3300, 280), (3900, 160), (4580, 0)], 20),
            ("ring", "PlugStruts", x, 280, tip, chord, thick, 8, 0)]


def spec():
    """[(sub-assembly or None, part label, finish, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    return [
        (None, "nacelle", "paint_grey", nacelle()),

        ("fan_module", "spinner", "dark_steel", [("spline", "Spinner", [(-568, 0), (-400, 190), (-200, 295), (0, 330)])]),
        ("fan_module", "fan", "machined_steel", fan()),

        ("static_structure", "core_casing", "cast_alloy", core_casing()),
        ("static_structure", "fan_frame_hub", "cast_alloy", [  # static inner wall of the gooseneck duct from the booster to the HPC inlet
            ("lathe", "FrameHub", [(475, 436), (800, 360), (1100, 252), (1160, 232), (1160, 130), (475, 130)], 6)]),
        ("static_structure", "exhaust_plug", "hot_alloy", exhaust_plug()),
        ("static_structure", "plug_bolts", "fastener", flange_bolts("Plug", (0, 0, 0), (1, 0, 0), 200, 16, 24, [(3080, -1)])),

        # fan-driven spool: shaft, booster, 5 LPT rotors; core spool: shaft, 10 HPC rotors, 2 HPT rotors
        ("spools", "lp_shaft", "dark_steel", [("revolve", "LPShaft", tube_profile(186, 3075, 0, LP_SHAFT_R))]),
        ("spools", "booster", "machined_steel", booster()),
        ("spools", "lpt_rotor", "hot_alloy", row_ops(LPT, "R", LP_SHAFT_R)),
        ("spools", "hp_shaft", "dark_steel", [("revolve", "HPShaft", tube_profile(*HP_SHAFT))]),
        ("spools", "hpc_rotor", "nozzle_alloy", row_ops(HPC, "R", HP_SHAFT[3])),
        ("spools", "hpt_rotor", "hot_alloy", row_ops(HPT, "R", HP_SHAFT[3])),
        ("spools", "hpt_tie_bolts", "fastener", hpt_tie_bolts()),

        ("core_stators", "combustor", "tint_bronze", combustor()),
        ("core_stators", "hpc_stators", "machined_steel", row_ops(HPC, "S")),
        ("core_stators", "hpt_nozzles", "tint_straw", row_ops(HPT, "S")),
        ("core_stators", "lpt_stators", "hot_alloy", row_ops(LPT, "S")),
    ]


SPEC = spec()
GROUPS = groups(SPEC)
MATERIALS = finishes(SPEC)


def parts():
    """[(label, colour, ops)] for assemble() and the native CAD builders."""
    return recipes(SPEC)


@glb(out="../GLB/ge_e3_turbofan.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/ge_e3_turbofan.stl")
@step(out="../STEP/ge_e3_turbofan.step", materials=MATERIALS)
def ge_e3_turbofan():
    return assemble(parts(), "ge_e3_turbofan", GROUPS)


if __name__ == "__main__":
    ge_e3_turbofan()
