from pcbench.reports.metrics import build_dashboard, status_from_score


def test_status_from_score() -> None:
    assert status_from_score(90) == "GOOD"
    assert status_from_score(70) == "OK"
    assert status_from_score(50) == "WARN"
    assert status_from_score(20) == "LOW"
    assert status_from_score(None) == "N/A"


def test_build_dashboard_scores_available_results() -> None:
    report = {
        "results": {
            "cpu_benchmark": {
                "score": {"single_core": 4000, "multi_core": 15000, "scaling_factor": 4},
                "multi_core": {"workers": 8},
            },
            "security_audit": {
                "summary": {"ok": 2, "warning": 0, "info": 1},
            },
        }
    }

    dashboard = build_dashboard(report)

    assert dashboard["overall_score"] is not None
    assert [row["area"] for row in dashboard["rows"]] == ["CPU", "SEC"]
