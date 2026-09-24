"""GE/NASA Energy Efficient Engine (E3) flight propulsion system: two-spool, long-duct mixed-flow turbofan.

Sources (see resources/README.md):
  - resources/E3_energy_efficient_engine_1981.pdf, Table I: fan Ø2108 mm, max nacelle Ø2489 mm,
    inlet length from fan face 1590 mm, nacelle length 6033 mm, exhaust nozzle Ø1590 mm,
    turbomachinery length 3180 mm, 162.4 kN takeoff thrust.
  - Same report, Figure 2 (cross-section): 32-blade fan with quarter-stage booster, 10-stage
    23:1 HPC, double-annular combustor, 2-stage HPT, 5-stage LPT, lobed mixer, centre plug.
Stations and radii are digitized from Figure 2 (scale from the fan diameter, ~±15 mm).
Blade counts beyond the fan, airfoil shapes and internal structure are assumptions.
Axis = +X, x = 0 at the fan leading edge (fan face). Units mm.
"""
from math import cos, radians, sin

from cadgen import build123d as bd
from cadgen import glb, step, stl
from lib.shapes import blade_ring, interp, labelled, revolved, stage, tip_radius, tube

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


def rows(xs, last_pitch, r_stagger, s_stagger, r_n, s_n, thick=3):
    """Rotor at each x, stator half a pitch behind it; chords scale with the local pitch."""
    out = []
    for x, nxt in zip(xs, xs[1:] + [xs[-1] + last_pitch]):
        p = nxt - x
        out += [("R", x, 0.4 * p / cos(radians(r_stagger)), thick, r_n, r_stagger),
                ("S", x + p / 2, 0.4 * p / cos(radians(s_stagger)), thick, s_n, s_stagger)]
    return out


# (kind, x, chord, thickness, count, stagger°)
BOOSTER = [("R", 400, 60, 4, 40, 40)]                                    # quarter stage
HPC = rows([1190, 1303, 1412, 1494, 1566, 1644, 1698, 1771, 1825, 1880], 55, 45, -40, 32, 40)
HPT = [("S", 2220, 40, 8, 36, -50), ("R", 2280, 42, 6, 50, 55), ("S", 2340, 40, 8, 36, -50), ("R", 2400, 42, 6, 50, 55)]
LPT = [st for x in (2592, 2688, 2792, 2901, 3015) for st in (("S", x - 47, 45, 6, 50, -50), ("R", x, 48, 6, 60, 55))]


def row(st, bore=0):
    return stage(*st, bore=bore, outer=GAS_OUTER, hub=GAS_HUB, gap=GAP)


def nacelle():
    """Long-duct mixed-flow nacelle: highlight 1590 mm ahead of the fan, 6033 mm long, Ø1590 exit."""
    outer = [(-1590, 1070), (-1400, 1190), (-900, 1240), (0, 1244.5), (1500, 1244.5), (3000, 1100), (4443, 820)]
    inner = [(4443, 795), (2500, 1000), (1000, FAN_CASE_R), (0, FAN_CASE_R), (-400, 1040), (-1400, 1010), (-1560, 1040)]
    return labelled(revolved(outer + inner), "nacelle", "#D9DDE3")


def spinner():
    return labelled(revolved([(-568, 0), (-400, 190), (-200, 295), (0, 330)], spline=True), "spinner", "#2B2F36")


def blade_section(x, r, chord, thick, angle):
    """Elliptical section on a plane normal to the radial (Y) direction."""
    a = radians(angle)
    plane = bd.Plane(origin=(x, r, 0), x_dir=(cos(a), 0, sin(a)), z_dir=(0, 1, 0))
    return plane * bd.Ellipse(chord / 2, thick / 2)


def fan():
    """32 twisted blades on the fan hub; leading edge at x=0, trailing edge at x=186 (Figure 2)."""
    hub = revolved([(0, 0), (0, 330), (186, 318), (186, 0)])
    blade = bd.loft([blade_section(93, 300, 190, 30, 25),
                     blade_section(93, tip_radius(FAN_TIP_R, 330, 0, 58), 330, 8, 58)])
    body = hub + [bd.Rot(360 / FAN_BLADES * i, 0, 0) * blade for i in range(FAN_BLADES)]
    return labelled(body, "fan", "#8A939E")


