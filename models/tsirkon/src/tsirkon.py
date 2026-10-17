"""3M22 Tsirkon (Zircon): cutaway display model, as reconstructed from open sources.

32 parts in 5 sub-assemblies (launch_container, nose_section, second_stage, control_section, first_stage).

Sources (models/tsirkon/profile/, see its README.md):
  - Luftlage, "Not quite a diamond" (2026), reconstruction article/fig01.jpeg: ~8.5 m long, Ø0.67 m,
    two solid-propellant stages; composite second-stage casing, alloy rear section carrying four
    folding control fins, first stage with cable raceways / actuator-rod housings and jet vanes;
    dark nose tip, rows of screws at the section joints.
  - Luftlage side renders with and without the launch cap, article/fig03.jpeg: stations (9.94 mm/px).
  - Luftlage article/fig08.jpeg and patent RU2723276: metal closure ring set into the composite dome,
    held by a bolt circle; the nozzle bolted to the aft closure.
  - Kyiv forensic institute (KNDISE) side-view sketch, debris/twz_wreckage_2024-02-07.jpg: first
    pass; its larger first-stage fins are not in the newer Luftlage renders and are left out.
  - Patents: RU2722994 (upper-stage motor: nozzle continued by a long gas duct that flares at the
    aft end, braced to the outer shell by 3 spokes, fin actuators in the annulus around it);
    RU2776123 (nose inside the launch container under a two-piece protective shroud with a dome cap,
    also dashed in the KNDISE sketch).
Illustration level: parts are placed and proportioned from these sources; the grains are plain
cylindrical-bore cartridges and the payload is an empty placeholder volume. Station positions
~±50 mm; internal dimensions are estimates. Axis = +X from the nose tip. Units mm.
Assumed for appearance, not taken from the sources: the 120 mm nose tip as a separate part, the
internal bolted frames at the band / casing and casing / control-section joints (16 x M12 each), the
closure and nozzle-flange rings and their bolt circles (12 x M8), the screw rows (36 x Ø12 heads) at
the skin joints, the fin hinge fittings, the jet-vane shafts, the corner radii and chamfers, and the
finishes (lib/materials.py). Fasteners are a nut and stud end standing on a face, screw heads stand
on the skin; no holes are cut.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # models/, for the shared lib/

from cadgen import glb, step, stl
from lib.materials import finishes, groups, recipes
from lib.rocket import motor, ogive, polar_flange, shell, skin_screws, tube
from lib.shapes import assemble, flange_bolts, interp, tip_radius

R = 335.0              # body radius (Ø670)
LENGTH = 8500.0
# Stations from Luftlage's side renders (article/fig03.jpeg, 9.94 mm/px), which supersede the KNDISE sketch
NOSE_END = 1640.0      # white ogive ends, r 308
NOSE_R = 308.0
TIP_X = 120.0          # dark tip (fig01)
BAND_END = 2137.0      # light band out to full diameter
CONTROL_START = 4821.0  # composite casing ends; alloy control section ~3R long (matches RU2722994)
STAGE_JOINT = 5915.0
SKIN = 8.0             # radome / band / control-section wall
X_AXIS = (0, 0, 0), (1, 0, 0)

STAGE2 = motor("S2", xe0=2347, xe1=4600, r=R, t=10, a=150, port_fwd=60, port_aft=110, bore=120,
               throat=(4850, 88), exit=(5500, 88), skirts=[(BAND_END, 2347), (4600, CONTROL_START)])
# RU2722994: the nozzle continues as a straight gas duct, then flares out to the aft end of the section
STAGE2["nozzle"].append(("revolve", "S2DuctFlare", [(5500, 88), (5900, 288), (5900, 300), (5500, 100)]))
STAGE1 = motor("S1", xe0=6125, xe1=7900, r=R, t=10, a=150, port_fwd=60, port_aft=120, bore=130,
               throat=(8150, 80), exit=(8480, 270), skirts=[(STAGE_JOINT, 6125), (7900, LENGTH)])
NOSE = ogive(NOSE_END, NOSE_R, 20)

# internal joint frames: (forward frame x0, joint x, aft frame x1); bolts on the two outer faces
BAND_JOINT = (2097.0, BAND_END, 2177.0)
CONTROL_JOINT = (4781.0, CONTROL_START, 4861.0)
FRAME_R0, JOINT_BOLT_R = 250.0, 290.0


def lathed(ops, radius, chamfer=False):
    """The same ops with every revolve turned into a lathe (corners rounded or chamfered)."""
    return [("lathe", op[1], op[2], radius, *X_AXIS, chamfer) if op[0] == "revolve" else op for op in ops]


def span(pts, x0, x1):
    """Part of an (x, r) polyline between x0 and x1, end points interpolated."""
    return [(x0, interp(pts, x0))] + [p for p in pts if x0 < p[0] < x1] + [(x1, interp(pts, x1))]


def frame(name, x0, x1, r0, r1):
    return ("lathe", name, [(x0, r0), (x1, r0), (x1, r1), (x0, r1)], 3.0, *X_AXIS, True)


def joint_bolts(name, joint):
    x0, _, x1 = joint
    return flange_bolts(name, *X_AXIS, JOINT_BOLT_R, 12, 16, [(x0, -1), (x1, 1)])


def closure(name, stage, end):
    """Metal closure ring on a dome's polar opening (fig08) with its bolt circle; returns (ring ops, bolt ops)."""
    if end == "fwd":
        pts, r0, r1, depth, side = stage["fwd_dome"], 62.0, 150.0, -30.0, -1
    else:
        pts, r0, r1, depth, side = stage["aft_dome"], stage["aft_dome"][0][1] + 2, stage["aft_dome"][0][1] + 90, 25.0, 1
    ring = polar_flange(pts, r0, r1, depth)
    face = ring[0][0] + depth
    return ([("lathe", f"{name}Ring", ring, 3.0)],
            flange_bolts(name, *X_AXIS, (r0 + r1) / 2, 8, 12, [(face, side)]))


