# Engine reference sources

All PDFs are NASA Technical Reports Server (NTRS) documents: US government works, public domain.
`figures/` holds pages rendered from them (engine axis rotated horizontal where needed).
`illustrations/` holds other reference pictures (provenance and rights as noted per model below).

| File | Report | Used for |
|---|---|---|
| `E3_energy_efficient_engine_1981.pdf` | GE, *Energy Efficient Engine* flight propulsion system preliminary design, NTRS 19810013521 | `models/src/turbofan.py` |
| `small_expendable_turbojet_1977.pdf` | NASA Lewis, small low-cost expendable turbojet, NTRS 19770007088 | `models/src/turbojet.py` |
| `NACA_RM_E51C16_16in_ramjet_1951.pdf` | NACA RM E51C16, internal flow and burning characteristics of a 16-inch ram jet in a free jet (Perchonok and Farley, 1951), NTRS 19930086538 | `models/src/naca_lewis_16in_ramjet.py` |
| `J85_TMX-2398_test_installation.pdf` | NASA TM X-2398, J85 test installation, NTRS 19720004246 | reference only |
| `J85-21_TM-81451.pdf` | NASA TM-81451, J85-21, NTRS 19800012848 | reference only |
| `J85_modeling_techniques_2016.pdf` | Practical techniques for modeling gas turbine engines (J85), NTRS 20160012485 | reference only |
| `turbofan_weight_and_dimensions_1977.pdf` | Analysis of turbofan propulsion system weight and dimensions, NTRS 19770012125 | reference only |

| Figure | From |
|---|---|
| `figures/E3_energy_efficient_engine_1981_p19.png` | E3 report Figure 2, uninstalled FPS cross-section |
| `figures/E3_cross_section_axis_horizontal.png` | same, rotated axis-horizontal (used for digitizing) |
| `figures/E3_energy_efficient_engine_1981_p18.png` | E3 report Figure 1, installed FPS features |
| `figures/E3_energy_efficient_engine_1981_p60.png` | E3 report Figure 20, nacelle general arrangement |
| `figures/small_expendable_turbojet_1977_p21.png` | turbojet report Figures 1–2, cross-section and components |
| `figures/NASA_small_turbojet_cross_section.png` | turbojet Figure 1 cropped (used for digitizing) |
| `figures/small_expendable_turbojet_1977_p22.png` | turbojet report Figures 3–4, installations and instrumentation |
| `figures/lyulka_offset_reactor_grid.png` | Lyulka illustration enlarged 5x with a pixel grid (used for digitizing) |
| `figures/NACA_RM_E51C16_fig1_16in_ramjet.png` | RM E51C16 Figure 1, schematic of the 16-inch ram jet (overlay reference) |
| `figures/NACA_RM_E51C16_table1_coordinates.png` | RM E51C16 Table I, shell, inner-body and spike coordinates |
| `figures/NACA_RM_E51C16_fig2_fuel_injector.png` | RM E51C16 Figure 2, spray-nozzle fuel injector (90° sector) |

## Turbofan: GE/NASA E3 (turbofan.py)

Published (E3 report, Table I and text):

| Quantity | Value |
|---|---|
| Takeoff thrust, SLS | 162.4 kN (36,500 lb) |
| Fan diameter | 2108 mm |
| Max nacelle diameter | 2489 mm |
| Inlet length from fan face | 1590 mm |
| Turbomachinery length, fan front flange to LPT aft frame flange | 3180 mm |
| Overall nacelle length | 6033 mm |
| Exhaust nozzle diameter | 1590 mm |
| Nacelle highlight / max diameter | 0.86 |
| Fan | 32 blades, quarter-stage booster |
| HPC | 10 stages, 23:1 pressure ratio |
| HPT | 2 stages |
| Combustor | double annular, shingle liner |
| Exhaust | long-duct mixed flow, lobed mixer, centre plug |

Digitized from Figure 2 (`figures/E3_cross_section_axis_horizontal.png`); scale from the
2108 mm fan diameter (0.454 cm/px), x = 0 at the fan leading edge, ~±15 mm:

- Fan LE 0 / TE 186 mm, hub radius ~318 mm; quarter-stage at x ≈ 360–430 mm under a splitter at r ≈ 690 mm
- HPC rotors at x = 1190, 1303, 1412, 1494, 1566, 1644, 1698, 1771, 1825, 1880 mm;
  tip r 377 → 318 mm, hub r 227 → 241 mm
- Combustor x ≈ 1970–2200 mm, r ≈ 250–410 mm
- HPT rotors x ≈ 2280, 2400 mm, r ≈ 240–377 mm
- LPT (5 stages, counted on the figure) rotors x ≈ 2592, 2688, 2792, 2901, 3015 mm;
  hub r 331 mm, tip r 468 → 617 mm
- LPT aft frame x ≈ 3080 mm (Table I: 3180; the drawing reads ~3% short), mixer to x ≈ 3540 mm, plug tip x ≈ 4580 mm

Airfoil counts, the fan's 50 %-span shroud, the 64 bypass OGVs, the 56-blade quarter-stage rotor and
the 18-lobe mixer come from the E3 component design reports (`profile_builder/Turbofan/`, see its README).

Assumed (not in the sources): airfoil shapes (flat or elliptical) and chords, disks/drums/shafts, nacelle
lines between the published stations, mixer lobes drawn as radial sidewalls only (no crests or centrebody
corrugations).

## Turbojet: NASA Lewis small expendable turbojet (turbojet.py)

Published (report text and Figure 1):

