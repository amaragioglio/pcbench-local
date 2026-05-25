from __future__ import annotations

import platform
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


TASK_NAME = "PCBench Weekly"


def schedule_weekly(args: Any) -> dict[str, Any]:
    command = _pcbench_run_command(args)
    system = platform.system()
    if system == "Windows":
        scheduled_command = _windows_command(command)
    else:
        scheduled_command = _cron_line(command)

    if getattr(args, "dry_run", False):
        return {"status": "dry_run", "platform": system, "command": scheduled_command}

    if system == "Windows":
        completed = subprocess.run(scheduled_command, capture_output=True, text=True, check=False)
        return _completed_result(system, scheduled_command, completed)

    return {
        "status": "manual",
        "platform": system,
        "command": scheduled_command,
        "message": "Add this line to crontab with `crontab -e`.",
    }


def _pcbench_run_command(args: Any) -> list[str]:
    python_or_exe = Path(sys.executable).resolve()
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    if python_or_exe.suffix.lower() == ".exe" and python_or_exe.name.lower().startswith("pcbench"):
        command = [str(python_or_exe), "run", "--quick", "--sanitize", "--reports", "json,html"]
    else:
        command = [str(python_or_exe), str(main_py), "run", "--quick", "--sanitize", "--reports", "json,html"]

    output_dir = getattr(args, "output_dir", None)
    if output_dir:
        command.extend(["--output-dir", str(output_dir)])
    return command


def _windows_command(command: list[str]) -> list[str]:
    task_command = subprocess.list2cmdline(command)
    return [
        "schtasks",
        "/Create",
        "/TN",
        TASK_NAME,
        "/SC",
        "WEEKLY",
        "/D",
        "SUN",
        "/ST",
        "09:00",
        "/TR",
        task_command,
        "/F",
    ]


def _cron_line(command: list[str]) -> str:
    return "0 9 * * 0 " + " ".join(shlex.quote(part) for part in command)


def _completed_result(system: str, command: list[str], completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "platform": system,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
