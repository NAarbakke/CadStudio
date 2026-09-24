# Engine reference sources

All PDFs are NASA Technical Reports Server (NTRS) documents: US government works, public domain.
`figures/` holds pages rendered from them (engine axis rotated horizontal where needed).

| File | Report | Used for |
|---|---|---|
| `E3_energy_efficient_engine_1981.pdf` | GE, *Energy Efficient Engine* flight propulsion system preliminary design, NTRS 19810013521 | `models/src/turbofan.py` |
| `small_expendable_turbojet_1977.pdf` | NASA Lewis, small low-cost expendable turbojet, NTRS 19770007088 | `models/src/turbojet.py` |
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

Assumed (not in the sources): all blade counts except the fan, airfoil shapes (flat or elliptical),
disks/drums/shafts, nacelle lines between the published stations, mixer as a plain cone (no lobes).

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

Digitized from Figure 1 (`figures/NASA_small_turbojet_cross_section.png`); scale from the
dimension lines (0.798 mm/px axial, 0.775 mm/px radial), x = 0 at the nose tip, ~±5 mm:

- Section breaks: inlet 0–295, compressor 295–487, combustor 487–742, turbine 742–810, exhaust 810–965 mm
- Compressor casing inner r ≈ 105 mm; hub r 65 → 85 mm
- Combustor liner r ≈ 61–128 mm, housing max r 146 mm
- Turbine r ≈ 63–97 mm; nozzle exit r ≈ 84 mm; tail cone to x = 965 mm

Assumed: blade counts, airfoils, disk/shaft layout, nose-cone profile, and a 20 mm aft shift of the
combustor dome so the compressor exit annulus stays open.
