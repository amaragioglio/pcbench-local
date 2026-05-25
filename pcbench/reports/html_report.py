from __future__ import annotations

import html
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
    cards = [
        _card("Dashboard", _dashboard_rows(dashboard)),
        _trend_card(trend or []),
        _card("System", _system_rows(results.get("system_info"))),
        _card("RAM", _memory_rows(results.get("memory_benchmark"))),
        _card("CPU", _cpu_rows(results.get("cpu_benchmark"))),
        _card("Disk", _disk_rows(results.get("disk_benchmark"))),
        _card("Network", _network_rows(results.get("network_benchmark"))),
        _card("GPU", _gpu_rows(results.get("gpu_benchmark"))),
        _card("Security", _security_rows(results.get("security_audit"))),
    ]
    source = f"<p>JSON: {html.escape(str(json_path))}</p>" if json_path else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PCBench Local Report</title>
  <style>
    :root {{ color-scheme: dark; --bg:#050805; --panel:#071207; --line:#1ee66d; --muted:#6fae7d; --text:#d8ffe1; --warn:#ffd166; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font:14px Consolas, "Cascadia Mono", monospace; }}
    header {{ padding:24px; border-bottom:1px solid #134d25; background:#030603; }}
    h1 {{ margin:0 0 6px; color:var(--line); letter-spacing:0; font-size:28px; }}
    h2 {{ margin:0 0 12px; color:var(--line); font-size:18px; }}
    main {{ padding:18px; display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; }}
    section {{ border:1px solid #145c2b; background:var(--panel); padding:14px; }}
    svg {{ width:100%; height:auto; }}
    svg line {{ stroke:#134d25; stroke-width:1; }}
    svg polyline {{ fill:none; stroke:var(--line); stroke-width:3; }}
    svg circle {{ fill:var(--line); }}
    table {{ width:100%; border-collapse:collapse; }}
    td {{ padding:6px 0; border-bottom:1px solid #103d20; vertical-align:top; }}
    td:first-child {{ color:var(--muted); width:42%; }}
    .meta {{ color:var(--muted); }}
  </style>
</head>
<body>
  <header>
    <h1>PCBENCH LOCAL // REPORT</h1>
    <div class="meta">Started: {html.escape(str(report.get("started_at", "")))} | Finished: {html.escape(str(report.get("finished_at", "")))}</div>
    {source}
  </header>
  <main>
    {''.join(cards)}
  </main>
</body>
</html>"""


def _card(title: str, rows: list[tuple[str, Any]]) -> str:
    if not rows:
        rows = [("Status", "Not run")]
    body = "".join(f"<tr><td>{html.escape(label)}</td><td>{html.escape(str(value))}</td></tr>" for label, value in rows)
    return f"<section><h2>{html.escape(title)}</h2><table>{body}</table></section>"


def _trend_card(rows: list[dict[str, Any]]) -> str:
    values = [row for row in rows if isinstance(row.get("overall_score"), (int, float))]
    if len(values) < 2:
        return _card("Score Trend", [("Status", "Need at least two history rows")])

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
    return f"<section><h2>Score Trend</h2>{svg}</section>"


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
