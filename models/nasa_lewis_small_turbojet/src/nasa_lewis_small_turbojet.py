"""NASA Lewis small expendable turbojet (1976-77), from its design report and published cross-section.

Sources (profile_builder/Turbojet/README.md):
  - profile_builder/Turbojet/small_expendable_turbojet_1977.pdf: Ø292 mm max, 965 mm long, 59 kg, 35 170 rpm rated.
  - profile_builder/Turbojet/TMX-3392_design_fabrication_1976.pdf (NASA TM X-3392, design and fabrication):
    Figure 1 cross-section (stations and walls read off it, x = 0 at the nose tip, ~±2 mm), Table II airfoil
    counts, Table III hub/tip chord, thickness, span and tip diameter of every row; text: two-strut inlet
    housing with the front bearing and a 5:1 gearbox in its centrebody, fuel control on top of it; welded
    4-stage blade-disk drum; casing halves split axially with threaded vane stems; annular combustor with a
    snout, perforated liners and no inner housing wall (the mainshaft is the inner boundary), 12 simplex fuel
    nozzles fed by one tube, two surface-discharge igniters; 35-vane one-piece turbine stator whose outer
    shroud runs ~25 mm past the vanes over the 57-blade rotor (tip Ø245.8); exhaust duct with three struts
    and the rear bearing housing; convergent nozzle; ball (205: 25 x 52 x 15) and roller (240: 20 x 47 x 14)
    main bearings.
Assumed: airfoil stagger/twist (not tabulated), elliptical sections stacked radially, the 8-vane swirlers
and liner perforations left out, wall/flange thicknesses, disk web/bore shapes, strut thickness, fuel
control box size, trunnion boss size and igniter clocking. 14 parts. Axis = +X from the nose tip. Units mm.
"""
from cadgen import glb, step, stl
from lib.rocket import shell
from lib.shapes import assemble, interp, tip_radius, x_half

GAP = 1.0              # rotor tip / stator hub clearance (0.4 mm at assembly, TM X-3392 p. 6)
# Compressor casing inner wall and rotor drum (x, r): Table III tip diameters and spans at the Figure 1 stations
C_OUTER = [(295, 99.2), (314, 99.2), (341, 99.4), (368, 100.2), (389, 101.2), (407, 102.1), (426, 102.9),
           (443, 103.7), (465, 104.3), (487, 104.5)]
C_HUB = [(300, 48.5), (314, 53.1), (341, 60.5), (368, 65.5), (389, 73.3), (407, 76.5), (426, 80.4), (443, 83.8),
         (465, 86.1), (475, 86.3)]
T_OUTER = [(725, 122.5), (752, 122.5), (752, 124), (800, 124)]  # vane ring shroud, then the rotor shroud
T_HUB = [(725, 81), (800, 81)]
# (name, kind, x, count, hub (chord, thick, twist°), tip (chord, thick, twist°)): Table II, Table III, Figure 1
ROWS = [("Comp1Rotor", "R", 314, 23, (31.9, 2.7, 35), (32.2, 1.3, 55)),
        ("Comp1Stator", "S", 341, 28, (19.9, 1.1, -25), (25.4, 2.2, -35)),
        ("Comp2Rotor", "R", 368, 29, (23.7, 3.3, 35), (23.7, 1.0, 55)),
        ("Comp2Stator", "S", 389, 36, (17.8, 1.1, -25), (20.0, 1.9, -35)),
        ("Comp3Rotor", "R", 407, 36, (19.4, 1.8, 35), (19.5, 0.9, 55)),
        ("Comp3Stator", "S", 426, 42, (16.5, 1.3, -25), (16.5, 1.8, -35)),
        ("Comp4Rotor", "R", 443, 38, (18.7, 1.6, 35), (18.8, 0.9, 55)),
        ("Comp4Stator", "S", 465, 42, (16.8, 1.3, -25), (16.8, 1.8, -35)),
        ("TurbNozzle", "S", 738, 35, (29.1, 4.1, -55), (21.9, 3.0, -60)),  # tip thickness misprinted in Table III
        ("TurbRotor", "R", 776, 57, (21.2, 3.6, 25), (18.6, 1.6, 45))]
BORE = (26, 38)        # disk bore bulb, r (Figure 1 proportions)
LINER = [(724, 124.5), (700, 125), (552, 125), (545, 118), (545, 69), (552, 60), (690, 60), (715, 78.8), (724, 80.8),
         (724, 82.8), (715, 80.8), (690, 62), (554, 62), (547, 69.5), (547, 117.5), (554, 123), (700, 123), (724, 122.5)]
