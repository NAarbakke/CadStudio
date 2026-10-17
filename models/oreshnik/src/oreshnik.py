"""Oreshnik IRBM: cutaway display model, as reconstructed from open sources.

Sources (models/oreshnik/profile/, see its README.md):
  - Luftlage, "The missile that came in from the cold" (2026), article/:
    fig01 reconstruction (~13 m, Ø1.61 m, two solid stages derived from the Yars 2nd/3rd stages),
    stations read from its side view at 12.23 mm/px (13 m over the 1063 px drawn, tip at px 1298);
    fig08 the same markings on the full Yars reconstruction (what each joint mark belongs to);
    fig02 post-boost control system (PBCS) from debris: attachment ring with separation mechanism,
    central solid-propellant gas generator, four valve blocks with nozzles, struts, actuators;
    fig03 instrumentation compartment (IC): sealed drum with a lattice end plate, like the RT-2PM
    Topol / START-1 adapter; text: IC "installed on top of the PBCS", RVs "on a frame attached to
    the top of the IC", 36 objects in six clusters.
  - web/: Defence Blog / UNITED24 (May 2026): deployment unit for six RVs; DB_image_930 IC debris
    (electronics inside the drum, PBCS chamber on it); Militarnyi: gyro-platform remnants.
  - references/START-1_user_handbook_vol1.pdf: p.3 fig 1-1 and §1.2 (head module on the front face
    of the platform, sealed IC, propulsion module with the post-boost gas generator behind it),
    p.26-27 fig 3-1/3-2 (fairing support ring; adapter "bottom" with the lattice).
  - references/START MOU 1998 Annex F: Topol-M 2nd stage Ø1.61 m, 3rd stage Ø1.58 m.
  - patents/RU2743670 (post-boost gas generator: case with front dome, end-burning charge, cover with
    nozzle blocks), RU2703556 (two-outlet gas valve: inlet pipe, two nozzle outlets, driven spool).
Stations (fig01 px -> mm from the tip): orange nose-cap ring px 1230-1234 (805); fairing base / light
band px 1036-1054 (2990-3210); notched silver ring px 916-924 (4568-4678); dashed joint px 726-733
(6950), start of the Ø1.58 -> Ø1.61 taper that ends at the dashed joint px 597-603 (8540); thin
silver line px 339-342 (11710); body end px 248.5 (12835) with the nozzle exit showing to 13000
(Ø1.39 m, 114 px). Reading (fig08, START-1 layout): 2990-3210 IC band; 3210-4568 PBV propulsion-module
shell; 4568-4678 PBCS attachment ring = PBV / upper-stage separation; 6950 stage separation; the
6950-8540 taper is the interstage; 8540 and ~11700 are the lower stage's case / skirt joints.
Parts (35 in 5 sub-assemblies): nose_section (nose_tip, nose_cap, nose_fairing, payload, fairing joint
bolts), instrument_compartment (ic_shell, ic_instruments, joint bolts, skin screws), post_boost_vehicle
(pbv_shell, post_boost_stage, pbcs_charge, joint bolts), second_stage and first_stage (case, closure
ring, grain, igniter, nozzle flange, nozzle, bolt circles, skin screws; the first stage also carries the
interstage and aft_skirt).
Assumed (no source gives them): wall 15 mm, frame depths 20-40 mm; motor dome depths 400 mm, domes and
grain bores (plain cylindrical cartridges); upper-stage case equators at 5200 (clear of the PBCS) and
6600; nozzle throats and bell angles (only the lower exit is drawn); PBCS sizes are fig02 proportions
scaled to its Ø1.58 m ring (chamber Ø0.73 m, valve blocks at r 550); the forward-firing nozzles are
drawn axial (fig02 cants them outward; the op set has no canted solids); the lattice is 30 mm ribs at
110 mm pitch (fig03: ~12 cells across); IC contents, RV frame and the six RV cones are placeholders.
Also assumed for appearance: the metal closure rings on the motor domes and the nozzle flanges (12 x M16
bolts each, after Tsirkon's RU2723276 pattern), the 36 x M14 bolt circles on the internal joint frames,
the 48-head screw rows at the skin joints, the corner radii and chamfers, and the finishes
(lib/materials.py). Fasteners are a nut and stud end standing on a face, screw heads stand on the skin;
no holes are cut.
Axis = +X from the tip. Units mm.
"""
from math import atan, cos, radians, sin, sqrt, tan

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # models/, for the shared lib/

