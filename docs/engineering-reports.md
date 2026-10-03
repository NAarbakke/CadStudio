# Engineering PDF reports

`tools/engineering_report.py` combines CAD renders, specification tables,
component measurements, material/mass entries, sources and vector engineering
drawings in one PDF. Its report definition is a YAML file under `reports/`.
The NACA Lewis 16-inch ramjet is the first working example.

## Generate

From the CadStudio root:

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python tools\patch_cadgen_windows.py
.venv\Scripts\python models\src\naca_lewis_16in_ramjet.py
.venv\Scripts\python tools\engineering_report.py reports\naca_lewis_16in_ramjet.yaml
```

The generator can regenerate the model first with `--build`. By default it
reports the saved STEP revision. `--reuse-renders` reuses image files only when
the STEP, source and manifest hashes match. `--output <path>.pdf` chooses a
different final destination.

The default deliverables are:

- `output/pdf/<model>_engineering_report.pdf`
- `output/pdf/<model>_engineering_report.json` with full input hashes, measured
  volume, geometry-validity result, component count and page sizes.

Intermediate images and drawing sheets live under ignored `tmp/reports/`.
Final reports are generated artifacts under ignored `output/`; retain the
generator, manifest and model source in Git.

## Define another report

Copy the example manifest and update its model paths, title, document ID,
views, dimensions and references. Paths in manifests are relative to the
CadStudio root, so the generator can be launched from any working directory.

`schema_version: 1` requires `title`, `model.source`, `model.step`, `renders`
and `drawings`. Optional fields include `subtitle`, `summary`, `status`,
`document_id`, `revision`, `specifications`, `sources`, `assumptions`,
`materials` and `part_materials`. Duplicate YAML keys are rejected.

Renders have unique `id` filenames, a `camera` preset or `azimuth:elevation`,
and a display preset such as `render` or `solid`. A section uses
`mode: section` and a plane such as `section: XY`. `hide` names actual STEP
component labels, which are resolved to CAD references before rendering.

Each drawing creates an ISO A-series sheet using cadgen's engineering drawing
API. Geometry is projected from the saved STEP with hidden-line removal.
The default layout has top, front and right views in third-angle arrangement.
Custom `views` specify view names and their centre positions `at` in sheet mm.
`parts` optionally selects named components; no simplified outline replaces
the selected geometry.

`scale` is the model-to-paper ratio: `0.0625` is 1:16. Native A3 drawing pages
are appended without resizing. Print those pages at actual size to retain the
title-block scale. Report narrative pages are A4.

Dimensions are grouped by view. Supported types are `overall`, `linear`,
`diameter`, `radius` and `note`. Overall extents come from the projected CAD;
linear dimensions measure two model-space points; radius/diameter callouts
require the feature's centre and radius. There is no arbitrary dimension-text
override. Literal coordinates are in model millimetres. A coordinate can bind
to a numeric Python model constant:

```yaml
type: linear
p1: [0, 0, 0]
p2: [{parameter: X_EXIT, unit: in}, 0, 0]
orientation: h
```

Bindings support `mm`, `in` and `m`, and apply unit conversion before drawing.
The named constant is read from the model source without building the model.
Geometry remains in Python; report YAML cannot override geometry parameters.
Choose callout points that belong to the feature or datum being measured.

## Materials and mass

Display colours do not imply physical materials. Unknown materials and masses
remain unknown. To calculate a component's model mass, supply a material with
an explicit positive density and assign its ID to an actual STEP label:

```yaml
materials:
  example_material:
    name: Documented material grade
    density_kg_m3: 7800
part_materials:
  component_label: example_material
```

The number above illustrates the format; it is not a ramjet assignment.
Calculated mass uses `CAD volume in mm3 * density in kg/m3 * 1e-9`. It describes
the simplified solid model, not a reported complete-engine dry mass. Identify
material evidence in the report's source and assumption notes.

## Verify

```powershell
.venv\Scripts\python -m unittest discover -s tests
```

The generator rejects invalid geometry, unknown components/materials, invalid
units, duplicate keys, non-finite coordinates and invalid densities. Cadgen
checks the vector drawing document and reports annotation/layout notices.
Page overflow is rejected rather than emitting clipped tables or paragraphs.
Review the rendered PDF pages after changing a manifest; drawing callout
placement and legibility still need visual inspection.
