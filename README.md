# CadStudio

Parametric CAD models written as Python code (build123d on the OpenCascade kernel, via the
[text-to-cad](https://github.com/earthtojake/text-to-cad) `cadgen` package), exported to STEP / STL / GLB
and pushed into SolidWorks, Fusion or Onshape.

| Model | Source script | What it is | Basis |
|---|---|---|---|
| Turbofan | `models/src/turbofan.py` | GE/NASA Energy Efficient Engine (E3): two-spool, long-duct mixed-flow turbofan, fan with 50 %-span shroud, 64 bypass OGVs, 18-lobe mixer, every core row at its design airfoil count; 12 parts | Dimensions and flowpath from the E3 NASA report, counts from the E3 component design reports ([resources/README.md](resources/README.md), `profile_builder/Turbofan/`) |
| Turbojet | `models/src/turbojet.py` | NASA Lewis small expendable turbojet: two-strut inlet with gearbox and front bearing, fuel control, welded 4-stage drum with lofted airfoils at the design counts, snout combustor with manifold, 12 nozzles and igniters, hollow mainshaft, one-piece 35-vane turbine stator, 57-blade rotor, strutted exhaust with rear bearing, convergent nozzle; 14 parts | Design report NASA TM X-3392: Figure 1 cross-section, airfoil tables ([resources/README.md](resources/README.md), `profile_builder/Turbojet/`) |
| Nuclear turbojet | `models/src/nuclear_turbojet.py` | OKB-165 (Lyulka) direct-cycle nuclear turbojet: offset reactor above the axis, S-ducts from the compressor and to the turbine, long shaft tunnel, 13 parts | Layout from a period illustration, scaled to the AL-7 ([resources/README.md](resources/README.md)) |
| Tsirkon | `models/src/tsirkon.py` | 3M22 Tsirkon (Zircon) cutaway: launch shroud, radome, seeker, electronics, payload placeholder, two solid motors (case, grain, igniter, nozzle), extended gas duct with fin actuators and bracing spokes, folding fins, raceways, jet vanes; 17 parts | Luftlage "Not quite a diamond" reconstruction (8.5 m × Ø0.67 m) + KNDISE side-view sketch (`profile_builder/Tsirkon/resources/`) |
| Oreshnik | `models/src/oreshnik.py` | Oreshnik IRBM cutaway: nose fairing, six payload cones on a plate, post-boost stage layout, instrumentation compartment, two solid motors (case, grain, igniter, nozzle), aft skirt; 18 parts | Luftlage "The missile that came in from the cold" reconstruction (13 m × Ø1.61 m), with further references recorded in the source (`profile_builder/Oreshnik/resources/`) |
| F-1 | `models/src/f1.py` | Rocketdyne F-1 (Saturn V S-IC) rocket engine: gimbal, hollow LOX dome, baffled injector, regeneratively cooled tube-bundle chamber with hatbands and fuel manifold, Rao bell to 10:1, double-walled nozzle extension to 16:1, turbine exhaust manifold, turbopump, heat exchanger, gas generator, valves, flat-topped LOX dome with ring manifold and elbow inlets, four high-pressure ducts; 12 parts | R-3896-1 technical manual Fig 2-22 envelope dimensions + performance data, heroicrelics section drawings (`profile_builder/F1/`) |
| Ramjet | `models/src/naca_lewis_16in_ramjet.py` | NACA Lewis 16-inch ram jet (1951 altitude-wind-tunnel engine): translating spike, sharp-lip conical diffuser, three-strut centre body with pilot cup, four dual-arc fuel bars with 16 upstream nozzles, gutter-grid flame holder, water-cooled Ø16 in chamber, convergent nozzle, movable tail plug on two strut rings; 9 parts | NACA RM E51C16 Table I coordinates, Figures 1-3 and text; RM E52D08 ([resources/README.md](resources/README.md), `profile_builder/Ramjet/`) |

All engine models are display/study models: the envelope and flowpath follow the sources, but airfoils
(flat or elliptical sections) and internal structure are simplified. Blade counts are the published design
counts for the turbojet and turbofan and assumed for the nuclear turbojet. Units are mm (the F-1 and ramjet
are written in inches, as their sources are, and scaled once); the engine axis is +X.

## Setup

Requires Python 3.11+ (tested on 3.13, Windows 11).

The engine and bundled CAD Viewer are pinned to text-to-cad/cadgen 0.7.10.
Model dimensions and geometry recipes currently live in Python; see
[model specification format](docs/model-specs.md) for the proposed YAML data
format, material/mass handling and cache-aware migration approach.

Engineering reports combine 3D renders, component/specification tables, source
notes and dimensioned vector drawings. See [engineering reports](docs/engineering-reports.md).

```powershell
.venv\Scripts\python tools\engineering_report.py reports\naca_lewis_16in_ramjet.yaml
```

The PDF is written to `output/pdf/naca_lewis_16in_ramjet_engineering_report.pdf`.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python tools\patch_cadgen_windows.py     # keep background workers hidden on Windows
.venv\Scripts\python -m playwright install chromium   # used for snapshot renders
.venv\Scripts\python -m cadgen.cli doctor <path-to-installed-cad-skill>   # checks cadgen + OpenCascade kernel
```

For Claude Code, the text-to-cad plugin provides CAD modeling and viewer integration:

```powershell
claude plugin marketplace add earthtojake/text-to-cad
claude plugin install text-to-cad@earthtojake
```

## Build

One script per model is the single source of truth. Running it writes every declared format together:

```powershell
.venv\Scripts\python models\src\turbofan.py    # -> models/STEP, models/STL, models/GLB (~15 min)
.venv\Scripts\python models\src\turbojet.py
.venv\Scripts\python models\src\naca_lewis_16in_ramjet.py
.venv\Scripts\python models\src\nuclear_turbojet.py
.venv\Scripts\python models\src\tsirkon.py
.venv\Scripts\python models\src\oreshnik.py
.venv\Scripts\python models\src\f1.py
```

Outputs are cached by cadgen and only rebuilt when the script (or `models/src/lib/`) changes; add
`--force` to rebuild anyway. Generated files are git-ignored; rebuild them after cloning.

```
models/
  src/            model scripts (edit these)
  src/lib/        shared factories: revolve profiles, blade rows, clearances (shapes.py)
  STEP/ STL/ GLB/ generated exports
  SolidWorks/     generated: <model>/ (solidworks_build.py), imported/<model>/ (solidworks_import.py)
integrations/     solidworks/ (native builder, editor, verify, STEP import), freecad/, fusion/, onshape/
resources/        source reports (NASA NTRS, public domain) + digitized figures and data
```

Tunable dimensions sit as constants and tables at the top of each script (gas-path radii, stage
positions, blade counts, clearances). Each script's `parts()` returns one recipe per part: a list
of named ops (revolve, offset revolve, offset ring, spline, cut, blade ring, pins, loft, duct, fins, pipe; see `lib/shapes.py`; missile helpers: shells, ogives, solid motors in `lib/rocket.py`). cadgen builds the
STEP/STL/GLB from the recipes and `integrations/solidworks/solidworks_build.py` builds the same recipes as native
SolidWorks features. Blade rows come from `stage()`, which sizes tips and roots so flat blade
corners never cut into the casing.

## View

- **CAD Viewer** (bundled with cadgen, runs locally in the browser):
  ```powershell
  .venv\Scripts\python tools\start_viewer.py --open
  .venv\Scripts\python tools\start_viewer.py turbofan --open
  ```
  Or double-click `Open CAD Viewer.cmd` in the project root. The launcher serves
  `models/`, starts or reuses a background viewer, verifies its root and prints
  the actual URL. Ports can change; use that URL. Expand **STEP** in the file
  panel and select a model. Opens STEP, STL and GLB; STEP supports topology
  selection and measurement. See [viewer operation and troubleshooting](docs/viewer.md).
  Settings provide clipping/sections and display presets.
- **PyVista** (desktop window, local OpenGL):
  ```powershell
  .venv\Scripts\python -c "import pyvista as pv; p = pv.Plotter(); p.import_gltf('models/GLB/turbofan.glb'); p.show()"
  ```
- **Snapshot to PNG**: `cd models; ..\.venv\Scripts\python -m cadgen.cli step snapshot STEP/turbojet.step ../tmp/view.png [--mode section] [--camera 200:15]`

See [local installation and update notes](docs/local-installation.md) for the
engine, viewer and plugin locations. For a full export-access check:

```powershell
.venv\Scripts\python tools\start_viewer.py --check-all
```

## CAD platform integrations

STEP is the exchange format: the Python script stays the master, the CAD platform receives a
non-parametric (dumb-solid) import. Edit the script, rebuild, re-import.

| Script | Platform | How it connects | Status |
|---|---|---|---|
| `integrations/solidworks/solidworks_import.py` | SolidWorks (Windows) | COM API via pywin32; imports STEP, saves `.SLDASM` + one `.SLDPRT` per part to `models/SolidWorks/imported/<name>/` | Tested with SOLIDWORKS 2026 SP3 (3DEXPERIENCE): all three engines import and save; the reopened ramjet assembly resolves all 6 parts from the output folder |
| `integrations/fusion/` | Autodesk Fusion | Fusion script (runs inside Fusion only): file picker, imports each STEP into a new design | Not tested (Fusion not installed here) |
| `integrations/onshape/onshape_import.py` | Onshape | REST API (`/translations`), API-key basic auth; creates or reuses a document | Not tested (needs API keys) |

```powershell
# SolidWorks: open SolidWorks and log in first (the 3DEXPERIENCE edition cannot be started over COM)
.venv\Scripts\python integrations\solidworks\solidworks_import.py models\STEP\turbofan.step [more.step ...] [--close] [--out DIR]

# Onshape: keys from https://dev-portal.onshape.com/keys
$env:ONSHAPE_ACCESS_KEY = "..."; $env:ONSHAPE_SECRET_KEY = "..."
.venv\Scripts\python integrations\onshape\onshape_import.py models\STEP\turbofan.step [--document <id>] [--flatten]
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
# build a model as native parts + assembly -> models/SolidWorks/<model>/
.venv\Scripts\python integrations\solidworks\solidworks_build.py MODEL [--parts fan nacelle]   # MODEL = script name in models/src

# check the native parts against the cadgen STEP (needs models/STEP/<model>.step)
.venv\Scripts\python integrations\solidworks\solidworks_verify.py turbofan

# inspect and edit any .SLDPRT/.SLDASM (rebuilds, refuses to save on rebuild errors)
.venv\Scripts\python integrations\solidworks\solidworks_edit.py list models\SolidWorks\nuclear_turbojet\nose_cone.SLDPRT
.venv\Scripts\python integrations\solidworks\solidworks_edit.py set  models\SolidWorks\nuclear_turbojet\nose_cone.SLDPRT InletStruts_count=6 r2@NoseBodyProfile=250
.venv\Scripts\python integrations\solidworks\solidworks_edit.py suppress models\SolidWorks\nuclear_turbojet\nose_cone.SLDPRT InletStruts
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
(`models/FreeCAD/<model>.FCStd`, git-ignored) and checks every part against the cadgen STEP:

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

1. **Develop in build123d** (`models/src/*.py`): layout, proportions, clearances, stage counts.
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
.venv\Scripts\python tools\render_check.py models\STEP\tsirkon.step --hide launch_shroud `
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
parts = {c.label: c for c in read_step("models/STEP/turbojet.step").leaves}
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
  the helper validates the 0.7.10 launch sites and preserves this local fix.
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
