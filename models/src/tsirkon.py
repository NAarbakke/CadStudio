"""3M22 Tsirkon (Zircon): cutaway display model, as reconstructed from open sources.

Sources (profile_builder/Tsirkon/resources/, see its README.md):
  - Luftlage, "Not quite a diamond" (2026), reconstruction article/fig01.jpeg: ~8.5 m long, Ø0.67 m,
    two solid-propellant stages; composite second-stage casing, alloy rear section carrying four
    folding control fins, first stage with cable raceways / actuator-rod housings and jet vanes.
  - Kyiv forensic institute (KNDISE) side-view sketch, debris/twz_wreckage_2024-02-07.jpg: stations
    (length 1485 px -> 8500 mm, 5.72 mm/px; diameter 135 px -> 670 mm).
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
NOSE_END = 1970.0      # ogive ends (KNDISE px 1545), r 263
NOSE_R = 263.0
BAND_END = 2720.0      # conical band out to full diameter (px 1415)
FINS_START = 5050.0    # alloy control section (fins px 935-1005)
STAGE_JOINT = 5500.0   # first/second stage joint (px 928)
SKIN = 8.0             # radome / band / control-section wall

STAGE2 = motor("S2", xe0=2930, xe1=4800, r=R, t=10, a=150, port_fwd=60, port_aft=110, bore=120,
               throat=(5000, 88), exit=(5250, 88), skirts=[(BAND_END, 2930), (4800, FINS_START)])
# RU2722994: the nozzle continues as a straight gas duct, then flares out to the aft end
STAGE2["nozzle"].append(("revolve", "S2DuctFlare", [(5250, 88), (5490, 288), (5490, 300), (5250, 100)]))
STAGE1 = motor("S1", xe0=5710, xe1=7900, r=R, t=10, a=150, port_fwd=60, port_aft=120, bore=130,
               throat=(8150, 80), exit=(8480, 270), skirts=[(STAGE_JOINT, 5710), (7900, LENGTH)])


def parts():
    """[(label, colour, ops)]: one entry per part (see lib/shapes.py for the op format)."""
    return [
        ("launch_shroud", "#8FA37A", [  # RU2776123: protective nose shroud + cap inside the container
            ("revolve", "Shroud", [(-60, 0), (-40, 150), (0, 250), (60, 320), (100, 340), (700, 345), (1260, 262),
                                   (1260, 254), (700, 337), (100, 332), (60, 312), (0, 242), (-40, 142), (-52, 0)])]),
        ("radome", "#E6E8EB", [("revolve", "Radome", shell(ogive(NOSE_END, NOSE_R), SKIN))]),
        ("seeker", "#C08A3E", [  # active radar seeker: gimballed antenna plate
            ("revolve", "Antenna", [(600, 0), (620, 0), (620, 120), (600, 120)]),
            ("revolve", "Gimbal", [(620, 0), (800, 0), (800, 60), (620, 60)])]),
        ("guidance_electronics", "#4F7A5A", [("revolve", "Electronics", [(1100, 0), (1800, 0), (1800, 170), (1100, 170)])]),
        ("band", "#DADDE1", [("revolve", "Band", [(NOSE_END, NOSE_R - SKIN), (BAND_END, R - SKIN), (BAND_END, R), (NOSE_END, NOSE_R)])]),
        ("payload_bay", "#8C5A5A", [  # placeholder volume only
            ("revolve", "PayloadBay", [(2050, 0), (2700, 0), (2700, 320), (2050, 255)])]),
        ("stage2_case", "#6B6655", STAGE2["case"]),
        ("stage2_grain", "#B89A6A", STAGE2["grain"]),
        ("stage2_igniter", "#D05A3A", STAGE2["igniter"]),
        ("stage2_nozzle_duct", "#8A8F96", STAGE2["nozzle"]),
        ("control_section", "#B9BEC4", [  # alloy skin, folding fins, 3 duct-bracing spokes (RU2722994)
            ("revolve", "ControlSkin", tube(FINS_START, STAGE_JOINT, R, SKIN)),
            ("fins", "ControlFins", [(5080, R - 5), (5300, R + 260), (5440, R + 260), (5460, R - 5)], 14, 4),
            ("ring", "DuctSpokes", 5380, 230, R - SKIN + 1, 30, 8, 3, 0, 60)]),  # flare outer r <= 221 here
        ("fin_actuators", "#5E6B7A", [("ring", "FinActuators", 5150, 130, tip_radius(R - SKIN, 120, 70, 0), 120, 70, 4, 0)]),
        ("stage1_case", "#C9CED6", STAGE1["case"] + [("ring", "Raceways", 6950, R - 5, R + 25, 2800, 60, 4, 0, 45)]),
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
