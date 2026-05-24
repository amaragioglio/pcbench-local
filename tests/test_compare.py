import json
from pathlib import Path

from pcbench.reports.compare import compare_reports


def test_compare_reports_detects_profile_warning(tmp_path: Path) -> None:
    base = tmp_path / "base.json"
    current = tmp_path / "current.json"
    base.write_text(json.dumps(_report("quick", 100)), encoding="utf-8")
    current.write_text(json.dumps(_report("full", 120)), encoding="utf-8")

    result = compare_reports(base, current)

    assert result["status"] == "passed"
    assert result["profile_warning"] is True
    assert result["rows"][0]["result"] == "mejor"


def _report(profile: str, single_core: int) -> dict:
    return {
        "profile": profile,
        "results": {
            "cpu_benchmark": {
                "score": {
                    "single_core": single_core,
                    "multi_core": single_core * 2,
                }
            }
        },
    }
