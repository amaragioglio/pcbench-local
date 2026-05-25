from pathlib import Path

from rich.console import Console

from pcbench import runner


def test_offer_open_html_report_skips_non_interactive_console(monkeypatch, tmp_path: Path) -> None:
    opened = []
    monkeypatch.setattr(runner.webbrowser, "open", lambda url: opened.append(url))
    console = Console(file=None)
    monkeypatch.setattr(console, "is_interactive", False)

    runner._offer_open_html_report(console, tmp_path / "report.html")

    assert opened == []


def test_offer_open_html_report_opens_when_confirmed(monkeypatch, tmp_path: Path) -> None:
    opened = []
    html_path = tmp_path / "report.html"
    html_path.write_text("<html></html>", encoding="utf-8")
    console = Console(file=None)
    monkeypatch.setattr(console, "is_interactive", True)
    monkeypatch.setattr(runner.Confirm, "ask", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(runner.webbrowser, "open", lambda url: opened.append(url))

    runner._offer_open_html_report(console, html_path)

    assert opened == [html_path.resolve().as_uri()]
