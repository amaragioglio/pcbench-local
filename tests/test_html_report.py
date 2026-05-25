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

    assert "Score Trend" in html
    assert "<polyline" in html
    assert "70 -&gt; 80" in html