from cadgen import glb, step, stl
from lib.materials import finishes, groups, recipes
from lib.rocket import dome, motor, polar_flange, shell, skin_screws, smooth, tube
from lib.shapes import assemble, flange_bolts, interp

R = 805.0              # Ø1.61 m: lower stage (Yars/Topol-M 2nd-stage diameter, START MOU)
R2 = 790.0             # Ø1.58 m: upper stage, PBV and fairing base (3rd-stage diameter, START MOU)
T = 15.0               # skin / case wall (assumed)
LENGTH = 13000.0
CAP_END = 805.0        # nose cap / fairing joint (fig01 orange ring)
FAIRING_END = 2990.0   # fairing base = IC band front edge (fig01 px 1054)
BAND_END = 3210.0      # IC band aft edge (px 1036)
RING = (4568.0, 4678.0)  # PBCS attachment ring (fig01 notched silver ring, px 916-924)
STAGE_JOINT = 6950.0   # stage separation (dashed joint px 726-733; the Ø taper starts here)
S1_FWD = 8540.0        # lower-stage case front joint, end of the taper (dashed joint px 597-603)
SKIRT = 11740.0        # aft skirt joint (fig01 thin silver line px 339-342 = 11686-11730)
BODY_END = 12835.0     # aft skirt end, nozzle exit visible behind it (px 248.5)

# fig01 top edge (x, r) at drawing scale (body 1.64 m there): blunt tip rho 210 mm (r 73/122/146 at
# 12/37/61 mm), then an 18.4° cone to ~1.1 m (the 0.2-0.56 m blisters are left out), then the ogive.
TIP_RHO, CONE = 210.0, atan(0.332)
TIP_X = TIP_RHO * (1 - sin(CONE))
FAIRING_PX = [(TIP_X, TIP_RHO * cos(CONE)), (575, 342), (868, 440), (1162, 535), (1455, 610), (1749, 673),
              (2042, 720), (2336, 758), (2629, 782), (2923, 795), (FAIRING_END, 795)]
K = R2 / 795           # drawing -> model radius: fairing base = R2
TIP = [(TIP_RHO * (1 - cos(a)), TIP_RHO * sin(a)) for a in ((radians(90) - CONE) * i / 6 for i in range(7))]
OUTER = [(x, r * K) for x, r in TIP[:-1] + smooth(FAIRING_PX)]

# payload (placeholders): six cones on a mounting plate, frame struts to the IC front frame
X_AXIS = (0, 0, 0), (1, 0, 0)
JOINT_R, JOINT_BOLT = 760.0, 14  # bolt circle radius and size on the internal joint frames
PLATE_X = 2820.0
# instrumentation compartment: lattice end plate (fig03), shallow dome, rib grid at 45° (fig03 / START-1 fig 3-2)
LAT_R, LAT_X, LAT_SAG, LAT_T, RIB_H, RIB_PITCH, RIB_T = 650.0, 3000.0, 70.0, 10.0, 30.0, 110.0, 8.0
LAT_RS = [0, 100, 200, 300, 400, 500, 600, LAT_R]
# PBCS (fig02 proportions of the Ø1.58 m ring: chamber 0.46, flange 0.49, valve blocks 0.7, flange plane 0.19 R fwd)
RING_FACE = RING[1]
PB_RC, PB_FLANGE, PB_RV = 365.0, 390.0, 550.0
PB_X = RING_FACE - 150.0   # 4528: case / cover flange plane
PB_CASE = (4368.0, 270.0)  # case cylinder front end, front dome depth (fig02 bowl ~1.1 R below the flange)
PB_COVER = (4556.0, 190.0)  # cover equator, dome depth (RU2743670 fig 1: cover ~0.5 R)