| Quantity | Value |
|---|---|
| Layout | single-spool axial turbojet, fixed-area nozzle |
| Compressor | 4 stages, axial |
| Combustor | annular |
| Turbine | 1 stage |
| Max diameter | 292 mm (11.5 in) |
| Overall length | 965 mm (38 in) |
| Mass | ~59 kg (130 lb) |
| Max speed | 37,000 rpm |
| Sea-level static thrust at max speed | 3118 N (701 lbf) |

Since the fidelity pass the model follows the design and fabrication report, NASA TM X-3392
(`profile_builder/Turbojet/`, see its README): Figure 1 re-read on a mm grid (x = 0 at the nose tip,
~±2 mm), Table II airfoil counts, Table III hub/tip sections, spans and tip diameters, and the
component descriptions:

- Section breaks: inlet 0–295, compressor 295–487, combustor 487–728, turbine 725–800, exhaust 800–965 mm
- Compressor casing inner r 99.2 → 104.5 mm; drum r 48.5 → 86.3 mm (rotor 1 hub r 53.1, rotor 4 hub r 83.8)
- Combustor: snout apex x 480, liner dome x 545, liner r 60–125 mm, housing max r 146 mm, hollow
  mainshaft r 49–55 mm as the inner wall
- Turbine annulus r ≈ 81–123 mm (the earlier 63–97 mm reading was wrong); nozzle exit r 84 mm

Assumed: airfoil stagger/twist, elliptical sections, disk web/bore shapes, strut thickness, the fuel
control box, trunnion bosses, igniter clocking; swirlers and liner perforations are left out.

## Nuclear turbojet: OKB-165 (Lyulka) offset-reactor direct-cycle design (nuclear_turbojet.py)

Source: `illustrations/direct_cooling_offset_reactor_nuclear_turbojet/OKB Lyukola offset reactor
nuclear turbojet design.jpg`, a 290 × 105 px side-view illustration of a Soviet 1950s design study
(provided by the user; original publication unknown). Background: in the direct cycle the
compressor air is ducted through the reactor core as its coolant and heated there instead of in a
combustor ([aviation-history.com](http://www.aviation-history.com/articles/nuke-bombers.htm));
Lyulka's OKB-165 developed engines for the Soviet nuclear-bomber programme.

No dimensions are published. Scale: the compressor module (40 px tall) is set to the Ø1300 mm of
Lyulka's contemporary AL-7 turbojet ([Wikipedia](https://en.wikipedia.org/wiki/Lyulka_AL-7)),
giving 32.5 mm/px, x = (x_px − 5) × 32.5, r = |y_px − 67| × 32.5. Read off the drawing
(`figures/lyulka_offset_reactor_grid.png`), ~±1 px (±30 mm):

- Engine axis y = 67 px; nose cone px 5–28; compressor px 28–70 (Ø1300 to px 50, then smaller)
- Reactor unit above the axis, centre y ≈ 37 px (975 mm up): inlet plenum px 82–125, main vessel
  px 125–178 (y 14–60, Ø1500 mm), outlet transition px 178–235 falling to the turbine
- Long shaft housing under the reactor, y 62–72 px; turbine px 235–250, nozzle to px 265,
  tail cone to px 280 (~8.9 m overall)

Assumed: AL-7-like 9-stage compressor and 2-stage turbine, blade counts and airfoils, round
(not box-shaped) plenum and vessel, S-duct shapes between compressor, vessel and turbine (hidden in
the drawing), wall thicknesses, and a plain reactor core seated on end grids.

## Ramjet: NACA Lewis 16-inch ram jet (naca_lewis_16in_ramjet.py)

A research engine run in the Lewis altitude wind tunnel in 1950-51 (connected-pipe and free-jet tests at
Mach 1.35 and 1.73). Main source: NACA RM E51C16, with RM E52D08 on the same engine
(`profile_builder/Ramjet/`, see its README).

| Quantity | Value (inches, as published) |
|---|---|
| Stations | inlet lip 0; diffuser 91; combustion chamber 91-172; nozzle 172-181 |
| Shell inside Ø (Table I) | 9.00 at the lip (16° included cone to station 1), 9.92 at 6, 16.00 from 65 to 172, 13.75 at 181 |
| Cowl | sharp lip (0.004 radius), outer surface at 11° |
| Diffuser inner body Ø (Table I) | 4.00 at 4¾, 4.56 at 9¾-10, 8.00 at 65-75, 6.00 at 91 (pilot-burner exit) |
| Spike (Table I) | 46° cone to 3 in from the apex, ogive to Ø4.00 at 6½, cylinder to 9¾; tip 2.63 (M 1.35) or 4.27 (M 1.73) ahead of the lip |
| Fuel injector (Fig 2) | 74 in behind the lip, spraying upstream; four dual-arc bars on a 5.22 radius, Ø2¼ hoop, 1⅞ arms, four nozzles each; fed from the centre body |
| Flame holder (Fig 3) | 17 in behind the injector; corrugated gutters, 2 in chord, 35-53° included angle, connecting gutters, inner rim around the pilot exit, 54 % of the annulus blocked |
| Exit area | 51-74 % of the chamber area with the movable tail plug (minimum area at the exit) |
| Cooling | chamber and tail plug water-cooled |
| Centre-body supports (RM E52D08) | three struts, 17 % thick; two of them duct air to the vortex pilot |

Read from Figure 1 (~±0.5 in): flanges at 65, 72, 91, 110¾ and 172; tail plug Ø7.67 (from the 51 % area)
with its maximum at 167.5 and tip at the exit; plug rod Ø2¾ from 117.5, strut rings at 121.3 and 155.4;
cooling-coil turns about 1 in apart from 100 to 169. Assumed: shell wall 3/16, flanges Ø19, centre-body
strut station (68.5) and chord (5), gutter pitch (5 gutters and 4 connectors counted from the photo),
straight gutters at 40° standing in for the corrugated ones (40° gives the reported 54 % blockage).