def lp_spool():
    """Fan-driven spool: shaft, booster drum with the quarter-stage blades, 5 LPT rotors."""
    parts = [tube(186, 3075, 0, LP_SHAFT_R), revolved([(186, LP_SHAFT_R), (186, 318), (470, 436), (470, LP_SHAFT_R)])]
    parts += blade_ring(400, interp(GAS_HUB, 400) - 10, tip_radius(interp(GAS_OUTER, 425) - GAP, 60, 4, 40), 60, 4, 40, 40)
    for st in LPT:
        if st[0] == "R":
            parts += row(st, bore=LP_SHAFT_R)
    return labelled(bd.Part() + parts, "lp_spool", "#9AA3AD")


def hp_spool():
    parts = [tube(*HP_SHAFT)]
    for st in HPC + HPT:
        if st[0] == "R":
            parts += row(st, bore=HP_SHAFT[3])
    return labelled(bd.Part() + parts, "hp_spool", "#B8A07A")


def core_casing():
    """Splitter, core cowl and casing to the mixer exit, with 40 bypass OGVs (integrated vane-frame)."""
    casing = revolved(BYPASS_COWL + GAS_OUTER[:0:-1] + [(240, 685)])
    ogv_x, chord, thick, stagger = 760, 140, 8, 20
    ogvs = blade_ring(ogv_x, 640, tip_radius(FAN_CASE_R, chord, thick, stagger), chord, thick, 40, stagger)
    return labelled(casing + ogvs, "core_casing", "#5B636E")


def fan_frame_hub():
    """Static inner wall of the gooseneck duct from the booster to the HPC inlet."""
    return labelled(revolved([(475, 436), (800, 360), (1100, 252), (1160, 232), (1160, 130), (475, 130)]),
                    "fan_frame_hub", "#6E7782")


def combustor():
    """Double-annular liner (open aft) with two rows of 20 fuel nozzles on stems from the casing."""
    liner = (revolved([(1975, 290), (1995, 262), (2190, 255), (2190, 400), (1995, 395), (1975, 370)])
             - revolved([(1985, 293), (2003, 268), (2200, 262), (2200, 393), (2003, 389), (1985, 366)]))
    liner += tube(1985, 2080, 326, 332)  # centre-body splitting the two annuli
    x_stem = 1985  # casing is flat (r=410) from 1970, so the Ø12 stems seat without clipping the diffuser slope
    r_wall = tip_radius(interp(GAS_OUTER, x_stem), 0, 12, 0)
    nozzles = []
    for i in range(20):
        for r, offset in ((300, 0), (358, 9)):  # outer row staggered by half a pitch
            nozzles += [bd.Rot(18 * i + offset, 0, 0) * s for s in (
                bd.Pos(1980, r, 0) * bd.Cylinder(7, 30, rotation=(0, 90, 0)),
                bd.Pos(x_stem, (r + r_wall) / 2, 0) * bd.Cylinder(6, r_wall - r, rotation=(90, 0, 0)))]
    return labelled(liner + nozzles, "combustor", "#A0522D")


def exhaust_plug():
    """Centre plug held by 8 LPT aft-frame struts."""
    plug = revolved([(3080, 0), (3080, 309), (3300, 280), (3900, 160), (4580, 0)])
    x, chord, thick = 3110, 50, 12
    tip = tip_radius(min(interp(GAS_OUTER, x - chord / 2), interp(GAS_OUTER, x + chord / 2)), chord, thick, 0)
    return labelled(plug + blade_ring(x, 280, tip, chord, thick, 8, 0), "exhaust_plug", "#3A3F47")


def stators(stages, label, color):
    return labelled(bd.Part() + [v for st in stages if st[0] == "S" for v in row(st)], label, color)


@glb(out="../GLB/turbofan.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/turbofan.stl")
@step(out="../STEP/turbofan.step")
def turbofan():
    return bd.Compound(children=[
        nacelle(), spinner(), fan(), core_casing(), fan_frame_hub(),
        lp_spool(), hp_spool(), combustor(), exhaust_plug(),
        stators(HPC, "hpc_stators", "#7F8893"),
        stators(HPT, "hpt_nozzles", "#8B5A3C"),
        stators(LPT, "lpt_stators", "#8B6B4A"),
    ], label="turbofan")


if __name__ == "__main__":
    turbofan()
