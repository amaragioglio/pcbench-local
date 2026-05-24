from pcbench.reports.supabase_report import render_supabase_payload


def test_render_supabase_payload_uses_flat_tables() -> None:
    payload = render_supabase_payload(
        {
            "tool": "pcbench-local",
            "version": "0.1.0",
            "profile": "quick",
            "started_at": "2026-01-01T00:00:00",
            "finished_at": "2026-01-01T00:01:00",
            "dashboard": {
                "overall_score": 90,
                "overall_status": "GOOD",
                "rows": [{"area": "CPU", "score": 90, "status": "GOOD", "detail": "ok"}],
            },
            "results": {
                "system_info": {
                    "machine": {"hostname": "host", "os": "Linux"},
                    "cpu": {"brand": "CPU"},
                    "ram": {"total_gib": 32},
                },
                "security_audit": {
                    "findings": [{"severity": "ok", "area": "Firewall", "message": "active"}]
                },
            },
        }
    )

    assert set(payload) == {"pcbench_runs", "pcbench_metrics", "pcbench_findings"}
    assert payload["pcbench_runs"][0]["overall_score"] == 90
    assert payload["pcbench_metrics"][0]["area"] == "CPU"
    assert payload["pcbench_findings"][0]["area"] == "Firewall"
