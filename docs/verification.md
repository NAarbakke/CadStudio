# Verification record

## Engine update to cadgen 0.7.19, 2026-10-10

cadgen and the text-to-cad plugin were updated from 0.7.10 to 0.7.19 (Windows 11).
`pip check` found no broken requirements, the 13 project tests passed and
`tools/patch_cadgen_windows.py` patched the four worker launch sites.

`tools/start_viewer.py --check-all` completed successfully for all 21 expected
exports on viewer 0.7.19. The launcher was adapted to that viewer's HTTP routes:
files are named by absolute path, the compiled tree comes from the file's
catalog row, and the server reports the folder it was started in, not a served root.

| Saved STEP | Assembly parts |
|---|---:|
| `rocketdyne_f1.step` | 42 |
| `naca_lewis_16in_ramjet.step` | 15 |
| `lyulka_nuclear_turbojet.step` | 13 |
| `oreshnik.step` | 18 |
| `tsirkon.step` | 17 |
| `ge_e3_turbofan.step` | 18 |
| `nasa_lewis_small_turbojet.step` | 21 |

`models/tsirkon/src/tsirkon.py` was rebuilt on the new engine and passed
`tools/model_check.py` (17 parts, 1654.2 L, no intersections). The other six
exports were read as saved and not rebuilt, and no model was visually reviewed
in the browser after the update.

## Per-model folders, Raptor models and nuclear turbojet upgrade, 2026-10-10

Sources and exports moved to `models/<model>/{src,STEP,STL,GLB,FreeCAD,SolidWorks}` with the shared
code in `models/lib/`. All seven existing models were rebuilt from their new locations on cadgen 0.7.19.

`tools/model_check.py` on the rebuilt STEP files (every part a valid solid, no two parts intersecting):

| Saved STEP | Parts | Result |
|---|---:|---|
| `spacex_raptor_1.step` (new) | 36 | OK, envelope 3100 x Ø1300 mm |
| `spacex_raptor_2.step` (new) | 30 | OK, envelope 3100 x Ø1300 mm |
| `spacex_raptor_3.step` (new) | 21 | OK, envelope 3100 x Ø1300 mm |
| `lyulka_nuclear_turbojet.step` (upgraded) | 23 | OK |
| `ge_e3_turbofan.step` | 18 | OK |
| `naca_lewis_16in_ramjet.step` | 15 | OK |
| `nasa_lewis_small_turbojet.step` | 21 | OK (one boolean hit on the rotor cleared as a false hit) |
| `oreshnik.step` | 18 | OK after the four PBCS struts were moved aft of the PBV frame (they overlapped it by 97,703 mm3) |

The Raptor models and the nuclear turbojet were reviewed as Render-display GLB snapshots
(`tmp/check/<model>_render.png`). The Raptor layout was then reworked against the SpaceX photographs (`profile_builder/Raptor/README.md`) and rebuilt, then dressed with swept ducts (the new `sweep` op), small lines, controllers and wiring; the part counts above are the final models. The three Raptors were also built in FreeCAD
(`integrations/freecad/freecad_build.py`): every part matches the cadgen part at 100.00 % overlap.
The upgraded nuclear turbojet was not rebuilt in FreeCAD, and the fidelity report
(`reports/latex/model_fidelity.py`) was not regenerated.

`tools/start_viewer.py --check-all` read all 30 exports of the ten built models on viewer 0.7.19 and
skipped the text-to-cad example projects, which have never been built.

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
