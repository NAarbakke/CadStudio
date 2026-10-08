# Verification record

## Viewer and saved exports, 2026-10-03

Viewer version: 0.7.10. Served folder: the project's `models/` directory
(Windows 11 at the time of this record).

`tools/start_viewer.py --check-all` completed successfully for all 21 expected
exports. Each STEP's current assembly JSON and native component geometry
could be read over HTTP. Every GLB and STL could be downloaded and was non-empty.

| Saved STEP | Assembly parts |
|---|---:|
| `rocketdyne_f1.step` | 12 |
| `naca_lewis_16in_ramjet.step` | 9 |
| `lyulka_nuclear_turbojet.step` | 13 |
| `oreshnik.step` | 18 |
| `tsirkon.step` | 17 |
| `ge_e3_turbofan.step` | 12 |
| `nasa_lewis_small_turbojet.step` | 14 |

Each STEP was selected from the viewer's file panel and visually checked in
Chrome after geometry finished loading. This confirms file switching and
browser rendering for the saved exports. It does not certify dimensions,
clearances or manufacturing suitability, or prove that an export matches
unbuilt source edits. The viewer never runs a model source when it opens a file.

Reproduce the access checks from the project root:

```powershell
.venv\Scripts\python tools\start_viewer.py --check-all   # Windows
```

```bash
.venv/bin/python tools/start_viewer.py --check-all       # Ubuntu
```

The launcher writes its machine-readable session to ignored
`tmp/viewer/session.json`. An invocation with `--check-all` includes individual
export results; a subsequent invocation without it replaces the record with
links and server information only. Run the check again to refresh the results
after rebuilding exports, reinstalling cadgen or restarting the viewer.

## Ramjet rename and report framework, 2026-10-03

- The old and renamed STEP both contained nine components and matching CAD
  volumes within relative tolerance `1e-9`: `119497291.45811792 mm3`.
- The current six-page engineering report was rendered and visually reviewed
  on every page: four A4 narrative/render/table pages and two A3 dimensioned
  vector drawing sheets. Final drawing paths and text remained within page bounds.
- Five engineering-report tests passed: duplicate YAML keys, unit conversion,
  invalid coordinates/units, density-to-mass conversion and unknown materials,
  and missing component/material assignments. The tests were rerun after the
  viewer/documentation update and all five passed.
- `pip check` found no broken requirements after the report dependencies
  were installed.

The report paths, generation command and YAML schema are documented in
[engineering reports](engineering-reports.md). Geometry dimensions remain in
Python; report definitions use YAML. Unknown material and mass values remain
unknown unless explicit evidence or density assignments are supplied.

Historical geometry and native FreeCAD/SolidWorks verification remains in
the main README. Those results apply to the revisions described there; they
were not all rerun during the viewer repair.
