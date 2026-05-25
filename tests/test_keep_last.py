import os
from pathlib import Path

from pcbench.reports.paths import prune_old_reports


def test_prune_old_reports_keeps_latest_files(tmp_path: Path) -> None:
    old = tmp_path / "pcbench_report_20260101_000000.json"
    middle = tmp_path / "pcbench_report_20260101_000001.html"
    latest = tmp_path / "pcbench_supabase_20260101_000002.json"
    for index, path in enumerate([old, middle, latest], start=1):
        path.write_text("{}", encoding="utf-8")
        timestamp = 1_700_000_000 + index
        os.utime(path, (timestamp, timestamp))

    prune_old_reports(tmp_path, keep_last=2)

    assert not old.exists()
    assert middle.exists()
    assert latest.exists()
