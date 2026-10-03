@echo off
"%~dp0.venv\Scripts\python.exe" "%~dp0tools\start_viewer.py" --open
if errorlevel 1 pause
