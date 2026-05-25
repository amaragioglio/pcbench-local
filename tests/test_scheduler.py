import sys
from argparse import Namespace
from pathlib import Path

from pcbench import scheduler


def test_schedule_weekly_dry_run_windows(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(scheduler.platform, "system", lambda: "Windows")
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python.exe"))

    result = scheduler.schedule_weekly(Namespace(dry_run=True, output_dir=tmp_path))

    assert result["status"] == "dry_run"
    assert result["command"][0] == "schtasks"
    assert "/SC" in result["command"]


def test_schedule_weekly_dry_run_cron(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(scheduler.platform, "system", lambda: "Linux")
    monkeypatch.setattr(sys, "executable", "/usr/bin/python3")

    result = scheduler.schedule_weekly(Namespace(dry_run=True, output_dir=tmp_path))

    assert result["status"] == "dry_run"
    assert result["command"].startswith("0 9 * * 0")
    assert "--output-dir" in result["command"]
