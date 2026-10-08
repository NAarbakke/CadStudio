# Ubuntu setup

## Status

**The pinned engine does not install on Linux yet.** The project code has been
made portable, but `pip install -r requirements.txt` fails on Linux because of
one dependency:

- `cadgen[snapshot]==0.7.10` requires `cadquery-ocp-novtk>=7.9,<8` (the
  OpenCascade bindings).
- `cadquery-ocp-novtk` 7.9.x is published with Windows wheels only. Checked on
  PyPI for `linux_x86_64`, `manylinux2014`, `manylinux_2_17`, `manylinux_2_28`
  and `manylinux_2_27` for Python 3.11, 3.12 and 3.13: no 7.9 file exists.
- Linux only has 8.0.1.x, which cadgen excludes.
- Newer cadgen releases (0.7.12, 0.7.17) have the same `<8` requirement.

Options, none tested yet:

1. Install OpenCascade 7.9 from conda-forge (`cadquery-ocp`) into a conda
   environment, then `pip install --no-deps` the rest. Unverified: I could not
   query conda-forge from the development machine.
2. Move the project to OCP 8 with a cadgen release that accepts it. This changes
   the geometry kernel, so the numbers the README reports (100.00 % match
   against cadgen 0.7.10) would have to be re-verified.
3. Build OCP from source on Ubuntu. Slow and fragile.

Until one of these is chosen, the commands below are the intended steps, not
tested steps.

## Not supported on Linux

- **SolidWorks** (`integrations/solidworks/`): COM automation, Windows only.
  The scripts stop with a message on Linux.
- **Autodesk Fusion** (`integrations/fusion/`): runs inside Fusion, which is
  Windows and macOS only.
- **`tools/patch_cadgen_windows.py`**: not needed. It does nothing on Linux.

FreeCAD (`integrations/freecad/`) works if `freecadcmd` is on the PATH
(`sudo apt install freecad`), or set `FREECADCMD` to its path.
Onshape (`integrations/onshape/`) needs internet access and `requests`.

## Steps

System packages (names are typical for Ubuntu 24.04; add any the `doctor`
command or a missing shared library asks for):

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git libgl1 libglu1-mesa
```

From the project root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install --with-deps chromium   # snapshot renders; --with-deps installs system libraries via apt
.venv/bin/python -m cadgen.cli doctor <path-to-installed-cad-skill>
```

Build and view:

```bash
.venv/bin/python models/src/naca_lewis_16in_ramjet.py
.venv/bin/python tools/engineering_report.py reports/naca_lewis_16in_ramjet.yaml
./open_cad_viewer.sh
```

LaTeX reports (optional) need a TeX installation that provides `latexmk` and
LuaLaTeX:

```bash
sudo apt install -y latexmk texlive-luatex texlive-latex-recommended texlive-fonts-recommended texlive-science lmodern
```

## Path conventions

The other docs show Windows (PowerShell) and Ubuntu commands side by side. On
Ubuntu, `.venv/bin/python` replaces `.venv\Scripts\python` and forward slashes
replace backslashes in paths.
