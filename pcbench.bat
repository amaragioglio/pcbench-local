@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo PCBench is not set up yet.
  echo Run setup.bat first.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" main.py wizard
pause