STAGE2 = motor("S2", xe0=5200, xe1=6600, r=R2, t=T, a=400, port_fwd=150, port_aft=250, bore=300,
               throat=(7120, 170), exit=(7900, 560), t_nozzle=T, skirts=[(RING_FACE, 5200), (6600, STAGE_JOINT)])
STAGE1 = motor("S1", xe0=S1_FWD, xe1=11650, r=R, t=T, a=400, port_fwd=150, port_aft=300, bore=300,
               throat=(12200, 195), exit=(LENGTH, 682), t_nozzle=T, skirts=[(11650, SKIRT)])


def span(pts, x0, x1):
    """Part of an (x, r) polyline between x0 and x1, end points interpolated."""
    return [(x0, interp(pts, x0))] + [p for p in pts if x0 < p[0] < x1] + [(x1, interp(pts, x1))]


def frame(name, x0, x1, r0, r1):
    return ("lathe", name, [(x0, r0), (x1, r0), (x1, r1), (x0, r1)], 3.0, *X_AXIS, True)


def bell(p0, p2, a0, a1, n=8):
    """Quadratic Bezier from the throat p0 (leaving at a0°) to the exit p2 (arriving at a1°)."""
    (x0, r0), (x2, r2) = p0, p2
    k0, k1 = tan(radians(a0)), tan(radians(a1))
    x1 = (r2 - r0 + k0 * x0 - k1 * x2) / (k0 - k1)
    p1 = (x1, r0 + k0 * (x1 - x0))
    return [tuple((1 - s) ** 2 * a + 2 * s * (1 - s) * b + s ** 2 * c for a, b, c in zip(p0, p1, p2))
            for s in (i / n for i in range(n + 1))]


def nozzle(name, stage, throat, exit, a0, a1, sub=150.0, t=T):
    """Replaces motor()'s straight cone: entry submerged in the bore, thick throat, bell exit (fig01 lip)."""
    (xa, ra) = stage["nozzle"][0][2][0]  # motor(): nozzle starts at the aft polar opening
    inner = bell(throat, exit, a0, a1)
    outer = [(x, r + t) for x, r in inner[1:-1]]
    (xt, rt), (xx, rx) = throat, exit
    pts = [(xa - sub, ra - 2 * t)] + inner + [(xx, rx + t)] + outer[::-1] + [(xt, rt + 2.5 * t), (xa, ra), (xa - sub, ra - t)]
    return [("lathe", f"{name}Nozzle", pts, 3.0)]


def lat_x(r):
    return LAT_X - LAT_SAG * (1 - (r / LAT_R) ** 2)


def lattice():
    """fig03: ribs laid as boxes (4 per pitch step), then trimmed to stand RIB_H proud of the dome."""
    surf = [(lat_x(r), r) for r in LAT_RS]
    xc = (lat_x(0) - RIB_H + LAT_X) / 2
    ops = [("ring", f"LatticeRibs{k + 1}", xc, y - RIB_T / 2, y + RIB_T / 2, LAT_SAG + RIB_H + 20,
            2 * sqrt(LAT_R ** 2 - y ** 2) + 40, 4, 0, 45)
           for k, y in enumerate(RIB_PITCH * (i + 0.5) for i in range(round(LAT_R / RIB_PITCH)))]
    return ops + [
        ("cut", "LatticeRibTops", [(2800, 0)] + [(x - RIB_H, r) for x, r in surf] + [(3100, LAT_R), (3100, 800), (2800, 800)]),
        ("cut", "LatticeRibRoots", surf + [(3100, LAT_R), (3100, 0)]),
        ("lathe", "LatticePlate", surf + [(x + LAT_T, r) for x, r in reversed(surf)], 3.0)]


def gas_generator():
    """RU2743670 layout: case with front dome (forward, fig02 bowl) + bolted flange + domed cover (aft)."""
    (xc, a), (xv, av), t = PB_CASE, PB_COVER, 12.0
    fwd_o, fwd_i = dome(xc, PB_RC, a, 0, True), dome(xc, PB_RC - t, a - t, 0, True)
    cov_o, cov_i = dome(xv, PB_RC, av, 0, False), dome(xv, PB_RC - t, av - t, 0, False)
    outer = fwd_o + [(PB_X - 10, PB_RC), (PB_X - 10, PB_FLANGE), (xv, PB_FLANGE)] + cov_o[::-1]
    inner = cov_i + fwd_i[::-1]
    return [("lathe", "GasGenerator", outer + inner, 3.0)], fwd_i


