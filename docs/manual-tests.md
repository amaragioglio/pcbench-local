# Manual Tests

These checks cover flows that are hard to validate safely in automated CI.

## Windows Setup

Goal: a fresh Windows user can reach the wizard from `setup.bat`.

Steps:

1. Open PowerShell in the project directory.
2. Run `.\setup.bat`.
3. If Python is missing, verify the script opens the official Python download page and exits.
4. If Python is present, verify it creates `.venv`, installs `requirements-windows.txt`, and launches the wizard.

Expected result: the numbered wizard appears and can start a benchmark.

## Windows Launcher

Goal: `pcbench.bat` launches the wizard after setup.

Steps:

1. Run `.\setup.bat` once.
2. Run `.\pcbench.bat`.

Expected result: the wizard opens using `.venv\Scripts\python.exe`.

## HTML Open Prompt

Goal: interactive runs can open the HTML report.

Steps:

1. Run `.\.venv\Scripts\python.exe main.py run --quick --reports json,html`.
2. When prompted, answer `y` to open the HTML report.

Expected result: the generated HTML report opens in the default browser.

## Ctrl+C Cleanup

Goal: interrupting a disk benchmark does not leave the temp file behind.

Steps:

1. Run `.\.venv\Scripts\python.exe main.py run --full --reports json`.
2. Press `Ctrl+C` while the disk benchmark is active.
3. Check `%TEMP%\pcbench-local\disk_benchmark.tmp`.

Expected result: the command exits cleanly and the temp file is removed.

## Windows Elevation

Goal: `--elevate` requests UAC only when explicitly asked.

Steps:

1. Run `.\.venv\Scripts\python.exe main.py run --quick --skip-gpu --skip-network --elevate`.
2. Accept the UAC prompt.

Expected result: PCBench relaunches in an elevated session and the security audit is less likely to be marked partial.
