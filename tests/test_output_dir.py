import json
from pathlib import Path

from pcbench.reports.json_report import save_json_report
from pcbench.reports.paths import resolve_reports_dir


def test_save_json_report_honors_output_dir(tmp_path: Path) -> None:
    path = save_json_report({"tool": "pcbench-local"}, tmp_path)

    assert path.parent == tmp_path
    assert path.name.startswith("pcbench_report_")
    assert json.loads(path.read_text(encoding="utf-8"))["tool"] == "pcbench-local"


def test_resolve_reports_dir_expands_user_path(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert resolve_reports_dir("~/custom").is_absolute()
