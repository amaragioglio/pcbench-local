import re
from pathlib import Path

from pcbench.gui.i18n import STRINGS, t
from pcbench.gui.view_model import build_view


def _report(findings, rows=None, disks=None, ram_used=40):
    return {
        "finished_at": "2026-10-23T21:23:00-05:00",
        "results": {
            "security_audit": {"partial": False, "findings": findings},
            "system_info": {"ram": {"used_percent": ram_used}, "disks": disks or []},
        },
        "dashboard": {"rows": rows or []},
    }


def _lines(view, tab="security"):
    return [line for group in view[tab] for line in group["lines"]]


def test_empty_view_before_first_scan() -> None:
    assert build_view(None, None, "es") == {"state": "empty"}


def test_critical_finding_drives_verdict_and_sorts_first() -> None:
    view = build_view(_report([
        {"id": "av_ok", "severity": "ok", "area": "Antivirus", "message": "Active: Windows Defender."},
        {"id": "rdp_no_nla", "severity": "critical", "area": "Remote access", "message": "x"},
    ]), None, "es")
    assert view["verdict"]["level"] == "critical"
    assert view["tally"] == {"red": 1, "amber": 0, "green": 1}
    assert view["security"][0]["lines"][0]["id"] == "rdp_no_nla"
    assert view["security"][0]["lines"][0]["fix"]


def test_notes_are_unlit_and_not_counted() -> None:
    view = build_view(_report([{"id": "reboot_pending", "severity": "info", "area": "Updates", "message": ""}]), None, "es")
    line = _lines(view)[0]
    assert line["light"] == "note"
    assert view["verdict"]["level"] == "ok"
    assert view["tally"] == {"red": 0, "amber": 0, "green": 0}


def test_fixed_since_last_scan_stays_on_the_sheet() -> None:
    previous = _report([{"id": "firewall_off", "severity": "critical", "area": "Firewall", "message": ""}])
    view = build_view(_report([{"id": "firewall_ok", "severity": "ok", "area": "Firewall", "message": ""}]), previous, "es")
    resolved = [line for line in _lines(view) if line["resolved"]]
    assert [line["id"] for line in resolved] == ["resolved_firewall_off"]
    assert view["tally"]["green"] == 1  # resolved lines are not double counted


def test_spanish_view_has_no_english_technical_detail() -> None:
    view = build_view(_report([
        {"id": "rdp_no_nla", "severity": "critical", "area": "Remote access",
         "message": "Remote Desktop is enabled without Network Level Authentication."},
        {"id": "updates_old", "severity": "warning", "area": "Updates", "message": "Last update installed 64 days ago."},
    ]), None, "es")
    details = {line["id"]: line["detail"] for line in _lines(view)}
    assert details["rdp_no_nla"] == ""
    assert details["updates_old"] == "Última actualización hace 64 días"


def test_performance_lines_in_plain_language() -> None:
    rows = [{"area": "CPU", "score": 45, "status": "WARN"}, {"area": "RAM", "score": 80, "status": "OK"},
            {"area": "SEC", "score": 100, "status": "GOOD"}]
    disks = [{"mountpoint": "/", "total_gib": 500, "free_gib": 20, "used_percent": 96}]
    view = build_view(_report([], rows=rows, disks=disks, ram_used=92), None, "en")
    lines = {line["id"]: line for line in view["performance"][0]["lines"]}
    assert lines["perf_score"]["value"] == "62/100"  # security excluded from performance
    assert lines["cpu"]["title"] == "Processor is tight for heavy programs"
    assert lines["space"]["light"] == "red"
    assert lines["ram_full"]["light"] == "amber"
    assert view["performance_attention"] == 3


def test_spanish_and_english_have_the_same_keys() -> None:
    assert set(STRINGS["es"]) == set(STRINGS["en"])


def test_every_key_used_by_the_window_exists() -> None:
    web = Path(__file__).resolve().parents[1] / "pcbench" / "gui" / "web"
    used = set(re.findall(r'data-t="([a-z_]+)"', (web / "index.html").read_text(encoding="utf-8")))
    used |= set(re.findall(r'\bt\("([a-z_]+)"', (web / "app.js").read_text(encoding="utf-8")))
    used |= set(re.findall(r'key: "([a-z_]+)"', (web / "app.js").read_text(encoding="utf-8")))
    missing = {key for key in used if key not in STRINGS["es"]}
    assert not missing, missing


def test_translation_formats_values() -> None:
    assert t("es", "step_of", i=2, n=7, name="Seguridad") == "Paso 2 de 7: Seguridad"


def test_window_bridge_runs_a_scan_without_a_console(monkeypatch, tmp_path) -> None:
    import time

    from pcbench.gui import app as gui_app

    fake = {"results": {"security_audit": {"findings": []}, "system_info": {}}, "dashboard": {"rows": []},
            "finished_at": "2026-10-23T21:23:00-05:00"}

    def fake_scan(progress):
        progress(1, 2, "security")
        progress(2, 2, "done")
        return fake

    monkeypatch.setattr(gui_app, "run_scan", fake_scan)
    monkeypatch.setattr(gui_app, "save_run_to_history", lambda report: None)
    monkeypatch.setattr(gui_app, "save_json_report", lambda report: None)
    monkeypatch.setattr(gui_app, "latest_saved_report", lambda: None)
    api = gui_app.Api()
    assert api.init()["strings"]["es"]["run"] == "Revisar mi PC"
    api.start_scan()
    for _ in range(50):
        if api.status()["progress"]["phase"] == "done":
            break
        time.sleep(0.02)
    assert api.status()["view"]["verdict"]["level"] == "ok"
