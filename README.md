# CadStudio

Parametric CAD models written as Python code (build123d on the OpenCascade kernel, via the
[text-to-cad](https://github.com/earthtojake/text-to-cad) `cadgen` package), exported to STEP / STL / GLB
and pushed into SolidWorks, Fusion or Onshape.

| Model | Source script | What it is | Basis |
|---|---|---|---|
| Turbofan | `models/src/turbofan.py` | GE/NASA Energy Efficient Engine (E3): two-spool, long-duct mixed-flow turbofan, 12 parts | Dimensions and flowpath from the E3 NASA report ([resources/README.md](resources/README.md)) |
| Turbojet | `models/src/turbojet.py` | NASA Lewis small expendable turbojet: single spool, 4-stage compressor, annular combustor, 1-stage turbine, 11 parts | Dimensions and flowpath from the NASA report ([resources/README.md](resources/README.md)) |
| Ramjet | `models/src/ramjet.py` | Axisymmetric ramjet: inlet spike, diffuser, fuel ring, V-gutter flame holders, CD nozzle, 6 parts | Generic proportions (not from a source document) |

All engine models are display/study models: the envelope and flowpath follow the sources, but blade
counts (except the E3 fan), airfoils (flat or elliptical sections) and internal structure are simplified.
Units are mm; the engine axis is +X.

## Setup

Requires Python 3.11+ (tested on 3.13, Windows 11).

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium   # used for snapshot renders
.venv\Scripts\python -m cadgen.cli doctor <path-to-installed-cad-skill>   # checks cadgen + OpenCascade kernel
```

For Claude Code, the text-to-cad plugin provides the `cad` / `cad-viewer` skills:

```powershell
claude plugin marketplace add earthtojake/text-to-cad
claude plugin install cad@text-to-cad
```

## Build

One script per model is the single source of truth. Running it writes every declared format together:

```powershell
.venv\Scripts\python models\src\turbofan.py    # -> models/STEP, models/STL, models/GLB (~3.5 min)
.venv\Scripts\python models\src\turbojet.py
.venv\Scripts\python models\src\ramjet.py
```

Outputs are cached by cadgen and only rebuilt when the script (or `models/src/lib/`) changes; add
`--force` to rebuild anyway. Generated files are git-ignored; rebuild them after cloning.

```
models/
  src/            model scripts (edit these)
  src/lib/        shared factories: revolve profiles, blade rows, clearances (shapes.py)
  STEP/ STL/ GLB/ generated exports
  SolidWorks/     generated: <model>/ (sw_build.py), imported/<model>/ (solidworks_import.py)
integrations/     native SolidWorks builder/editor; STEP import into SolidWorks, Fusion, Onshape
resources/        source reports (NASA NTRS, public domain) + digitized figures and data
```

Tunable dimensions sit as constants and tables at the top of each script (gas-path radii, stage
positions, blade counts, clearances). Each script's `parts()` returns one recipe per part: a list
of named ops (revolve, spline, cut, blade ring, pins, loft; see `lib/shapes.py`). cadgen builds the
STEP/STL/GLB from the recipes and `integrations/sw_build.py` builds the same recipes as native
SolidWorks features. Blade rows come from `stage()`, which sizes tips and roots so flat blade
corners never cut into the casing.

## View

- **CAD Viewer** (bundled with cadgen, runs locally in the browser):
  ```powershell
  cd models; ..\.venv\Scripts\python -m cadgen.viewer --host 127.0.0.1
  ```
  Opens at `http://127.0.0.1:3245/`. Opens STEP, STL and GLB; lets you hide, isolate or explode parts;
  Display > Clip cuts a section to see inside the engines; the Render mode is the photographic view.
- **PyVista** (desktop window, local OpenGL):
  ```powershell
  .venv\Scripts\python -c "import pyvista as pv; p = pv.Plotter(); p.import_gltf('models/GLB/turbofan.glb'); p.show()"
  ```
- **Snapshot to PNG**: `cd models; ..\.venv\Scripts\python -m cadgen.cli step snapshot STEP/turbojet.step ../tmp/view.png [--mode section] [--camera 200:15]`

## CAD platform integrations

STEP is the exchange format: the Python script stays the master, the CAD platform receives a
non-parametric (dumb-solid) import. Edit the script, rebuild, re-import.

| Script | Platform | How it connects | Status |
|---|---|---|---|
| `integrations/solidworks_import.py` | SolidWorks (Windows) | COM API via pywin32; imports STEP, saves `.SLDASM` + one `.SLDPRT` per part to `models/SolidWorks/imported/<name>/` | Tested with SOLIDWORKS 2026 SP3 (3DEXPERIENCE): all three engines import and save; the reopened ramjet assembly resolves all 6 parts from the output folder |
| `integrations/fusion/CadStudioImport/` | Autodesk Fusion | Fusion script (runs inside Fusion only): file picker, imports each STEP into a new design | Not tested (Fusion not installed here) |
| `integrations/onshape_import.py` | Onshape | REST API (`/translations`), API-key basic auth; creates or reuses a document | Not tested (needs API keys) |

```powershell
# SolidWorks: open SolidWorks and log in first (the 3DEXPERIENCE edition cannot be started over COM)
.venv\Scripts\python integrations\solidworks_import.py models\STEP\turbofan.step [more.step ...] [--close] [--out DIR]

# Onshape: keys from https://dev-portal.onshape.com/keys
$env:ONSHAPE_ACCESS_KEY = "..."; $env:ONSHAPE_SECRET_KEY = "..."
.venv\Scripts\python integrations\onshape_import.py models\STEP\turbofan.step [--document <id>] [--flatten]
```

Fusion: Utilities > Scripts and Add-Ins > "+" > Script from my computer > pick
`integrations/fusion/CadStudioImport`, then Run.

Notes:
- SolidWorks loads STEP through 3D Interconnect (parts land in a temp folder); the script saves parts
  first, then the assembly, so references point into the output folder. Paths are made absolute
  because SolidWorks resolves relative paths against its own working directory.
- Re-importing creates new documents; none of the platforms keeps downstream features on a dumb
  import across changes, so do detailing (drawings, fillets on imported bodies) only on a frozen model.
- `solidworks_import.py` uses `sw_api.py` (typed COM wrappers) and default import options; retested
  on the ramjet (6 parts, reopened assembly resolves every part from the output folder).

## Native parametric SolidWorks (no STEP)

`integrations/sw_api.py` drives SolidWorks' own modeller over COM, so the result has a real feature
tree: fully defined sketches, named dimensions, circular patterns driven by global variables.
No MCP server is needed; plain Python + pywin32 talks to SolidWorks directly.

```powershell
# build a model as native parts + assembly -> models/SolidWorks/<model>/
.venv\Scripts\python integrations\sw_build.py ramjet|turbojet|turbofan [--parts fan nacelle]

# check the native parts against the cadgen STEP (needs models/STEP/<model>.step)
.venv\Scripts\python integrations\sw_verify.py turbofan

# inspect and edit any .SLDPRT/.SLDASM (rebuilds, refuses to save on rebuild errors)
.venv\Scripts\python integrations\sw_edit.py list models\SolidWorks\ramjet\inlet.SLDPRT
.venv\Scripts\python integrations\sw_edit.py set  models\SolidWorks\ramjet\inlet.SLDPRT SpikeStruts_count=6 r1@CowlProfile=210
.venv\Scripts\python integrations\sw_edit.py suppress models\SolidWorks\ramjet\inlet.SLDPRT SpikeStruts
```

- Feature tree per recipe op: revolves/cuts/splines are `<Name>Profile` sketches with every
  vertex dimensioned `x<i>`/`r<i>` from the origin; blade/pin rows are `<Name>Plane` +
  `<Name>Sketch` + `<Name>Blade` (span `D1@<Name>Blade`) + pattern `<Name>` driven by global
  `<Name>_count`; the fan blade is a loft through eight closed-spline sections. Stage names follow the
  scripts: `HPC3Rotor`, `LPT2Nozzle`, `Comp1Stator`, `FanBlades`, ...
- Blade sections sit on reference planes (hidden) and are fixed geometry; change span and count
  by dimension/global, change airfoil shape in the Python recipe.
- Free-standing rows (stator vanes) are body patterns; rows on a disk are feature patterns.
- `sw_verify.py` exports each part to STEP and compares it with the cadgen part: volume and the
  overlap volume (fuzzy boolean), plus rebuild errors and fully defined sketches. Tolerance 0.1 %,
  0.2 % for lofted parts (see Known issues).
- Build time (SOLIDWORKS 2026): ramjet ~1.5 min, turbojet ~4 min, turbofan ~30 min (the HPC stator
  part alone ~12 min: ten free-standing vane rows, each a body pattern).
- Files saved by a 3DEXPERIENCE Makers licence are flagged personal-use.
- pywin32 type wrappers: `sw_api` generates them on first use (`gencache.EnsureModule`); after a
  SolidWorks upgrade delete `%LOCALAPPDATA%\Temp\gen_py` to regenerate.

## Recommended workflow

1. **Develop in build123d** (`models/src/*.py`): layout, proportions, clearances, stage counts.
   Fast iteration, diffable in git, checked with the viewer and `read_step`. Get it ~90 % there.
2. **Freeze and hand over to SolidWorks natively** (`sw_build.py`) rather than as STEP, so the
   SolidWorks model has editable dimensions instead of dumb solids.
3. **Final tuning in SolidWorks**, by hand or with `sw_edit.py`: dimension tweaks, fillets,
   drawings, mates, materials, simulation.
4. **Decide once which side is master.** After detailing starts in SolidWorks, regenerating from
   Python overwrites that work. Carry big changes back into the Python data (and rebuild), keep
   small, detail-level changes in SolidWorks only.

STEP import (`solidworks_import.py`) remains the quick path for looking at a model or sharing it
with someone else.

## Verification done

Checks run with `read_step` on the saved STEP files (rerun with the snippet below after changing geometry):

- Every part of every model is a valid solid.
- Turbojet: envelope 965 × Ø292 mm (matches the source); rotor clears all static parts (min 1.16 mm).
- Turbofan (E3): envelope x −1590…4580 mm, Ø2489 mm (matches Table I); fan tip clearance ≥ 7.1 mm;
  LP spool clears casing 2.99 mm, frame hub/plug 5 mm, stators ≥ 12 mm; HP spool clears casing 2.19 mm, HPC stators 2.38 mm, frame hub 4.34 mm;
  LP–HP spool gap 20 mm.
- Ramjet: parts meet with zero overlap.
- Native SolidWorks vs cadgen (`sw_verify.py`): every part of the three engines has fully defined
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
  open a console window. Local fix: `CREATE_NO_WINDOW` added to the three `subprocess.Popen` calls in
  `.venv/Lib/site-packages/cadgen/daemon/{pool,executors,artifacts}.py`. It is lost on reinstall;
  worth reporting upstream to text-to-cad.
- The turbofan build takes ~3.5 min and its STEP is ~40 MB (≈1,400 blade solids).
- **Twisted lofts**: a loft between two ellipses has no defined start point, so with twist the
  kernels pair the wrong points (OpenCascade pinched the old fan blades to ~0.9 L, SolidWorks
  bulged them). Blade sections are now closed splines through matched points (`blade_section()`),
  eight stations root to tip. The sections are identical in both kernels, but OpenCascade's smooth
  loft overshoots ~12 % next to the end sections, so cadgen lofts ruled (straight between stations);
  that matches SolidWorks' smooth loft to 0.006 % in blade volume, slices within 0.5 % (1.8 % near
  the tip).
- **Volumes of spline solids**: build123d's `.volume` is ~10 % off on the lofted fan (132.9 vs
  146.7 L); use adaptive integration (`volume()` in `integrations/sw_verify.py`) for such parts.
- Plain booleans between two nearly identical solids (e.g. SolidWorks export vs cadgen part) can
  return nothing; use a fuzzy boolean (`common_volume()` in `sw_verify.py`).
