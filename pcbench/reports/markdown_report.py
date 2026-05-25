from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pcbench.reports.paths import ensure_reports_dir


def save_markdown_report(report: dict[str, Any], output_dir: Path | str | None = None) -> Path:
    reports_dir = ensure_reports_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"pcbench_report_{timestamp}.md"
    path.write_text(render_markdown(report), encoding="utf-8")
    return path


def render_markdown(report: dict[str, Any]) -> str:
    dashboard = report.get("dashboard", {})
    lines = [
        "# PCBench Local Report",
        "",
        f"- Profile: `{report.get('profile', 'normal')}`",
        f"- Started: `{report.get('started_at', '')}`",
        f"- Finished: `{report.get('finished_at', '')}`",
        f"- Overall: `{dashboard.get('overall_score', 'N/A')}` `{dashboard.get('overall_status', 'N/A')}`",
        "",
        "## Dashboard",
        "",
        "| Area | Score | Status | Detail |",
        "| --- | ---: | --- | --- |",
    ]
    for row in dashboard.get("rows", []):
        lines.append(f"| {row['area']} | {row['score']} | {row['status']} | {row['detail']} |")

    results = report.get("results", {})
    system = results.get("system_info")
    if system:
        lines.extend(
            [
                "",
                "## System",
                "",
                f"- OS: `{system['machine']['system']} {system['machine']['release']}`",
                f"- CPU: `{system['cpu']['brand']}`",
                f"- RAM: `{system['ram']['total_gib']} GiB`",
                f"- Local IP: `{system['network'].get('local_ip') or 'Not detected'}`",
            ]
        )

    security = results.get("security_audit")
    if security:
        lines.extend(["", "## Security Findings", ""])
        for finding in security.get("findings", []):
            lines.append(f"- `{finding['severity']}` **{finding['area']}**: {finding['message']}")

    lines.append("")
    return "\n".join(lines)
