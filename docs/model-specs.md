# Model specification format

## Current state

The seven models in `models/src/` are Python scripts. Dimensions, stations,
profile tables, counts and derived formulas live in constants and `parts()`
recipes. `lib/shapes.py` builds those recipes; the native CAD integrations read
the same recipes. Part entries contain a label, display colour and operations.
They do not currently assign physical materials, densities or masses. A colour
is not evidence of a material.

## Recommendation

Use YAML for externally supplied specifications, and Python for geometry and
derived calculations. Migrate one model at a time once its specification is
ready. This update does not move existing dimensions out of Python.

Place future specifications in `models/specs/<model>.yaml`. Store named,
independent dimensions and measured profile tables there. Keep interpolation,
trigonometry, unit conversion, geometry operations and calculated dimensions
in Python. Do not embed executable Python expressions or CAD operation recipes
in YAML. Both cadgen and the native integrations must consume the same parsed
specification through the model's geometry factories.

Use explicit units, references and evidence status for each physical quantity.
Retain source-native units (such as inches) and convert to millimetres once at
the geometry boundary. Distinguish a reported complete-engine mass from a mass
estimated from the simplified model's volume. Leave unknown materials, density
and mass as `null` rather than inferring them from colours or appearance.

Example proposal, using dimensions already recorded in `naca_lewis_16in_ramjet.py`:

```yaml
schema_version: 1
model: naca_lewis_16in_ramjet
coordinate_system:
  axis: +X
  origin: inlet_lip
  geometry_length_unit: mm
sources:
  naca_e51c16:
    file: profile_builder/Ramjet/RM-E51C16_16in_ramjet_free_jet_1951.pdf
dimensions:
  chamber_inside_diameter:
    value: 16.0
    unit: in
    status: reported
    source: naca_e51c16
    locator: Figure 1
  shell_wall_thickness:
    value: 0.1875
    unit: in
    status: assumed
    note: Existing display-model assumption
mass:
  reported_dry_mass:
    value: null
    unit: kg
    status: unknown
materials: {}
parts:
  combustion_chamber:
    material: null
    display_colour: "#6B717A"
```

Material entries should identify a sourced grade and density, with units such
as `kg/m3`. Part assignments should refer to those material IDs. Calculated
part mass uses `volume_mm3 * density_kg_m3 * 1e-9` and belongs in a generated
report with its assumptions, rather than being copied back into the input YAML.

## Loading and rebuilds

Adopting YAML requires a pinned YAML parser and validation of schema version,
units, finite positive dimensions, integer counts, source IDs and material IDs.
Use `yaml.safe_load`; reject duplicate keys so a typo cannot silently override
a dimension. The example above is documentation, not an active build input.

Read the file inside the decorated model's build, anchored to `__file__`.
Cadgen 0.7.10 tracks files opened by a model automatically; an explicit
`declare_input` call is no longer needed. Verify that specification edits
invalidate the build when migrating a model.
Pass the validated values into ordinary Python factories; avoid mutable global
configuration. The native integrations can use the same loader outside a
cadgen build.

```python
from pathlib import Path

# Inside the decorated model function; safe_spec_loader is a future project helper.
path = Path(__file__).resolve().parents[1] / "specs" / "naca_lewis_16in_ramjet.yaml"
spec = safe_spec_loader(path)
shape = build_naca_lewis_16in_ramjet(spec)
```

Before migrating a model, compare its old and new recipes and exported geometry,
verify that editing YAML triggers a rebuild, and check native CAD imports use
the same values. Keep the input YAML as the single source for migrated quantities.

The engineering-report framework now uses `reports/<model>.yaml` for report
content, views, drawing callouts, source notes and optional material densities.
These manifests document the model; they do not override geometry. Callouts may
bind to named numeric Python constants, with explicit units, so values need not
be duplicated between the source and its report.
