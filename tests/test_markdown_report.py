from pcbench.reports.markdown_report import render_markdown


def test_render_markdown_contains_dashboard() -> None:
    markdown = render_markdown(
        {
            "profile": "quick",
            "started_at": "start",
            "finished_at": "end",
            "dashboard": {
                "overall_score": 88,
                "overall_status": "GOOD",
                "rows": [{"area": "CPU", "score": 90, "status": "GOOD", "detail": "ok"}],
            },
            "results": {},
        }
    )

    assert "# PCBench Local Report" in markdown
    assert "| CPU | 90 | GOOD | ok |" in markdown
