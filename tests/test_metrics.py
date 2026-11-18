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


def test_ram_score_uses_new_scale_for_real_bandwidth() -> None:
    from pcbench.reports.metrics import _ram_score

    new = _ram_score({"allocation": {"status": "passed"},
                      "bandwidth": {"method_version": 2, "read_mib_per_second": 15000,
                                    "write_mib_per_second": 10000}})
    old = _ram_score({"allocation": {"status": "passed"},
                      "bandwidth": {"read_mib_per_second": 1000, "write_mib_per_second": 5000}})
    assert new["score"] == 100
    assert old["score"] == 100


def test_disk_score_ignores_cached_reads() -> None:
    from pcbench.reports.metrics import _disk_score

    base = {"write": {"mib_per_second": 1000}, "latency": {"average_ms": 1}}
    cached = _disk_score({**base, "read": {"mib_per_second": 9000, "cache_bypassed": False}})
    uncached = _disk_score({**base, "read": {"mib_per_second": 350, "cache_bypassed": True}})
    assert cached["score"] > uncached["score"]  # cached read is dropped, not counted as 100
    assert cached["score"] == round((50 + 80) / 2, 1)
