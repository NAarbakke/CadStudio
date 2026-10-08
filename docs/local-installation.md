# Local installation and updates

Inventory recorded on 2026-10-03 on Windows 11. Paths are relative to the
project root, which is wherever the repository is cloned.

| Component | Location | Version / role |
|---|---|---|
| Project Python | `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Ubuntu) | Python 3.13 virtual environment |
| CAD engine | `.venv/Lib/site-packages/cadgen/` (Windows) or `.venv/lib/python3.*/site-packages/cadgen/` (Ubuntu) | cadgen 0.7.10, build123d/OpenCascade, exports and snapshots |
| Browser viewer | `cadgen/viewer/` inside the site-packages above | Viewer server; browser distribution bundled with cadgen |
| Model sources | `models/src/` | Python geometry and dimension constants |
| Exports | `models/STEP/`, `models/STL/`, `models/GLB/` | Generated files consumed by the viewer |
| Report definitions | `reports/` | YAML report content, views, dimension bindings and materials |
| Report outputs | `output/pdf/` | Generated PDF and provenance JSON |

The Python package is the executable CAD engine. The viewer is bundled with the
engine; there is no separate npm installation for it.

## Recreate the project environment

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python tools\patch_cadgen_windows.py
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python -m pip check
```

Ubuntu: the engine does not install on Linux yet. See [Ubuntu setup](ubuntu.md)
for the blocker and the intended steps. The intended commands are:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install --with-deps chromium
.venv/bin/python -m pip check
```

`tools/patch_cadgen_windows.py` is a Windows-only workaround for visible worker
consoles. It validates and patches four known launch sites in cadgen 0.7.10 and
is safe to rerun. It deliberately refuses a different cadgen version until those
launch sites are reviewed. Reinstalling cadgen replaces the patched package
files, so run it again afterwards. On Linux it does nothing.

## Upgrade procedure

1. Review the upstream release and installed CAD skill's migration guidance.
2. Update the engine pin in `requirements.txt` and install with the project
   interpreter.
3. On Windows, review and update the worker patch before applying it to a new
   engine version. Install the required snapshot Chromium runtime.
4. Stop the existing viewer, restart through `tools/start_viewer.py`, and reload
   its browser page. Use the URL it prints.
5. Run `pip check`, the project tests and `tools/start_viewer.py --check-all`.
   Build and visually review changed models; generate and visually review
   affected engineering reports. Record the versions and results in docs.

Geometry specifications currently remain in Python. Report YAML is active;
the proposed `models/specs/` geometry YAML schema has not been implemented.
See [model specifications](model-specs.md) and
[engineering reports](engineering-reports.md).

The ramjet stem is `naca_lewis_16in_ramjet` across current Python, STEP, STL,
GLB and FreeCAD files. Superseded generic raw exports were retained under
ignored `tmp/renamed_ramjet_exports/`. Historical six-part SolidWorks files
and FreeCAD backups are older revisions, not current nine-part exports.
