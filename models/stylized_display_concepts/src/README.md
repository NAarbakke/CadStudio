# Stylized display concepts

Two original decorative sculptures with invented proportions. These are not
reconstructions or scale replicas of the DF-17 or any North Korean vehicle.
No reference photographs, measured weapon dimensions, or aerodynamic data were
used. All lengths below are dimensions of the decorative objects only.

| Entrypoint | Purpose | Invented size (mm) | Exports |
| --- | --- | --- | --- |
| `delta_display.py` | Broad orange delta sculpture | 120 x 68 x 18 | STEP, STL, GLB |
| `dart_display.py` | Narrow blue dart sculpture | 136 x 60 x 22 | STEP, STL, GLB |
| `display_pair.py` | Both sculptures placed side by side | See individual parts | STEP, GLB |

Both individual models are intended as single solid ornaments with flat
undersides at Z=0. Tips and decorative lobes are deliberately thick and blunt.
They have no internal mechanisms or functional interfaces. Colours are retained
in STEP/GLB; STL contains geometry only. STL coordinates are in millimetres.

From the CadStudio workspace root, use the existing project environment:

```powershell
.\.venv\Scripts\python.exe models\stylized_display_concepts\src\display_pair.py
```

Building the pair first builds and exports each individual model sequentially,
then reuses those results in the pair. This avoids concurrent child-worker
startup timeouts observed in this Windows installation. The existing
environment has cadgen 0.7.19; it is left unchanged. Geometry helpers are in
`src/lib/display_shapes.py`; edit source and rerun the pair to regenerate.
The complete pair build also closes STL tessellation seams by welding vertices
within 0.005 mm. It does not change the STEP solids. The finishing report records
the maximum displacement; verification checks the resulting STL edge pairing,
orientation, connected shell, dimensions, and volume against the STEP solid.
Use `display_pair.py` for the complete export and finishing pipeline.

Verification and views:

```powershell
.\.venv\Scripts\python.exe models\stylized_display_concepts\checks\verify_outputs.py
.\.venv\Scripts\python.exe -m cadgen.cli step snapshot --job models\stylized_display_concepts\checks\views.json
```

Top and side images show only these invented decorative designs. Snapshot and
geometry results are recorded in `profile/`. Physical printability has not been
established by a test print or slicer run.
