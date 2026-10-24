from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pcbench.history import score_trend
from pcbench.reports.paths import ensure_reports_dir


def save_html_report(report: dict[str, Any], json_path: Path | None = None, output_dir: Path | str | None = None) -> Path:
    reports_dir = ensure_reports_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"pcbench_report_{timestamp}.html"
    path.write_text(_render_html(report, json_path, score_trend(output_dir=output_dir)), encoding="utf-8")
    return path


def _render_html(report: dict[str, Any], json_path: Path | None, trend: list[dict[str, Any]] | None = None) -> str:
    results = report.get("results", {})
    dashboard = report.get("dashboard", {})
    security = results.get("security_audit")
    cards = [
        _trend_card(trend or []),
        _card("System", _system_rows(results.get("system_info"))),
        _card("CPU", _cpu_rows(results.get("cpu_benchmark"))),
        _card("RAM", _memory_rows(results.get("memory_benchmark"))),
        _card("Disk", _disk_rows(results.get("disk_benchmark"))),
        _card("Network", _network_rows(results.get("network_benchmark"))),
        _card("GPU", _gpu_rows(results.get("gpu_benchmark"))),
        _security_card(security),
    ]
    # Only the file name: a full path can contain the user's account name.
    source = f'<span>Data: {html.escape(re.split(r"[\\/]", str(json_path))[-1])}</span>' if json_path else ""
    sanitized = '<span class="tag">sanitized</span>' if report.get("sanitized") else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PCBench Local Report</title>
  <style>
    :root {{ color-scheme: dark; --bg:#050805; --panel:#071207; --edge:#145c2b; --rule:#103d20;
             --line:#1ee66d; --muted:#7fbf8d; --text:#d8ffe1; --ok:#1ee66d; --warn:#ffd166; --fail:#ff6b6b; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text);
            font:14px/1.5 "Cascadia Mono", Consolas, "SFMono-Regular", Menlo, monospace;
            font-variant-numeric:tabular-nums; }}
    ::selection {{ background:var(--line); color:var(--bg); }}
    header {{ padding:24px 24px 20px; border-bottom:1px solid var(--rule); background:#030603; }}
    h1 {{ margin:0 0 8px; color:var(--line); font-size:22px; letter-spacing:.02em; }}
    h2 {{ margin:0 0 12px; color:var(--line); font-size:15px; letter-spacing:.04em; text-transform:uppercase; }}
    .meta {{ color:var(--muted); display:flex; flex-wrap:wrap; gap:4px 16px; overflow-wrap:anywhere; }}
    .tag {{ border:1px solid var(--edge); padding:0 6px; color:var(--text); }}
    main {{ padding:18px; display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px;
            max-width:1400px; }}
    section {{ border:1px solid var(--edge); background:var(--panel); padding:16px; min-width:0; }}
    .overview {{ grid-column:1 / -1; display:grid; grid-template-columns:minmax(160px,220px) 1fr; gap:8px 28px; align-items:start; }}
    .total {{ font-size:48px; line-height:1; color:var(--text); }}
    .total small {{ font-size:16px; color:var(--muted); }}
    .areas {{ display:grid; gap:10px; }}
    .area {{ display:grid; grid-template-columns:56px 1fr 48px 52px; gap:12px; align-items:center; }}
    .area .detail {{ grid-column:2 / -1; color:var(--muted); font-size:12px; margin-top:-6px; overflow-wrap:anywhere; }}
    .bar {{ height:6px; background:var(--rule); }}
    .bar span {{ display:block; height:100%; background:currentColor; }}
    .ok {{ color:var(--ok); }} .warn {{ color:var(--warn); }} .fail {{ color:var(--fail); }}
    .num {{ text-align:right; }}
    svg {{ width:100%; height:auto; }}
    svg line {{ stroke:var(--rule); stroke-width:1; }}
    svg polyline {{ fill:none; stroke:var(--line); stroke-width:2; }}
    svg circle {{ fill:var(--line); }}
    table {{ width:100%; border-collapse:collapse; }}
    td {{ padding:6px 0; border-bottom:1px solid var(--rule); vertical-align:top; overflow-wrap:anywhere; }}
    td:first-child {{ color:var(--muted); width:42%; padding-right:12px; }}
    ul.findings {{ list-style:none; margin:0; padding:0; }}
    ul.findings li {{ padding:6px 0; border-bottom:1px solid var(--rule); display:grid; grid-template-columns:64px 1fr; gap:10px; }}
    @media (max-width:560px) {{
      .overview {{ grid-template-columns:1fr; }}
      header {{ padding:20px 16px; }} main {{ padding:12px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>PCBench Local report</h1>
    <div class="meta">
      <span>{html.escape(_when(report))}</span>
      {source}
      {sanitized}
    </div>
  </header>
  <main>
    {_overview(dashboard)}
    {''.join(cards)}
  </main>
</body>
</html>"""


def _when(report: dict[str, Any]) -> str:
    try:
        start = datetime.fromisoformat(str(report.get("started_at")))
        end = datetime.fromisoformat(str(report.get("finished_at")))
    except (TypeError, ValueError):
        return f"Started {report.get('started_at', '')}"
    seconds = max(0, round((end - start).total_seconds()))
    return f"{start.strftime('%d %b %Y, %H:%M')} · took {seconds} s"


def _status_class(status: Any) -> str:
    value = str(status).upper()
    if value in ("OK", "PASS", "GOOD"):
        return "ok"
    if value in ("WARN", "WARNING"):
        return "warn"
    return "fail"


def _overview(data: dict | None) -> str:
    if not data:
        return ""
    status = data.get("overall_status", "")
    areas = []
    for row in data.get("rows", []):
        try:
            width = max(0.0, min(100.0, float(row["score"])))
        except (TypeError, ValueError):
            width = 0.0
        cls = _status_class(row.get("status"))
        areas.append(
            f'<div class="area"><span>{html.escape(str(row["area"]))}</span>'
            f'<div class="bar {cls}"><span style="width:{width:.0f}%"></span></div>'
            f'<span class="num">{html.escape(str(row["score"]))}</span>'
            f'<span class="{cls}">{html.escape(str(row["status"]))}</span>'
            f'<div class="detail">{html.escape(str(row.get("detail", "")))}</div></div>'
        )
    return (
        '<section class="overview"><div><h2>Overall</h2>'
        f'<div class="total">{html.escape(str(data.get("overall_score")))}<small> / 100</small></div>'
        f'<div class="{_status_class(status)}">{html.escape(str(status))}</div></div>'
        f'<div class="areas">{"".join(areas)}</div></section>'
    )


def _security_card(data: dict | None) -> str:
    if not data:
        return _card("Security", [])
    order = {"critical": 0, "fail": 0, "warning": 1, "info": 2, "ok": 3}
    findings = sorted(data.get("findings", []), key=lambda f: order.get(str(f.get("severity")).lower(), 4))
    severity_class = {"critical": "fail", "fail": "fail", "warning": "warn", "info": "", "ok": "ok"}
    items = "".join(
        f'<li><span class="{severity_class.get(str(f.get("severity")).lower(), "")}">'
        f'{html.escape(str(f.get("severity", "")).upper())}</span>'
        f'<span>{html.escape(str(f.get("area", "")))}: {html.escape(str(f.get("message", "")))}</span></li>'
        for f in findings
    )
    table = "".join(
        f"<tr><td>{html.escape(label)}</td><td>{html.escape(str(value))}</td></tr>"
        for label, value in _security_rows(data)
    )
    partial = '<p class="warn">Partial audit: run as administrator/root for full results.</p>' if data.get("partial") else ""
    return f'<section><h2>Security</h2>{partial}<ul class="findings">{items}</ul><table>{table}</table></section>'


def _card(title: str, rows: list[tuple[str, Any]]) -> str:
    if not rows:
        rows = [("Status", "Not run")]
    body = "".join(f"<tr><td>{html.escape(label)}</td><td>{html.escape(str(value))}</td></tr>" for label, value in rows)
    return f"<section><h2>{html.escape(title)}</h2><table>{body}</table></section>"


def _trend_card(rows: list[dict[str, Any]]) -> str:
    values = [row for row in rows if isinstance(row.get("overall_score"), (int, float))]
    if len(values) < 2:
        return _card("Score trend", [("Status", "Run PCBench again to see a trend")])

    width = 420
    height = 150
    padding = 24
    usable_width = width - padding * 2
    usable_height = height - padding * 2
    points = []
    for index, row in enumerate(values):
        x = padding + (usable_width * index / max(1, len(values) - 1))
        score = max(0.0, min(100.0, float(row["overall_score"])))
        y = padding + usable_height - (score / 100.0 * usable_height)
        points.append((x, y, score))

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y, _score in points)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" />' for x, y, _score in points)
    latest = values[-1]
    first = values[0]
    delta = round(float(latest["overall_score"]) - float(first["overall_score"]), 2)
    summary = html.escape(f"{first['overall_score']} -> {latest['overall_score']} ({delta:+})")
    svg = f"""
    <svg viewBox="0 0 {width} {height}" role="img" aria-label="Overall score trend">
      <line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" />
      <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" />
      <polyline points="{polyline}" />
      {dots}
    </svg>
    <p class="meta">Overall score trend: {summary}</p>
    """
    return f"<section><h2>Score trend</h2>{svg}</section>"


def _dashboard_rows(data: dict | None) -> list[tuple[str, Any]]:
    if not data:
        return []
    rows = [("General", f"{data.get('overall_score')} / 100 {data.get('overall_status')}")]
    for row in data.get("rows", []):
        rows.append((row["area"], f"{row['score']} {row['status']} | {row['detail']}"))
    return rows


def _system_rows(data: dict | None) -> list[tuple[str, Any]]:
    if not data:
        return []
    return [
        ("System", f"{data['machine']['system']} {data['machine']['release']}"),
        ("CPU", data["cpu"]["brand"]),
        ("RAM", f"{data['ram']['total_gib']} GiB"),
        ("IP", data["network"].get("local_ip") or "Not detected"),
    ]


def _memory_rows(data: dict | None) -> list[tuple[str, Any]]:
    if not data:
        return []
    return [
        ("Test size", f"{data['target_test_mib']} MiB"),
        ("Allocation", data["allocation"]["status"]),
        ("Read", f"{data['bandwidth']['read_mib_per_second']} MiB/s"),
        ("Write", f"{data['bandwidth']['write_mib_per_second']} MiB/s"),
    ]


def _cpu_rows(data: dict | None) -> list[tuple[str, Any]]:
    if not data:
        return []
    return [
        ("Single-core", data["score"]["single_core"]),
        ("Multi-core", data["score"]["multi_core"]),
        ("Scaling", f"{data['score']['scaling_factor']}x"),
        ("Workers", data["multi_core"]["workers"]),
    ]


def _disk_rows(data: dict | None) -> list[tuple[str, Any]]:
    if not data:
        return []
    return [
        ("Write", f"{data['write']['mib_per_second']} MiB/s"),
        ("Read", f"{data['read']['mib_per_second']} MiB/s"),
        ("Average latency", f"{data['latency']['average_ms']} ms"),
    ]


def _network_rows(data: dict | None) -> list[tuple[str, Any]]:
    if not data:
        return []
    ping = data["ping"]
    return [
        ("Average ping", f"{ping.get('average_ms')} ms"),
        ("Jitter", f"{ping.get('jitter_ms')} ms"),
        ("Packet loss", f"{ping.get('packet_loss_percent')}%"),
        ("DNS", f"{data['dns'].get('elapsed_ms')} ms"),
    ]


def _gpu_rows(data: dict | None) -> list[tuple[str, Any]]:
    if not data:
        return []
    nvidia = data.get("nvidia_smi", {})
    gpu = nvidia.get("gpus", [{}])[0] if nvidia.get("gpus") else {}
    return [
        ("Detected", data.get("detected_count")),
        ("NVIDIA", gpu.get("name", "Unavailable")),
        ("VRAM", f"{gpu.get('memory_used_mib')} / {gpu.get('memory_total_mib')} MiB" if gpu else "Unavailable"),
        ("Temperature", f"{gpu.get('temperature_c')} C" if gpu else "Unavailable"),
    ]


def _security_rows(data: dict | None) -> list[tuple[str, Any]]:
    if not data:
        return []
    summary = data["summary"]
    return [
        ("Summary", f"{summary['ok']} ok | {summary['warning']} warnings | {summary['info']} info"),
        ("Listening ports", len(data["listening_ports"])),
        ("Active connections", data["active_connections"]["established_count"]),
    ]
