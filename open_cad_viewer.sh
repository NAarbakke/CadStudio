#!/bin/sh
# Linux counterpart of "Open CAD Viewer.cmd"
cd "$(dirname "$0")" || exit 1
exec .venv/bin/python tools/start_viewer.py --open