def screws(name, *xs):
    """Rows of screw heads on the Ø670 skin; 36 per row, clear of the fins and raceways (offset 5°)."""
    return [skin_screws(f"{name}{i + 1}", x, R, 12, 36, 5) for i, x in enumerate(xs)]


S2_CLOSURE, S2_CLOSURE_BOLTS = closure("S2Closure", STAGE2, "fwd")
S2_FLANGE, S2_FLANGE_BOLTS = closure("S2NozzleFlange", STAGE2, "aft")
S1_CLOSURE, S1_CLOSURE_BOLTS = closure("S1Closure", STAGE1, "fwd")
S1_FLANGE, S1_FLANGE_BOLTS = closure("S1NozzleFlange", STAGE1, "aft")


def spec():
    """[(sub-assembly, part label, finish, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    case2 = [op for op in STAGE2["case"] if "Skirt" not in op[1]] + lathed([op for op in STAGE2["case"] if "Skirt" in op[1]], 2.0, True)
    case1 = [op for op in STAGE1["case"] if "Skirt" not in op[1]] + lathed([op for op in STAGE1["case"] if "Skirt" in op[1]], 2.0, True)
    return [
        ("launch_container", "launch_shroud", "paint_olive", [  # RU2776123 + fig03: cap ~body diameter, ~1.4 m, dropped at launch
            ("lathe", "Shroud", [(-50, 0), (-35, 150), (0, 250), (40, 315), (80, 340), (1150, 340), (1300, 313),
                                 (1300, 305), (1150, 332), (80, 332), (40, 307), (0, 242), (-35, 142), (-42, 0)], 3.0)]),

        ("nose_section", "nose_tip", "graphite", [  # fig01: dark tip
            ("revolve", "NoseTip", [p for p in NOSE if p[0] < TIP_X] + [(TIP_X, interp(NOSE, TIP_X)), (TIP_X, 0)])]),
        ("nose_section", "radome", "radome", [("lathe", "Radome", shell(span(NOSE, TIP_X, NOSE_END), SKIN), 2.0)]),
        ("nose_section", "seeker", "machined_steel", [  # active radar seeker: gimballed antenna plate
            ("lathe", "Antenna", [(450, 0), (470, 0), (470, 120), (450, 120)], 3.0),
            ("lathe", "Gimbal", [(470, 0), (650, 0), (650, 60), (470, 60)], 6.0)]),
        ("nose_section", "guidance_electronics", "electronics", [
            ("lathe", "Electronics", [(900, 0), (1500, 0), (1500, 170), (900, 170)], 12.0)]),
        ("nose_section", "band", "paint_grey", [
            ("lathe", "Band", [(NOSE_END, NOSE_R - SKIN), (BAND_END, R - SKIN), (BAND_END, R), (NOSE_END, NOSE_R)], 2.0, *X_AXIS, True),
            frame("BandAftFrame", BAND_JOINT[0], BAND_END, FRAME_R0, R - SKIN + 1)]),
        ("nose_section", "payload_bay", "inert", [  # placeholder volume only, clear of the band joint bolts
            ("lathe", "PayloadBay", [(1700, 0), (2070, 0), (2070, 316), (1700, 295)], 10.0)]),
        ("nose_section", "band_joint_bolts", "fastener", joint_bolts("BandJoint", BAND_JOINT)),

        ("second_stage", "stage2_case", "composite", case2 + [
            frame("S2FwdFrame", BAND_END, BAND_JOINT[2], FRAME_R0, R - 10 + 1),
            frame("S2AftFrame", CONTROL_JOINT[0], CONTROL_START, FRAME_R0, R - 10 + 1)]),
        ("second_stage", "stage2_closure", "tint_bronze", S2_CLOSURE),
        ("second_stage", "stage2_closure_bolts", "fastener", S2_CLOSURE_BOLTS),
        ("second_stage", "stage2_grain", "propellant", STAGE2["grain"]),
        ("second_stage", "stage2_igniter", "brass", lathed(STAGE2["igniter"], 4.0)),
        ("second_stage", "stage2_nozzle_flange", "cast_alloy", S2_FLANGE),
        ("second_stage", "stage2_nozzle_flange_bolts", "fastener", S2_FLANGE_BOLTS),
        ("second_stage", "stage2_nozzle_duct", "nozzle_alloy", lathed(STAGE2["nozzle"], 3.0)),
        ("second_stage", "stage2_skin_screws", "fastener", screws("S2Screws", BAND_END + 25, CONTROL_START - 25)),

        ("control_section", "control_skin", "polished_alloy", [  # alloy skin and 3 duct-bracing spokes (RU2722994)
            ("lathe", "ControlSkin", tube(CONTROL_START, STAGE_JOINT, R, SKIN), 2.0, *X_AXIS, True),
            frame("ControlFwdFrame", CONTROL_START, CONTROL_JOINT[2], FRAME_R0, R - SKIN + 1),
            ("ring", "DuctSpokes", 5450, 110, R - SKIN + 1, 30, 8, 3, 0, 60)]),
        ("control_section", "control_fins", "machined_steel", [
            # folding fins in the stowed position (fig03: ~95 mm proud of the skin); deployed shape not published
            ("fins", "ControlFins", [(5190, R - 5), (5880, R + 95), (5914, R + 95), (5914, R - 5)], 14, 4),
            ("ring", "FinHingeFittings", 5300, R - 10, R + 28, 180, 40, 4, 0),
            ("cut", "FinRoots", [(5100, 0), (6000, 0), (6000, R), (5100, R)])]),  # roots follow the skin
        ("control_section", "fin_actuators", "dark_steel", [("ring", "FinActuators", 5200, 110, tip_radius(R - SKIN, 120, 70, 0), 120, 70, 4, 0)]),
        ("control_section", "control_joint_bolts", "fastener", joint_bolts("ControlJoint", CONTROL_JOINT)),
        ("control_section", "control_skin_screws", "fastener", screws("ControlScrews", CONTROL_START + 25, STAGE_JOINT - 25)),

        ("first_stage", "stage1_case", "cast_alloy", case1 + [("ring", "Raceways", 7175, R - 5, R + 25, 2350, 60, 4, 0, 45)]),
        ("first_stage", "stage1_closure", "tint_bronze", S1_CLOSURE),
        ("first_stage", "stage1_closure_bolts", "fastener", S1_CLOSURE_BOLTS),
        ("first_stage", "stage1_grain", "propellant", STAGE1["grain"]),
        ("first_stage", "stage1_igniter", "brass", lathed(STAGE1["igniter"], 4.0)),
        ("first_stage", "stage1_nozzle_flange", "cast_alloy", S1_FLANGE),
        ("first_stage", "stage1_nozzle_flange_bolts", "fastener", S1_FLANGE_BOLTS),
        ("first_stage", "stage1_nozzle", "nozzle_alloy", lathed(STAGE1["nozzle"], 3.0)),
        ("first_stage", "jet_vanes", "graphite", [  # in the plume at the nozzle exit, shafts out through the skirt end
            ("ring", "JetVanes", 8520, 60, 240, 100, 10, 4, 0),
            ("pins", "VaneShafts", 8520, 230, R - 5, 20, 4)]),
        ("first_stage", "stage1_skin_screws", "fastener", screws("S1Screws", STAGE_JOINT + 25, LENGTH - 25)),
    ]


SPEC = spec()
GROUPS = groups(SPEC)
MATERIALS = finishes(SPEC)


def parts():
    """[(label, colour, ops)] for assemble() and the native CAD builders."""
    return recipes(SPEC)


@glb(out="../GLB/tsirkon.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/tsirkon.stl")
@step(out="../STEP/tsirkon.step", materials=MATERIALS)
def tsirkon():
    return assemble(parts(), "3M22 Tsirkon", GROUPS)


if __name__ == "__main__":
    tsirkon()
