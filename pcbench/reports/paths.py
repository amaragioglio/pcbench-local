from __future__ import annotations

import platform
from pathlib import Path


def default_reports_dir() -> Path:
    home = Path.home()
    if platform.system() == "Windows":
        return home / "Documents" / "PCBench" / "reports"
    return home / "PCBench" / "reports"


def resolve_reports_dir(output_dir: Path | str | None = None) -> Path:
    return Path(output_dir).expanduser() if output_dir else default_reports_dir()


def ensure_reports_dir(output_dir: Path | str | None = None) -> Path:
    path = resolve_reports_dir(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def prune_old_reports(output_dir: Path | str | None, keep_last: int | None) -> None:
    if keep_last is None or keep_last <= 0:
        return

    reports_dir = resolve_reports_dir(output_dir)
    if not reports_dir.exists():
        return

    patterns = ("pcbench_report_*.*", "pcbench_supabase_*.json")
    paths = sorted(
        {path for pattern in patterns for path in reports_dir.glob(pattern) if path.is_file()},
        key=lambda path: (path.stat().st_mtime, path.name),
    )
    for path in paths[:-keep_last]:
        path.unlink(missing_ok=True)
