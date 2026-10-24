from pcbench.reports.html_report import _render_html


def test_render_html_includes_score_trend() -> None:
    html = _render_html(
        {
            "started_at": "start",
            "finished_at": "end",
            "dashboard": {"overall_score": 80, "overall_status": "GOOD", "rows": []},
            "results": {},
        },
        json_path=None,
        trend=[
            {"started_at": "a", "overall_score": 70, "overall_status": "OK"},
            {"started_at": "b", "overall_score": 80, "overall_status": "GOOD"},
        ],
    )

    assert "Score trend" in html
    assert "<polyline" in html
    assert "70 -&gt; 80" in html


def test_render_html_shows_only_report_file_name_and_findings() -> None:
    from pathlib import Path

    report = {
        "started_at": "2026-10-23T21:19:06.526206-05:00",
        "finished_at": "2026-10-23T21:19:14.526931-05:00",
        "dashboard": {"overall_score": 65.1, "overall_status": "OK",
                      "rows": [{"area": "CPU", "score": 44.6, "status": "WARN", "detail": "x"}]},
        "results": {"security_audit": {"summary": {"ok": 0, "warning": 1, "info": 0},
                                       "findings": [{"severity": "warning", "area": "Firewall",
                                                     "message": "nftables is not active."}],
                                       "listening_ports": [], "active_connections": {"established_count": 0}}},
    }
    page = _render_html(report, json_path=Path(r"C:\Users\andres\reports\pcbench_report_1.json"), trend=[])
    assert "andres" not in page
    assert "pcbench_report_1.json" in page
    assert "nftables is not active." in page
    assert 'class="warn"' in page
    assert "took 8 s" in page
