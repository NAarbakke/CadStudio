# CAD Viewer

CAD Viewer is the browser application bundled with `cadgen==0.7.10` in the
project `.venv`. Its server runs on this Windows computer and serves `models/`.
A localhost link works on this computer while the server is running.

## Open and select models

Double-click `Open CAD Viewer.cmd` in the project root, or run from PowerShell:

```powershell
.venv\Scripts\python tools\start_viewer.py --open
.venv\Scripts\python tools\start_viewer.py turbofan --open
.venv\Scripts\python tools\start_viewer.py naca_lewis_16in_ramjet --open
```

The launcher finds or starts a detached viewer with `models/` as its working
directory. It checks the returned server root before printing its URL.
`--open` opens the system browser; omit it to print links only. It works from
any working directory when the script is invoked by its absolute path.
No model build is run by this launcher.

Use **Show files** at the top left, expand **STEP**, then select a filename.
The file name and browser URL should change. Wait for **Reading model** and
**Loading geometry** to finish. The turbofan and turbojet contain thousands
of airfoil faces and can take longer on a cold browser/cache.

| Model source stem | STEP file under the served directory |
|---|---|
| `f1` | `STEP/f1.step` |
| `naca_lewis_16in_ramjet` | `STEP/naca_lewis_16in_ramjet.step` |
| `nuclear_turbojet` | `STEP/nuclear_turbojet.step` |
| `oreshnik` | `STEP/oreshnik.step` |
| `tsirkon` | `STEP/tsirkon.step` |
| `turbofan` | `STEP/turbofan.step` |
| `turbojet` | `STEP/turbojet.step` |

For a visual-only mesh export, use the GLB folder or:

```powershell
.venv\Scripts\python tools\start_viewer.py turbofan --format GLB --open
```

STEP supports component selection and topology measurements; GLB/STL provide
mesh viewing. The viewer renders saved exports. Build the Python source after
editing geometry to update them.

## Lifecycle and ports

The port is chosen or reused by cadgen; it is not guaranteed to be 3245 or 3246.
Use the printed URL. The launcher records the current server, model links and
optional checks in ignored `tmp/viewer/session.json`. This file is a session
record, not a permanently valid endpoint.
Each invocation replaces this session record; use `--check-all` when you want
it to include the export-access results.

The detached server continues after the launcher exits. A Windows restart,
explicit stop, process termination or crash requires launching it again.
The project does not install an automatic logon service.

Underlying commands, from the project root:

```powershell
Push-Location models
..\.venv\Scripts\python -m cadgen.cli viewer --host 127.0.0.1 --json --detach
..\.venv\Scripts\python -m cadgen.cli viewer list --json
..\.venv\Scripts\python -m cadgen.cli viewer stop --port 3246
Pop-Location
```

Replace the stop port with the running instance's port. After upgrading cadgen,
stop and restart the viewer so its Python code and browser assets use the same
version. Reload the browser page.

## Diagnose opening failures

```powershell
.venv\Scripts\python tools\start_viewer.py --check-all
```

This checks every source's expected STEP, GLB and STL export. For STEP it
checks compilation status, reads the assembly document and downloads each
component's native geometry asset. A missing viewer cache is compiled from
the saved STEP without regenerating model geometry. For GLB/STL it verifies
that the exported file is served and non-empty. It prints individual failures,
writes the results to `tmp/viewer/session.json`, and exits nonzero if any check
fails. Browser appearance still needs a visual check.

- **Site cannot be reached / connection refused:** run the launcher and use
  its returned link. The previous server may have stopped or its port changed.
- **Empty file list:** check the printed `Serving:` path is this project's
  `models` directory, and expand the STEP folder in the panel.
- **Missing export:** run `.venv\Scripts\python models\src\<model>.py`.
  Outputs are ignored by Git and must be rebuilt after a fresh clone.
- **Compilation error:** retain the reported error and the launcher's server
  log location. Inspect it before forcing a rebuild or removing caches.
- **Old browser state after an update:** reload the page; if necessary use a
  hard reload with Ctrl+Shift+R after restarting the viewer.
- **Slow STEP opening:** allow geometry loading to finish. The saved GLB is
  an alternative for a visual check, but can also be large (the turbojet GLB
  checked on 2026-10-03 was about 310 MB). Opening the file does not rebuild
  its source script.

The restart investigation on 2026-10-03 found the advertised port had no live
listener. No crash traceback was present in its saved launch log, so the cause
of termination was not established. The model files were preserved; access
and visual checks are documented in `docs/verification.md`.