HOUSING = [(487, 104.5), (500, 110), (540, 127), (580, 140), (600, 143), (645, 143), (700, 131), (728, 128)]
EXHAUST = [(800, 124), (815, 128), (835, 130), (870, 122), (925, 100)]          # duct inner wall
CENTREBODY = [(805, 80), (835, 70), (870, 52), (930, 27), (952, 12), (958, 0)]  # tail cone outer surface


def row(name, kind, x, n, hub_sec, tip_sec, outer, hub):
    """Lofted row through hub, mid and tip sections; rotor roots sink into the drum, stator tips reach the casing."""
    dx = max(x_half(*hub_sec), x_half(*tip_sec))
    r_out = min(interp(outer, x - dx), interp(outer, x + dx))
    if kind == "R":
        root, tip = min(interp(hub, x - dx), interp(hub, x + dx)) - 2, tip_radius(r_out - GAP, *tip_sec)
    else:
        root, tip = max(interp(hub, x - dx), interp(hub, x + dx)) + GAP, tip_radius(r_out, *tip_sec)
    return ("loft", name, x, [(root + (tip - root) * k / 2, *(h + (t - h) * k / 2 for h, t in zip(hub_sec, tip_sec)))
                              for k in range(3)], n)


def rows(kind, outer, hub, names):
    return [row(*r, outer, hub) for r in ROWS if r[1] == kind and r[0].startswith(names)]


def disk(name, x, hub_sec, tip_sec):
    """Blade-disk rim under the drum line, a web and a bore bulb (stages 2-4; stage 1 is the front hub)."""
    dx = max(x_half(*hub_sec), x_half(*tip_sec)) + 1
    rim = min(interp(C_HUB, x - dx), interp(C_HUB, x + dx)) - 6
    return ("revolve", f"{name}Disk", [(x - 7, BORE[0]), (x + 7, BORE[0]), (x + 7, BORE[1]), (x + 2.5, BORE[1]),
                                       (x + 2.5, rim), (x + dx, rim), (x + dx, interp(C_HUB, x + dx)),
                                       (x - dx, interp(C_HUB, x - dx)), (x - dx, rim), (x - 2.5, rim),
                                       (x - 2.5, BORE[1]), (x - 7, BORE[1])])


