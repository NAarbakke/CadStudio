"""3M22 Tsirkon (Zircon): cutaway display model, as reconstructed from open sources.

Sources (profile_builder/Tsirkon/resources/, see its README.md):
  - Luftlage, "Not quite a diamond" (2026), reconstruction article/fig01.jpeg: ~8.5 m long, Ø0.67 m,
    two solid-propellant stages; composite second-stage casing, alloy rear section carrying four
    folding control fins, first stage with cable raceways / actuator-rod housings and jet vanes.
  - Luftlage side renders with and without the launch cap, article/fig03.jpeg: stations (9.94 mm/px).
  - Kyiv forensic institute (KNDISE) side-view sketch, debris/twz_wreckage_2024-02-07.jpg: first
    pass; its larger first-stage fins are not in the newer Luftlage renders and are left out.
  - Patents: RU2722994 (upper-stage motor: nozzle continued by a long gas duct that flares at the
    aft end, braced to the outer shell by 3 spokes, fin actuators in the annulus around it);
    RU2723276 (wound case, bolted nozzle flange); RU2776123 (nose inside the launch container under
    a two-piece protective shroud with a dome cap, also dashed in the KNDISE sketch).
Illustration level: parts are placed and proportioned from these sources; the grains are plain
cylindrical-bore cartridges and the payload is an empty placeholder volume. Station positions
~±50 mm; internal dimensions are estimates. Axis = +X from the nose tip. Units mm.
"""
from cadgen import glb, step, stl
from lib.rocket import motor, ogive, shell, tube
from lib.shapes import assemble, tip_radius

R = 335.0              # body radius (Ø670)
LENGTH = 8500.0
# Stations from Luftlage's side renders (article/fig03.jpeg, 9.94 mm/px), which supersede the KNDISE sketch
NOSE_END = 1640.0      # white ogive ends, r 308
NOSE_R = 308.0
BAND_END = 2137.0      # light band out to full diameter
CONTROL_START = 4821.0  # composite casing ends; alloy control section ~3R long (matches RU2722994)
STAGE_JOINT = 5915.0
SKIN = 8.0             # radome / band / control-section wall

STAGE2 = motor("S2", xe0=2347, xe1=4600, r=R, t=10, a=150, port_fwd=60, port_aft=110, bore=120,
               throat=(4850, 88), exit=(5500, 88), skirts=[(BAND_END, 2347), (4600, CONTROL_START)])
# RU2722994: the nozzle continues as a straight gas duct, then flares out to the aft end of the section
STAGE2["nozzle"].append(("revolve", "S2DuctFlare", [(5500, 88), (5900, 288), (5900, 300), (5500, 100)]))
STAGE1 = motor("S1", xe0=6125, xe1=7900, r=R, t=10, a=150, port_fwd=60, port_aft=120, bore=130,
               throat=(8150, 80), exit=(8480, 270), skirts=[(STAGE_JOINT, 6125), (7900, LENGTH)])


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    return [
        ("launch_shroud", "#8FA37A", [  # RU2776123 + fig03: cylindrical cap ~body diameter, ~1.4 m, dropped at launch
            ("revolve", "Shroud", [(-50, 0), (-35, 150), (0, 250), (40, 315), (80, 340), (1150, 340), (1300, 313),
                                   (1300, 305), (1150, 332), (80, 332), (40, 307), (0, 242), (-35, 142), (-42, 0)])]),
        ("radome", "#E6E8EB", [("revolve", "Radome", shell(ogive(NOSE_END, NOSE_R), SKIN))]),
        ("seeker", "#C08A3E", [  # active radar seeker: gimballed antenna plate
            ("revolve", "Antenna", [(450, 0), (470, 0), (470, 120), (450, 120)]),
            ("revolve", "Gimbal", [(470, 0), (650, 0), (650, 60), (470, 60)])]),
        ("guidance_electronics", "#4F7A5A", [("revolve", "Electronics", [(900, 0), (1500, 0), (1500, 170), (900, 170)])]),
        ("band", "#DADDE1", [("revolve", "Band", [(NOSE_END, NOSE_R - SKIN), (BAND_END, R - SKIN), (BAND_END, R), (NOSE_END, NOSE_R)])]),
        ("payload_bay", "#8C5A5A", [  # placeholder volume only
            ("revolve", "PayloadBay", [(1700, 0), (2130, 0), (2130, 318), (1700, 295)])]),
        ("stage2_case", "#6B6655", STAGE2["case"]),
        ("stage2_grain", "#B89A6A", STAGE2["grain"]),
        ("stage2_igniter", "#D05A3A", STAGE2["igniter"]),
        ("stage2_nozzle_duct", "#8A8F96", STAGE2["nozzle"]),
        ("control_section", "#B9BEC4", [  # alloy skin, folding fins, 3 duct-bracing spokes (RU2722994)
            ("revolve", "ControlSkin", tube(CONTROL_START, STAGE_JOINT, R, SKIN)),
            # folding fins in the stowed position (fig03: ~95 mm proud of the skin); deployed shape not published
            ("fins", "ControlFins", [(5190, R - 5), (5880, R + 95), (5914, R + 95), (5914, R - 5)], 14, 4),
            ("ring", "DuctSpokes", 5450, 110, R - SKIN + 1, 30, 8, 3, 0, 60)]),
        ("fin_actuators", "#5E6B7A", [("ring", "FinActuators", 5200, 110, tip_radius(R - SKIN, 120, 70, 0), 120, 70, 4, 0)]),
        ("stage1_case", "#C9CED6", STAGE1["case"] + [("ring", "Raceways", 7175, R - 5, R + 25, 2350, 60, 4, 0, 45)]),
        ("stage1_grain", "#B89A6A", STAGE1["grain"]),
        ("stage1_igniter", "#D05A3A", STAGE1["igniter"]),
        ("stage1_nozzle", "#8A8F96", STAGE1["nozzle"]),
        ("jet_vanes", "#3E4A57", [("ring", "JetVanes", 8520, 60, 240, 100, 10, 4, 0)]),  # in the plume at the nozzle exit
    ]


@glb(out="../GLB/tsirkon.glb", mesh_tolerance=3e-4, mesh_angular_tolerance=0.15)
@stl(out="../STL/tsirkon.stl")
@step(out="../STEP/tsirkon.step")
def tsirkon():
    return assemble(parts(), "tsirkon")


if __name__ == "__main__":
    tsirkon()