def nozzle_cup(x0, x1):
    """fig02 thruster cup about its own axis: collar at x0, exit Ø190 at x1 (either direction)."""
    s = 1 if x1 > x0 else -1
    return [(x0, 35), (x1, 85), (x1, 97), (x0 + 30 * s, 62), (x0 + 30 * s, 72), (x0, 72)]


GG_OPS, GG_INNER = gas_generator()


def lathed(ops, radius, chamfer=False):
    """The same ops with every revolve turned into a lathe (corners rounded or chamfered)."""
    return [("lathe", op[1], op[2], radius, *X_AXIS, chamfer) if op[0] == "revolve" else op for op in ops]


def bolts(name, r, n, *faces, size=JOINT_BOLT):
    """Bolt circle on the given (x, side) faces of internal joint frames."""
    return flange_bolts(name, *X_AXIS, r, size, n, list(faces))


def closure(name, stage, end):
    """Metal closure ring on a motor dome's polar opening with its bolt circle; returns (ring ops, bolt ops)."""
    if end == "fwd":
        pts, depth, side = stage["fwd_dome"], -30.0, -1
    else:
        pts, depth, side = stage["aft_dome"], 25.0, 1
    r0 = pts[0][1] + 2
    r1 = r0 + 90
    ring = polar_flange(pts, r0, r1, depth)
    return ([("lathe", f"{name}Ring", ring, 3.0)],
            flange_bolts(name, *X_AXIS, (r0 + r1) / 2, 12, 16, [(ring[0][0] + depth, side)]))


def screws(name, r, *xs):
    """Rows of screw heads on the skin; 48 per row, offset 3.75 deg from the joint bolts."""
    return [skin_screws(f"{name}{i + 1}", x, r, 14, 48, 3.75) for i, x in enumerate(xs)]


S2_CLOSURE, S2_CLOSURE_BOLTS = closure("S2Closure", STAGE2, "fwd")
S2_FLANGE, S2_FLANGE_BOLTS = closure("S2NozzleFlange", STAGE2, "aft")
S1_CLOSURE, S1_CLOSURE_BOLTS = closure("S1Closure", STAGE1, "fwd")
S1_FLANGE, S1_FLANGE_BOLTS = closure("S1NozzleFlange", STAGE1, "aft")