def rotor():
    """Welded drum: front hub + stub shaft, disks 2-4, rear cone, hollow mainshaft, turbine disk + rear stub shaft."""
    drum = [(x, r) for x, r in C_HUB]
    return [("revolve", "FrontHub", [(255, 0), (255, 12.5), (290, 12.5), (298, 30), (300, 48.5), (328, 56.8),
                                     (333, 40), (333, 0)]),
            ("revolve", "Drum", drum + [(x, r - 3) for x, r in reversed(drum)]),
            *[disk(r[0], r[2], r[4], r[5]) for r in ROWS if r[1] == "R" and r[0] in ("Comp2Rotor", "Comp3Rotor", "Comp4Rotor")],
            ("revolve", "MainShaft", [(458, 86.1), (472, 86.3), (497, 55), (752, 55), (752, 49), (490, 49), (458, 82)]),
            ("revolve", "TurbineDisk", [(752, 0), (752, 60), (765, 70), (765, 81), (787, 81), (787, 70), (800, 60),
                                        (800, 10), (856, 10), (856, 0)]),
            *rows("R", C_OUTER, C_HUB, "Comp"), *rows("R", T_OUTER, T_HUB, "Turb")]


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    stators = [r for r in ROWS if r[1] == "S" and r[0].startswith("Comp")]
    exhaust_out = [(x, r + 5) for x, r in EXHAUST]
    return [
        ("nose_cone", "#2B2F36", [("spline", "NoseCone", [(3, 0), (10, 15), (25, 28), (50, 40), (80, 46), (110, 48)])]),
        ("inlet_housing", "#C9CED6", [  # one casting: shell, two struts, centrebody with gearbox and front bearing
            ("revolve", "InletShell", [(140, 101), (140, 124), (148, 124), (148, 130), (262, 130), (268, 112),
                                       (295, 112), (295, 99.2), (148, 101)]),
            ("revolve", "Centrebody", [(110, 42), (294, 42), (294, 48), (110, 48)]),
            ("ring", "InletStruts", 205, 45, 103, 114, 20, 2, 0),  # two struts (vibration, p. 5), x 148-262
            ("revolve", "Gearbox", [(150, 0), (250, 0), (250, 36), (155, 36), (155, 42), (150, 42)]),  # 5:1 fuel-pump drive
            ("revolve", "FrontBearingHousing", [(262, 26), (290, 26), (290, 42), (286, 42), (286, 34), (262, 34)]),
            ("pins", "TrunnionBosses", 205, 128, 146, 30, 2, 90)]),  # test-stand trunnion mounting bosses
        ("fuel_control", "#7C8288", [("ring", "FuelControl", 290, 131, 178, 220, 110, 1, 0)]),  # bolted on top (p. 12)
        ("compressor_casing", "#AEB5BF", [  # halves split axially; vane stems threaded through with lock nuts
            ("revolve", "CompCasing", C_OUTER + [(487, 124), (480, 124), (480, 110), (302, 110), (302, 124), (295, 124)]),
            ("ring", "SplitFlanges", 391, 108, 120, 178, 10, 2, 0, 90),
            *[("pins", f"{name}Nuts", x, 108, 116, 7, n) for name, _, x, n, *_ in stators]]),
        ("compressor_stators", "#7F8893", rows("S", C_OUTER, C_HUB, "Comp")),
        ("rotor", "#9AA3AD", rotor()),
        ("bearings", "#D4B04C", [
            ("revolve", "FrontBearing", [(268, 12.5), (283, 12.5), (283, 26), (268, 26)]),   # 205 ball, 25 x 52 x 15
            ("revolve", "RearBearing", [(841, 10), (855, 10), (855, 23.5), (841, 23.5)])]),  # 240 roller, 20 x 47 x 14
        ("combustor_housing", "#6B717A", [  # hydroformed sheet shell, flanges, two igniters
            ("revolve", "Housing", HOUSING + [(x, r + 2) for x, r in reversed(HOUSING)]),
            ("revolve", "HousingFwdFlange", [(487, 106.5), (494, 106.5), (494, 124), (487, 124)]),
            ("revolve", "HousingAftFlange", [(721, 130), (728, 130), (728, 146), (721, 146)]),
            ("pins", "Igniters", 570, 125, 150, 12, 2, 90)]),
        ("combustor_liner", "#A0522D", [  # liner with dome, snout, fuel manifold and 12 simplex nozzles
            ("revolve", "Liner", LINER),
            ("revolve", "Snout", [(480, 98), (547, 119), (547, 116.5), (484, 98), (547, 71.5), (547, 69)]),
            ("torus", "FuelManifold", 512, 93, 4),
            ("axial_pins", "FuelNozzles", 530, 93, 8, 30, 12),
            ("pins", "FuelFeed", 512, 95, 113, 6, 1)]),
        ("turbine_nozzle", "#8B5A3C", [  # one-piece 360° casting: vanes between shrouds, outer shroud over the rotor
            ("revolve", "InnerShroud", [(725, 79), (752, 79), (752, 82.8), (725, 82.8)]),
            ("revolve", "OuterShroud", [(725, 122.5), (752, 122.5), (752, 124), (800, 124), (800, 128), (725, 128)]),
            *[("loft", name, x, [(s[0] - 2 if i == 0 else s[0] + 2 if i == 2 else s[0], *s[1:])
                                 for i, s in enumerate(sections)], n)
              for _, name, x, sections, n in rows("S", T_OUTER, T_HUB, "Turb")]]),  # roots and tips sunk into the shrouds
        ("turbine_casing", "#5B636E", [("revolve", "TurbCasing", [(728, 128), (800, 128), (800, 143), (745, 143),
                                                                  (745, 146), (728, 146)])]),
        ("exhaust_casing", "#3A3F47", [  # cast duct, three airfoil struts on the tail cone
            ("revolve", "ExhaustDuct", EXHAUST + list(reversed(exhaust_out))),
            ("revolve", "DuctFwdFlange", [(800, 129), (808, 129), (808, 143), (800, 143)]),
            ("revolve", "DuctAftFlange", [(918, 103), (925, 100.5), (925, 115), (918, 115)])]),
        ("exhaust_nozzle", "#2B2F36", [("revolve", "Nozzle", [(925, 100), (965, 84), (965, 86), (931, 99.6), (931, 115),
                                                                (925, 115)])]),
        ("tail_cone", "#4A4F57", [
            ("revolve", "TailCone", shell(CENTREBODY, 3)),
            ("revolve", "RearBearingHousing", [(832, 23.5), (862, 23.5), (862, 54), (857, 57), (857, 30), (832, 30)]),
            ("fins", "ExhaustStruts", [(834.5, 50), (869.5, 45), *[(x, tip_radius(interp(EXHAUST, x), 0, 8, 0) - 0.2)
                                                                   for x in (869.5, 834.5)]], 8, 3)]),
    ]


@glb(out="../GLB/nasa_lewis_small_turbojet.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/nasa_lewis_small_turbojet.stl")
@step(out="../STEP/nasa_lewis_small_turbojet.step")
def nasa_lewis_small_turbojet():
    return assemble(parts(), "nasa_lewis_small_turbojet")


if __name__ == "__main__":
    nasa_lewis_small_turbojet()
