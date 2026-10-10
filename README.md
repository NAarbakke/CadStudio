# CadStudio

Parametric CAD models written as Python code (build123d on the OpenCascade kernel, via the
[text-to-cad](https://github.com/earthtojake/text-to-cad) `cadgen` package), exported to STEP / STL / GLB
and pushed into SolidWorks, Fusion or Onshape.

| Model | Source script | What it is | Basis |
|---|---|---|---|
| Turbofan | `models/ge_e3_turbofan/src/ge_e3_turbofan.py` | GE/NASA Energy Efficient Engine (E3): two-spool, long-duct mixed-flow turbofan, fan with 50 %-span shroud, 64 bypass OGVs, 18-lobe mixer, every core row at its design airfoil count, each spool split into shaft and rotors, rounded nacelle lip, plug and HPT tie bolts; 18 parts in 4 sub-assemblies | Dimensions and flowpath from the E3 NASA report, counts from the E3 component design reports (`profile_builder/Turbofan/`) |
| Turbojet | `models/nasa_lewis_small_turbojet/src/nasa_lewis_small_turbojet.py` | NASA Lewis small expendable turbojet: two-strut inlet with gearbox and front bearing, fuel control, welded 4-stage drum with lofted airfoils at the design counts, snout combustor with manifold, 12 nozzles and igniters, hollow mainshaft, one-piece 35-vane turbine stator, 57-blade rotor, strutted exhaust with rear bearing, convergent nozzle, bolted casing joints; 21 parts in 6 sub-assemblies | Design report NASA TM X-3392: Figure 1 cross-section, airfoil tables (`profile_builder/Turbojet/`) |
| Nuclear turbojet | `models/lyulka_nuclear_turbojet/src/lyulka_nuclear_turbojet.py` | OKB-165 (Lyulka) direct-cycle nuclear turbojet: offset reactor above the axis, S-ducts from the compressor and to the turbine, long shaft tunnel, intake lip, flanged and bolted casing, duct, vessel and nozzle joints, vessel bands and control drive housings, spool split into shaft and rotors; 23 parts in 5 sub-assemblies | Layout from a period illustration, scaled to the AL-7 (`profile_builder/Nuclear_turbojet/`) |
| Tsirkon | `models/tsirkon/src/tsirkon.py` | 3M22 Tsirkon (Zircon) cutaway: launch shroud, radome, seeker, electronics, payload placeholder, two solid motors (case, grain, igniter, nozzle), extended gas duct with fin actuators and bracing spokes, folding fins, raceways, jet vanes; 17 parts | Luftlage "Not quite a diamond" reconstruction (8.5 m × Ø0.67 m) + KNDISE side-view sketch (`profile_builder/Tsirkon/resources/`) |
| Oreshnik | `models/oreshnik/src/oreshnik.py` | Oreshnik IRBM cutaway: nose fairing, six payload cones on a plate, post-boost stage layout, instrumentation compartment, two solid motors (case, grain, igniter, nozzle), aft skirt; 18 parts | Luftlage "The missile that came in from the cold" reconstruction (13 m × Ø1.61 m), with further references recorded in the source (`profile_builder/Oreshnik/resources/`) |
| F-1 | `models/rocketdyne_f1/src/rocketdyne_f1.py` | Rocketdyne F-1 (Saturn V S-IC) rocket engine: gimbal, hollow LOX dome, baffled injector, regeneratively cooled tube-bundle chamber with hatbands and fuel manifold, Rao bell to 10:1, double-walled nozzle extension to 16:1, turbine exhaust manifold, turbopump, heat exchanger, gas generator, valves, flat-topped LOX dome with ring manifold and elbow inlets, four high-pressure ducts, bolted flanges; 42 parts in 8 sub-assemblies | R-3896-1 technical manual Fig 2-22 envelope dimensions + performance data, heroicrelics section drawings (`profile_builder/F1/`) |
| Ramjet | `models/naca_lewis_16in_ramjet/src/naca_lewis_16in_ramjet.py` | NACA Lewis 16-inch ram jet (1951 altitude-wind-tunnel engine): translating spike, sharp-lip conical diffuser, three-strut centre body with pilot cup, four dual-arc fuel bars with 16 upstream nozzles, gutter-grid flame holder, water-cooled Ø16 in chamber with a copper cooling coil, convergent nozzle, movable tail plug on two strut rings, five bolted flange joints; 15 parts in 4 sub-assemblies | NACA RM E51C16 Table I coordinates, Figures 1-3 and text; RM E52D08 (`profile_builder/Ramjet/`) |
| Raptor 1 | `models/spacex_raptor_1/src/spacex_raptor_1.py` | SpaceX Raptor 1 sea-level engine: mount plate and gimbal block on a thrust frame, oxygen pump and preburner on the chamber axis, Ø870 hot-gas manifold disc on the main injector, methane turbopump under the disc beside the chamber (turbine, preburner, pump, inlet duct), jacketed chamber with a coolant collector, heat-tinted throat, coolant manifold just below it fed by a duct wrapped around the chamber, short wide bell, swept ducts, seven small lines, two engine controllers with wiring, valves with actuators, torch igniter, sensor ports, bolted flanges throughout; 36 parts in 5 sub-assemblies | Published envelope (3.1 m long, Ø1.3 m exit, 34.34:1 expansion); stations and diameters of the main masses read from SpaceX photographs at about ±5 % (`profile_builder/Raptor/`); the rest is assumed (`models/lib/raptor.py`) |
| Raptor 2 | `models/spacex_raptor_2/src/spacex_raptor_2.py` | The same layout simplified: oxygen inlet bellows on the axis, wider throat, welded preburners, three small lines, one engine controller with wiring, green-grey oxidised bell, no igniter or sensor ports; 30 parts in 5 sub-assemblies | As Raptor 1; throat scaled from thrust over chamber pressure |
| Raptor 3 | `models/spacex_raptor_3/src/spacex_raptor_3.py` | The integrated engine: flanged oxygen inlet studded onto smooth dark welded housings, housing bosses, methane pump dropping straight onto the coolant manifold, one thin service line, bare dark bell, no visible valves or oxygen line; 21 parts in 5 sub-assemblies | As Raptor 1; throat scaled from thrust over chamber pressure |

All engine models are display/study models: the envelope and flowpath follow the sources, but airfoils
(flat or elliptical sections) and internal structure are simplified. Blade counts are the published design
counts for the turbojet and turbofan and assumed for the nuclear turbojet. The three Raptor models share one layout: their overall size is from published figures and their main proportions from photographs, the rest is assumed. Units are mm (the F-1 and ramjet
are written in inches, as their sources are, and scaled once); the engine axis is +X.

## Setup

Requires Python 3.11+ (tested on 3.13, Windows 11).

Commands are shown in Windows PowerShell. On Ubuntu, use `.venv/bin/python` in place of
`.venv\Scripts\python` and forward slashes in paths, and run `./open_cad_viewer.sh` in place
of `Open CAD Viewer.cmd`. See [Ubuntu setup](docs/ubuntu.md) for what does and does not work there.

The engine and bundled CAD Viewer are pinned to text-to-cad/cadgen 0.7.19.
Model dimensions and geometry recipes currently live in Python; see
[model specification format](docs/model-specs.md) for the proposed YAML data
format, material/mass handling and cache-aware migration approach.

Engineering reports combine 3D renders, component/specification tables, source
notes and dimensioned vector drawings. See [engineering reports](docs/engineering-reports.md).

```powershell
.venv\Scripts\python tools\engineering_report.py reports\naca_lewis_16in_ramjet.yaml
```

The PDF is written to `output/pdf/naca_lewis_16in_ramjet_engineering_report.pdf`.

Reports with equations, plots and numbered tables can be typeset with LaTeX instead
(optional; needs TeX Live or MiKTeX). See [LaTeX reports](docs/latex-reports.md).

```powershell
.venv\Scripts\python reports\latex\naca_lewis_16in_ramjet.py
```

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python tools\patch_cadgen_windows.py     # keep background workers hidden on Windows
.venv\Scripts\python -m playwright install chromium   # used for snapshot renders
.venv\Scripts\python -m cadgen.cli doctor <path-to-installed-cad-skill>   # checks cadgen + OpenCascade kernel
```

On Ubuntu, see [Ubuntu setup](docs/ubuntu.md). The pinned engine does not install on Linux yet.

## Build

One script per model is the single source of truth. Running it writes every declared format together:

```powershell
.venv\Scripts\python models\ge_e3_turbofan\src\ge_e3_turbofan.py    # -> STEP/, STL/, GLB/ beside its src/ (~15 min)
.venv\Scripts\python models\nasa_lewis_small_turbojet\src\nasa_lewis_small_turbojet.py
.venv\Scripts\python models\naca_lewis_16in_ramjet\src\naca_lewis_16in_ramjet.py
.venv\Scripts\python models\lyulka_nuclear_turbojet\src\lyulka_nuclear_turbojet.py
.venv\Scripts\python models\tsirkon\src\tsirkon.py
.venv\Scripts\python models\oreshnik\src\oreshnik.py
.venv\Scripts\python models\rocketdyne_f1\src\rocketdyne_f1.py
.venv\Scripts\python models\spacex_raptor_1\src\spacex_raptor_1.py
.venv\Scripts\python models\spacex_raptor_2\src\spacex_raptor_2.py
.venv\Scripts\python models\spacex_raptor_3\src\spacex_raptor_3.py
```

Outputs are cached by cadgen and only rebuilt when the script (or `models/lib/`) changes; add
`--force` to rebuild anyway. Generated files are git-ignored; rebuild them after cloning.

```
models/
  lib/              shared factories: revolve profiles, blade rows, clearances (shapes.py)
  <model>/
    src/            the model script, <model>.py (edit this)
    STEP/ STL/ GLB/ generated exports
    FreeCAD/        generated: <model>.FCStd (freecad_build.py)
    SolidWorks/     generated: native parts (solidworks_build.py), imported/ (solidworks_import.py)
integrations/     solidworks/ (native builder, editor, verify, STEP import), freecad/, fusion/, onshape/
profile_builder/  gitignored reference material per model (source reports, digitized figures, notes)
```

`models/` also holds the text-to-cad example projects (`f1`, `f14d`, `hypercar`, `falcon_heavy`, `tendon_hand`
and others; MIT, see `models/LICENSE-text-to-cad`), catalogued in `models/EXAMPLES.md`. They have the same
folder shape with their own `src/lib/` and are source-only until built: run a project's `src/*.py` to
generate its exports. The rest of the upstream clone stays in git-ignored `vendor/text-to-cad`.

Tunable dimensions sit as constants and tables at the top of each script (gas-path radii, stage
positions, blade counts, clearances). Each script's `parts()` returns one recipe per part: a list
of named ops (revolve, offset revolve, offset ring, spline, cut, blade ring, pins, loft, duct, fins, pipe, sweep; see `lib/shapes.py`; missile helpers: shells, ogives, solid motors in `lib/rocket.py`). cadgen builds the
STEP/STL/GLB from the recipes and `integrations/solidworks/solidworks_build.py` builds the same recipes as native
SolidWorks features. Blade rows come from `stage()`, which sizes tips and roots so flat blade
corners never cut into the casing.

## Model fidelity standard

Every model should read as built hardware, not as a diagram of primitives. A new or edited model
is expected to have:

- **Finishes, not function colours.** Each part takes a named finish from `lib/materials.py` (base
  colour, roughness, metalness), and the model passes `materials=` to `@step`. Keep base colours mid
  to light and metalness moderate (about 0.35 to 0.6): near 1 the Render display turns large
  surfaces almost black. Finishes are display properties and assign no alloy, density or mass.
- **Rounded or chamfered edges.** Use the `lathe` op in place of `revolve` for flanges, housings and
  turned parts; it also revolves about any axis. Chamfer (`chamfer=True`) a small radius on a large
  thin ring, where a rounded edge meshes into a very large number of triangles.
- **Fasteners on flanges.** `flange_bolts()` adds a bolt circle (`hex_circle` nuts on `pin_circle`
  stud ends) standing on a flange face. No holes are cut. One part per bolt circle.
- **Sub-assemblies of real components.** Split a component into the housings and flanges it is
  built from, give each a label, and nest them with `GROUPS` passed to `assemble()`, in place of one
  fused solid per function.
- **Assumptions declared.** The docstring says which details are for appearance and not from the
  sources (flange sizes, bolt counts, corner radii, component splits).

Check the saved STEP after every build. Every part must be a valid solid and no two parts may intersect:

```powershell
.venv\Scripts\python tools\model_check.py models\rocketdyne_f1\STEP\rocketdyne_f1.step
```

Where the model builds in FreeCAD, run `integrations\freecad\freecad_build.py <model>` as well; that
comparison has caught a part the kernel silently dropped. Review a snapshot in the Render display
with the floor moved off the axis (`--display '{"mode":"render","floor":{"placement":"lowest"}}'`).
`lathe`, `hex_circle`, `pin_circle` and `sweep` (a round duct with real bends) build in cadgen and FreeCAD; the SolidWorks builder does not
have them, so bring such a model into SolidWorks with `solidworks_import.py`.

`reports\latex\model_fidelity.py` writes `output/pdf/model_fidelity.pdf`, which measures each model
against its previous commit (parts, fasteners, rounded profiles, finishes, file sizes). Status: the
F-1 (42 parts in 8 sub-assemblies, 574 fasteners), the ramjet (15 parts, 240 fasteners), the turbojet
(21 parts, 144 fasteners), the turbofan (18 parts, 84 fasteners), the nuclear turbojet (23 parts, 600
fasteners) and the three Raptors (36, 30 and 21 parts; 272, 172 and 68 fasteners) meet the standard;
Tsirkon and Oreshnik do not yet. The report covers the seven models that existed at its baseline
commit, not the Raptors. All of these use `lathe` and bolt-circle ops, so `solidworks_build.py` stops
at them; the nuclear turbojet's earlier native SolidWorks files predate its upgrade.

## View

- **CAD Viewer** (bundled with cadgen, runs locally in the browser):
  ```powershell
  .venv\Scripts\python tools\start_viewer.py --open
  .venv\Scripts\python tools\start_viewer.py ge_e3_turbofan --open
  ```
  Or double-click `Open CAD Viewer.cmd` in the project root. The launcher serves
  `models/`, starts or reuses a background viewer, verifies its root and prints
  the actual URL. Ports can change; use that URL. Expand **STEP** in the file
  panel and select a model. Opens STEP, STL and GLB; STEP supports topology
  selection and measurement. See [viewer operation and troubleshooting](docs/viewer.md).
  Settings provide clipping/sections and display presets.
- **PyVista** (desktop window, local OpenGL):
  ```powershell
  .venv\Scripts\python -c "import pyvista as pv; p = pv.Plotter(); p.import_gltf('models/ge_e3_turbofan/GLB/ge_e3_turbofan.glb'); p.show()"
  ```
- **Snapshot to PNG**: `cd models; ..\.venv\Scripts\python -m cadgen.cli step snapshot nasa_lewis_small_turbojet/STEP/nasa_lewis_small_turbojet.step ../tmp/view.png [--mode section] [--camera 200:15]`

See [local installation and update notes](docs/local-installation.md) for the
engine and viewer locations. For a full export-access check:

```powershell
.venv\Scripts\python tools\start_viewer.py --check-all
```

## CAD platform integrations

STEP is the exchange format: the Python script stays the master, the CAD platform receives a
non-parametric (dumb-solid) import. Edit the script, rebuild, re-import.

| Script | Platform | How it connects | Status |
|---|---|---|---|
| `integrations/solidworks/solidworks_import.py` | SolidWorks (Windows) | COM API via pywin32; imports STEP, saves `.SLDASM` + one `.SLDPRT` per part to `models/<name>/SolidWorks/imported/` | Tested with SOLIDWORKS 2026 SP3 (3DEXPERIENCE): all three engines import and save; the reopened ramjet assembly resolves all 6 parts from the output folder |
| `integrations/fusion/` | Autodesk Fusion | Fusion script (runs inside Fusion only): file picker, imports each STEP into a new design | Not tested (Fusion not installed here) |
| `integrations/onshape/onshape_import.py` | Onshape | REST API (`/translations`), API-key basic auth; creates or reuses a document | Not tested (needs API keys) |

```powershell
# SolidWorks: open SolidWorks and log in first (the 3DEXPERIENCE edition cannot be started over COM)
.venv\Scripts\python integrations\solidworks\solidworks_import.py models\ge_e3_turbofan\STEP\ge_e3_turbofan.step [more.step ...] [--close] [--out DIR]

# Onshape: keys from https://dev-portal.onshape.com/keys
$env:ONSHAPE_ACCESS_KEY = "..."; $env:ONSHAPE_SECRET_KEY = "..."
.venv\Scripts\python integrations\onshape\onshape_import.py models\ge_e3_turbofan\STEP\ge_e3_turbofan.step [--document <id>] [--flatten]
```

Fusion: Utilities > Scripts and Add-Ins > "+" > Script from my computer > pick
`integrations/fusion`, then Run.

Notes:
- SolidWorks loads STEP through 3D Interconnect (parts land in a temp folder); the script saves parts
  first, then the assembly, so references point into the output folder. Paths are made absolute
  because SolidWorks resolves relative paths against its own working directory.
- Re-importing creates new documents; none of the platforms keeps downstream features on a dumb
  import across changes, so do detailing (drawings, fillets on imported bodies) only on a frozen model.
- `solidworks_import.py` uses `solidworks_api.py` (typed COM wrappers) and default import options; retested
  on the earlier 6-part ramjet (reopened assembly resolves every part from the output folder).

## Native parametric SolidWorks (no STEP)

`integrations/solidworks/solidworks_api.py` drives SolidWorks' own modeller over COM, so the result has a real feature
tree: fully defined sketches, named dimensions, circular patterns driven by global variables.
No MCP server is needed; plain Python + pywin32 talks to SolidWorks directly.

```powershell
# build a model as native parts + assembly -> models/<model>/SolidWorks/
.venv\Scripts\python integrations\solidworks\solidworks_build.py MODEL [--parts fan nacelle]   # MODEL = folder name in models/

# check the native parts against the cadgen STEP (needs models/<model>/STEP/<model>.step)
.venv\Scripts\python integrations\solidworks\solidworks_verify.py ge_e3_turbofan

# inspect and edit any .SLDPRT/.SLDASM (rebuilds, refuses to save on rebuild errors)
.venv\Scripts\python integrations\solidworks\solidworks_edit.py list models\lyulka_nuclear_turbojet\SolidWorks\nose_cone.SLDPRT
.venv\Scripts\python integrations\solidworks\solidworks_edit.py set  models\lyulka_nuclear_turbojet\SolidWorks\nose_cone.SLDPRT InletStruts_count=6 r2@NoseBodyProfile=250
.venv\Scripts\python integrations\solidworks\solidworks_edit.py suppress models\lyulka_nuclear_turbojet\SolidWorks\nose_cone.SLDPRT InletStruts
```

- Feature tree per recipe op: revolves/cuts/splines are `<Name>Profile` sketches with every
  vertex dimensioned `x<i>`/`r<i>` from the origin; blade/pin rows are `<Name>Plane` +
  `<Name>Sketch` + `<Name>Blade` (span `D1@<Name>Blade`) + pattern `<Name>` driven by global
  `<Name>_count`; the fan blade is a loft through eight closed-spline sections. Stage names follow the
  scripts: `HPC3Rotor`, `LPT2Nozzle`, `Comp1Stator`, `FanBlades`, ...
- Blade sections sit on reference planes (hidden) and are fixed geometry; change span and count
  by dimension/global, change airfoil shape in the Python recipe.
- Free-standing rows (stator vanes) are body patterns; rows on a disk are feature patterns.
- `solidworks_verify.py` exports each part to STEP and compares it with the cadgen part: volume and the
  overlap volume (fuzzy boolean), plus rebuild errors and fully defined sketches. Tolerance 0.1 %,
  0.2 % for lofted parts (see Known issues). When the overlap boolean fails (nothing or a partial overlap
  from cone tips, many nearly coincident faces or differently placed seams) it falls back to classifying
  600 random points in both solids.
- Build time (SOLIDWORKS 2026): the earlier 6-part ramjet ~1.5 min, turbojet ~4 min, turbofan ~30 min (the HPC stator
  part alone ~12 min: ten free-standing vane rows, each a body pattern).
- Files saved by a 3DEXPERIENCE Makers licence are flagged personal-use.
- pywin32 type wrappers: `solidworks_api` generates them on first use (`gencache.EnsureModule`); after a
  SolidWorks upgrade delete `%LOCALAPPDATA%\Temp\gen_py` to regenerate.

## Native parametric FreeCAD

`integrations/freecad/freecad_build.py` builds the same recipes as a parametric FreeCAD document
(`models/<model>/FreeCAD/<model>.FCStd`, git-ignored) and checks every part against the cadgen STEP:

```powershell
.venv\Scripts\python integrations\freecad\freecad_build.py tsirkon          # add --no-verify to skip the check
```

- The venv evaluates the model's `parts()` into JSON (FreeCAD's own Python has no cadgen), then
  `freecadcmd` runs `integrations/freecad/freecad_builder.py`. Default FreeCAD path is
  `%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecadcmd.exe`; override with `FREECADCMD`.
- Part workbench features, editable in FreeCAD: revolve and fin profiles are fully constrained
  sketches with dimensions `x<i>` / `r<i>`; blade, pin and cone rows are primitives
  (`Part::Box`/`Part::Cylinder`) in a Draft polar array (edit `NumberPolar`); lofts and ducts are
  `Part::Loft`; cuts are `Part::Cut` in recipe order.
- No colours yet (freecadcmd has no GUI to store them).
- Verified: ramjet (9 parts, including the `pipe` fuel bars and angled `fins` gutters), f1 (12 parts, including
  the `pipe` ducts), tsirkon (17 parts), oreshnik (13 parts) match cadgen at 100.00 % for every part (the two
  missiles were last run before the torus fix below); the same two missiles also pass `solidworks_verify.py`.
  Turbojet (~80 min): every part matches in volume; `compressor_stators` passes by point sampling (99.62 %;
  the fuzzy boolean says 71.79 % on the 148 thin vanes); `rotor` is still flagged: the boolean returns
  nothing and point classification in the ~430-blade fused solid gives 46 %, while its volume, centroid,
  mass properties and blade slices match cadgen exactly (checked separately).

## Recommended workflow

1. **Develop in build123d** (`models/<model>/src/<model>.py`): layout, proportions, clearances, stage counts.
   Fast iteration, diffable in git, checked with the viewer and `read_step`. Get it ~90 % there.
2. **Freeze and hand over to SolidWorks natively** (`solidworks_build.py`) rather than as STEP, so the
   SolidWorks model has editable dimensions instead of dumb solids.
3. **Final tuning in SolidWorks**, by hand or with `solidworks_edit.py`: dimension tweaks, fillets,
   drawings, mates, materials, simulation.
4. **Decide once which side is master.** After detailing starts in SolidWorks, regenerating from
   Python overwrites that work. Carry big changes back into the Python data (and rebuild), keep
   small, detail-level changes in SolidWorks only.

STEP import (`solidworks_import.py`) remains the quick path for looking at a model or sharing it
with someone else.

## Visual check loop

`tools/render_check.py` renders a model from five views into one sheet (iso, rear 3/4, side, top,
section) so the whole assembly can be reviewed at a glance, and optionally scores the side
silhouette against a reference picture:

```powershell
.venv\Scripts\python tools\render_check.py models\tsirkon\STEP\tsirkon.step --hide launch_shroud `
    --ref profile_builder\Tsirkon\resources\article\fig03.jpeg --ref-box 280,185,380,1055 --ref-rotate 90 --ref-tol 15 --length 8500
```

Outputs `tmp/check/<model>_sheet.png` and `<model>_overlay.png` (grey both, red model only, cyan
reference only) with the silhouette IoU and the worst radius mismatch in mm. The reference is
cropped to `--ref-box`, rotated/flipped to nose-left and fitted by length. Current scores: Tsirkon
0.958 vs the Luftlage side render, Oreshnik 0.961 vs the Luftlage reconstruction, F-1 0.839 vs R-3896-1 Fig 2-22
(misses are the drawing's dimension lines and insulation-cocoon corners), ramjet 0.898 vs RM E51C16 Figure 1
(misses are leader lines, the tunnel mounts and the schematic's ~9 % taller radial scale).

## Verification done

Current viewer/export-access checks and their scope are recorded separately in
[verification notes](docs/verification.md). The checks below are historical
geometry and native-platform checks; rerun them after changing the relevant model.

Checks run with `read_step` on the saved STEP files (rerun with the snippet below after changing geometry):

- Every part of every model is a valid solid.
- Turbojet: envelope 965 × Ø292 mm (matches the source); no two parts intersect; rotor tip and stator hub
  clearances ≥ 1.0 mm by construction (`tip_radius`, `GAP`), 0.4 mm in the real engine.
- F-1: no two parts intersect (the turbine exhaust manifold was moved to the Fig 2-22 centre, x 141.5 / r 62.5,
  which also cleared an overlap with the exit flange).
- Turbofan (E3): envelope x −1590…4580 mm, Ø2489 mm (matches Table I); fan tip clearance ≥ 7.1 mm;
  LP spool clears casing 2.99 mm, frame hub/plug 5 mm, stators ≥ 12 mm; HP spool clears casing 2.19 mm, HPC stators 2.38 mm, frame hub 4.34 mm;
  LP–HP spool gap 20 mm.
- Ramjet: no two parts intersect; exit area 74 % of the chamber area open, 51 % with the plug's Ø7.67 in
  section at the exit (the report's range); flame-holder blockage 54 % of the annulus (the report's value).
- Native SolidWorks vs cadgen (`solidworks_verify.py`): every part of the three engines has fully defined
  sketches and no rebuild errors; all non-lofted parts match in volume and overlap (100.00 %). The
  lofted fan matches in volume within the loft tolerance (the overlap boolean fails on lofted
  blades, so it is checked by volume and radial slices instead).

```python
from cadgen import read_step
parts = {c.label: c for c in read_step("models/nasa_lewis_small_turbojet/STEP/nasa_lewis_small_turbojet.step").leaves}
print(parts["rotor"].distance_to(parts["compressor_casing"]))   # clearance, mm
print(parts["rotor"] & parts["compressor_casing"])              # None = no interference
```

`distance_to` on large assemblies can take minutes and can report a false 0.00 on revolved seams;
confirm a zero with the intersection check above.

## Known issues

- **Console windows on Windows**: cadgen's background build daemon starts worker processes that each
  open a console window. Local fix: `CREATE_NO_WINDOW` added to the four `subprocess.Popen` calls in
  `.venv/Lib/site-packages/cadgen/daemon/{pool,executors,artifacts,housekeeping}.py`.
  Run `.venv\Scripts\python tools\patch_cadgen_windows.py` after reinstalling cadgen;
  the helper validates the 0.7.19 launch sites and preserves this local fix.
- The turbofan build takes ~15 min and its STEP is ~80 MB (≈3,300 airfoil solids at the design counts).
- **Twisted lofts**: a loft between two ellipses has no defined start point, so with twist the
  kernels pair the wrong points (OpenCascade pinched the old fan blades to ~0.9 L, SolidWorks
  bulged them). Blade sections are now closed splines through matched points (`blade_section()`),
  eight stations root to tip. The sections are identical in both kernels, but OpenCascade's smooth
  loft overshoots ~12 % next to the end sections, so cadgen lofts ruled (straight between stations);
  that matches SolidWorks' smooth loft to 0.006 % in blade volume, slices within 0.5 % (1.8 % near
  the tip).
- **Volumes of spline solids**: build123d's `.volume` is ~10 % off on the lofted fan (132.9 vs
  146.7 L); use adaptive integration (`volume()` in `integrations/compare.py`) for such parts.
- **SolidWorks loft from an on-axis circle**: SOLIDWORKS 2026 refuses to loft from a full circle
  centred on the engine axis when the next section moves off-axis (1 mm off works). `solidworks_api`
  draws on-axis duct stations as two semicircles; arcs everywhere breaks other stations instead.
- Plain booleans between two nearly identical solids (e.g. SolidWorks export vs cadgen part) can
  return nothing; use a fuzzy boolean (`common_volume()` in `integrations/compare.py`). Even the fuzzy one
  fails on some very thin lofted vanes (turbojet stators), which `compare()` then reports as partial overlap.
- FreeCAD's MultiFuse silently leaves a `Part::Torus` unfused when the torus seam lies on a
  `Part::Revolution` seam (both in the XY plane); `op_torus` turns the torus seam 45° about the axis
  (same solid). Found on the ramjet cooling coil, where 60 rings came out as separate solids.
- The `pipe` op (F-1 ducts, ramjet fuel bars) and `fins` with an `angle` (ramjet connecting gutters) build in
  cadgen and FreeCAD only; `solidworks_build.py` stops at them, so bring the F-1 and the ramjet into
  SolidWorks with `solidworks_import.py`.