def spec():
    """[(sub-assembly, part label, finish, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    case2 = [op for op in STAGE2["case"] if "Skirt" not in op[1]] + lathed([op for op in STAGE2["case"] if "Skirt" in op[1]], 2.0, True)
    case1 = [op for op in STAGE1["case"] if "Skirt" not in op[1]] + lathed([op for op in STAGE1["case"] if "Skirt" in op[1]], 2.0, True)
    return [
        ("nose_section", "nose_tip", "ablative", [("revolve", "NoseTip", [p for p in OUTER if p[0] <= TIP_X] + [(TIP_X, 0)])]),  # fig01 orange tip
        ("nose_section", "nose_cap", "graphite", [("lathe", "NoseCap", shell(span(OUTER, TIP_X, CAP_END), T), 2.0)]),
        ("nose_section", "nose_fairing", "composite", [
            ("lathe", "Fairing", shell(span(OUTER, CAP_END, FAIRING_END), T), 2.0),
            frame("FairingBaseRing", 2930, FAIRING_END, 755, R2 - T + 2)]),  # START-1 fig 3-1 support ring
        ("nose_section", "payload", "inert", [  # six RVs (Defence Blog 2026) as cones on a plate; frame on the IC (article text)
            ("offset_ring", "PayloadCones", [(PLATE_X - 1350, 0), (PLATE_X, 190), (PLATE_X, 0)], 400, 6),
            ("lathe", "MountPlate", [(PLATE_X, 0), (PLATE_X + 30, 0), (PLATE_X + 30, 620), (PLATE_X, 620)], 6.0),
            ("fins", "FrameStruts", [(PLATE_X + 30, 560), (PLATE_X + 30, 620), (FAIRING_END, 750), (FAIRING_END, 690)], 40, 6)]),
        ("nose_section", "fairing_joint_bolts", "fastener", bolts("FairingJoint", JOINT_R - 2, 36, (2930, -1))),

        ("instrument_compartment", "ic_shell", "paint_grey", lattice() + [  # sealed drum: fig01 band, fig03 lattice top
            ("lathe", "InstrumentShell", tube(FAIRING_END, BAND_END, R2, T), 2.0, *X_AXIS, True),
            frame("IcFwdFrame", FAIRING_END, 3030, LAT_R, R2 - T + 1),
            frame("IcAftFrame", 3170, BAND_END, 730, R2 - T + 1),
            ("lathe", "IcAftBulkhead", dome(BAND_END, 740, 170, 0, False) + dome(BAND_END, 730, 160, 0, False)[::-1], 3.0)]),
        ("instrument_compartment", "ic_instruments", "electronics", [  # placeholders: gyro platform (article, Militarnyi), electronics (DB_image_930)
            ("lathe", "InstrumentDeck", [(3030, 0), (3040, 0), (3040, 770), (3030, 770)], 2.0),
            ("lathe", "GyroPlatform", [(3040, 0), (3290, 0), (3290, 230), (3040, 230)], 8.0),
            ("ring", "Electronics", 3110, 300, 560, 140, 180, 8, 0, 22.5)]),
        ("instrument_compartment", "ic_joint_bolts", "fastener", bolts("IcJoint", JOINT_R, 36, (3170, -1), (3260, 1))),
        ("instrument_compartment", "ic_skin_screws", "fastener", screws("IcScrews", R2, FAIRING_END + 30, BAND_END - 30)),

        ("post_boost_vehicle", "pbv_shell", "hot_alloy", [  # START-1 fig 1-1 item 4: propulsion module between IC and PBCS ring
            ("lathe", "PbvShell", tube(BAND_END, RING[0], R2, T), 2.0, *X_AXIS, True),
            frame("PbvFwdFrame", BAND_END, 3260, 745, R2 - T + 1),
            frame("PbvAftFrame", RING[0] - 50, RING[0], 745, R2 - T + 1)]),
        ("post_boost_vehicle", "post_boost_stage", "cast_alloy", GG_OPS + [  # fig02; valve blocks per RU2703556 (inlet + two outlets)
            ("lathe", "AttachRing", [(RING[0], 770), (RING_FACE - 30, 770), (RING_FACE - 30, 700), (RING_FACE, 700),
                                     (RING_FACE, R2), (RING[0], R2)], 3.0),
            ("ring", "SeparationFittings", 4600, 735, 772, 50, 50, 16, 0, 11.25),  # fig01: 16 notches in the ring
            ("axial_pins", "GuidePins", RING_FACE + 20, 715, 24, 40, 4, 22.5),  # fig02: 4 pins on the aft face
            ("ring", "Struts", 4610, 340, 772, 80, 50, 4, 0, 45),  # aft of the PBV frame, which ends at RING[0]
            ("pins", "GasPipes", 4600, 300, PB_RV, 80, 4),
            ("axial_pins", "ValveHousings", 4600, PB_RV, 150, 160, 4),
            ("offset_ring", "AftNozzles", nozzle_cup(4680, 4830), PB_RV, 4),
            ("offset_ring", "FwdNozzles", nozzle_cup(4520, 4370), PB_RV, 4),
            ("ring", "Actuators", 4470, 590, 690, 100, 110, 4, 0, 22),
            ("pins", "Igniter", 4550, 330, 470, 60, 1, 67.5)]),
        ("post_boost_vehicle", "pbcs_charge", "propellant",
         lathed([("revolve", "EndBurningCharge", GG_INNER + [(4500, PB_RC - 12), (4500, 0)])], 3.0)),
        ("post_boost_vehicle", "pbv_joint_bolts", "fastener", bolts("PbvJoint", JOINT_R, 36, (RING[0] - 50, -1))),

        ("second_stage", "stage2_case", "composite", case2 + [
            frame("S2FwdFrame", RING_FACE, RING_FACE + 50, 740, R2 - T + 1),
            frame("S2AftFrame", STAGE_JOINT - 60, STAGE_JOINT, 735, R2 - T + 1)]),
        ("second_stage", "stage2_closure", "tint_bronze", S2_CLOSURE),
        ("second_stage", "stage2_closure_bolts", "fastener", S2_CLOSURE_BOLTS),
        ("second_stage", "stage2_grain", "propellant", STAGE2["grain"]),
        ("second_stage", "stage2_igniter", "brass", lathed(STAGE2["igniter"], 4.0)),
        ("second_stage", "stage2_nozzle_flange", "cast_alloy", S2_FLANGE),
        ("second_stage", "stage2_nozzle_flange_bolts", "fastener", S2_FLANGE_BOLTS),
        ("second_stage", "stage2_nozzle", "nozzle_alloy", nozzle("S2", STAGE2, (7120, 170), (7900, 560), 35, 15)),
        ("second_stage", "stage2_joint_bolts", "fastener",
         bolts("S2Joint", JOINT_R, 36, (RING_FACE + 50, 1), (STAGE_JOINT - 60, -1))),
        ("second_stage", "stage2_skin_screws", "fastener", screws("S2Screws", R2, RING_FACE + 80, STAGE_JOINT - 30)),

        ("first_stage", "stage1_case", "cast_alloy", case1 + [  # interstage: fig01 taper Ø1.58 -> Ø1.61 from 6950 to 8540
            ("lathe", "S1Interstage", [(STAGE_JOINT, R2 - T), (S1_FWD, R - T), (S1_FWD, R), (STAGE_JOINT, R2)], 2.0, *X_AXIS, True),
            frame("S1InterstageFrame", STAGE_JOINT, STAGE_JOINT + 60, 735, R2 - T + 2)]),
        ("first_stage", "stage1_closure", "tint_bronze", S1_CLOSURE),
        ("first_stage", "stage1_closure_bolts", "fastener", S1_CLOSURE_BOLTS),
        ("first_stage", "stage1_grain", "propellant", STAGE1["grain"]),
        ("first_stage", "stage1_igniter", "brass", lathed(STAGE1["igniter"], 4.0)),
        ("first_stage", "stage1_nozzle_flange", "cast_alloy", S1_FLANGE),
        ("first_stage", "stage1_nozzle_flange_bolts", "fastener", S1_FLANGE_BOLTS),
        ("first_stage", "stage1_nozzle", "nozzle_alloy", nozzle("S1", STAGE1, (12200, 195), (LENGTH, 682), 42, 18)),  # exit Ø1.39 m (fig01)
        ("first_stage", "aft_skirt", "machined_steel", [
            ("lathe", "AftSkirt", tube(SKIRT, BODY_END, R, T), 2.0, *X_AXIS, True),
            frame("AftSkirtRing", BODY_END - 60, BODY_END, 745, R - T + 1)]),
        ("first_stage", "first_stage_joint_bolts", "fastener",
         bolts("S1Joint", JOINT_R, 36, (STAGE_JOINT + 60, 1)) + bolts("S1Skirt", JOINT_R + 6, 36, (BODY_END - 60, -1))),
        ("first_stage", "stage1_skin_screws", "fastener", screws("S1Screws", R, S1_FWD + 40, SKIRT + 30, BODY_END - 30)),
    ]


SPEC = spec()
GROUPS = groups(SPEC)
MATERIALS = finishes(SPEC)


def parts():
    """[(label, colour, ops)] for assemble() and the native CAD builders."""
    return recipes(SPEC)


@glb(out="../GLB/oreshnik.glb", mesh_tolerance=6e-4, mesh_angular_tolerance=0.25)
@stl(out="../STL/oreshnik.stl")
@step(out="../STEP/oreshnik.step", materials=MATERIALS)
def oreshnik():
    return assemble(parts(), "oreshnik", GROUPS)


if __name__ == "__main__":
    oreshnik()
