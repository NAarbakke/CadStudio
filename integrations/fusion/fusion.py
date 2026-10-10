"""Fusion script: import CadStudio STEP files, each into a new Fusion design.

Install: Fusion > Utilities > Scripts and Add-Ins > "+" > Script from my computer >
pick this fusion folder, then Run it and choose one or more .step files. Fusion requires the folder,
.py and .manifest to share a name, so keep them as fusion/fusion.*.
Fusion runs scripts only inside the app; there is no external API to drive it.
"""
import os
import traceback

import adsk.core

DEFAULT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        dialog = ui.createFileDialog()
        dialog.title = "Import STEP into Fusion"
        dialog.filter = "STEP files (*.step;*.stp)"
        dialog.isMultiSelectEnabled = True
        if os.path.isdir(DEFAULT_DIR):
            dialog.initialDirectory = DEFAULT_DIR
        if dialog.showOpen() != adsk.core.DialogResults.DialogOK:
            return
        for path in dialog.filenames:
            options = app.importManager.createSTEPImportOptions(path)
            app.importManager.importToNewDocument(options)
        ui.messageBox(f"Imported {len(dialog.filenames)} file(s). Save each design to your Fusion project to keep it.")
    except Exception:
        if ui:
            ui.messageBox("Import failed:\n" + traceback.format_exc())
