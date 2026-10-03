# Local installation and updates

Local inventory recorded on 2026-10-03. The project is
`C:/Users/admin1/Documents/Projects/CadStudio`.

| Component | Local location | Version / role |
|---|---|---|
| Project Python | `.venv/Scripts/python.exe` | Python 3.13 virtual environment |
| CAD engine | `.venv/Lib/site-packages/cadgen/` | cadgen 0.7.10, build123d/OpenCascade, exports and snapshots |
| Browser viewer | `.venv/Lib/site-packages/cadgen/viewer/` | Viewer server; browser distribution bundled with cadgen |
| Codex plugin | `C:/Users/admin1/.codex/plugins/cache/earthtojake/text-to-cad/0.7.10/` | text-to-cad skill/tool instructions |
| Claude plugin | `C:/Users/admin1/.claude/plugins/cache/text-to-cad/text-to-cad/0.7.10/` | text-to-cad, existing local marketplace alias retained |
| Model sources | `models/src/` | Python geometry and dimension constants |
| Exports | `models/STEP/`, `models/STL/`, `models/GLB/` | Generated files consumed by the viewer |
| Report definitions | `reports/` | YAML report content, views, dimension bindings and materials |
| Report outputs | `output/pdf/` | Generated PDF and provenance JSON |

The Python package is the executable CAD engine. The plugins contain agent
instructions and integrations; their cache directories are separate from
the project's environment. Updating a plugin alone does not update this
project's pinned engine. The viewer is bundled with the engine; there is no
separate project npm installation for it.

## Recreate the project environment

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python tools\patch_cadgen_windows.py
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python -m pip check
```

`tools/patch_cadgen_windows.py` is the maintained local workaround for visible
worker consoles on Windows. It validates and patches four known launch sites
in cadgen 0.7.10 and is safe to rerun. It deliberately refuses a different
cadgen version until those launch sites are reviewed. Reinstalling cadgen
replaces the patched package files, so run it again afterwards.

## Upgrade procedure

1. Review the upstream release and installed CAD skill's migration guidance.
2. Update the engine pin in `requirements.txt` and install with the project
   interpreter. Update Codex/Claude plugins through their plugin managers.
   Existing marketplace aliases may differ between the two clients.
3. Review and update the Windows worker patch before applying it to a new
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
