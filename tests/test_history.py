from pathlib import Path

from pcbench.history import history_db_path, latest_runs, save_run_to_history


def test_save_run_to_history_creates_queryable_rows(tmp_path: Path) -> None:
    report = {
        "tool": "pcbench-local",
        "version": "0.3.0",
        "profile": "quick",
        "started_at": "2026-05-25T00:00:00",
        "finished_at": "2026-05-25T00:01:00",
        "sanitized": True,
        "dashboard": {
            "overall_score": 88.5,
            "overall_status": "GOOD",
            "rows": [{"area": "CPU", "score": 90, "status": "GOOD", "detail": "ok"}],
        },
        "results": {
            "system_info": {
                "machine": {"hostname": "host_abc", "os": "Windows"},
                "cpu": {"brand": "CPU"},
                "ram": {"total_gib": 32},
            },
            "security_audit": {
                "findings": [{"severity": "ok", "area": "Firewall", "message": "enabled"}],
            },
        },
    }

    db_path = save_run_to_history(report, tmp_path)
    rows = latest_runs(5, tmp_path)

    assert db_path == history_db_path(tmp_path)
    assert db_path.exists()
    assert rows[0]["profile"] == "quick"
    assert rows[0]["overall_score"] == 88.5
    assert rows[0]["sanitized"] == 1


def test_latest_runs_returns_empty_without_db(tmp_path: Path) -> None:
    assert latest_runs(output_dir=tmp_path) == []
