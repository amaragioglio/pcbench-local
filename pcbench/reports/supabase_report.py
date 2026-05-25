from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pcbench.reports.paths import ensure_reports_dir


def save_supabase_report(report: dict[str, Any], output_dir: Path | str | None = None) -> Path:
    reports_dir = ensure_reports_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"pcbench_supabase_{timestamp}.json"
    path.write_text(json.dumps(render_supabase_payload(report), indent=2, ensure_ascii=True), encoding="utf-8")
    return path


def render_supabase_payload(report: dict[str, Any]) -> dict[str, Any]:
    run_id = _run_id(report)
    dashboard = report.get("dashboard", {})
    results = report.get("results", {})
    system = results.get("system_info", {})

    return {
        "pcbench_runs": [
            {
                "run_id": run_id,
                "tool": report.get("tool"),
                "version": report.get("version"),
                "profile": report.get("profile"),
                "started_at": report.get("started_at"),
                "finished_at": report.get("finished_at"),
                "overall_score": dashboard.get("overall_score"),
                "overall_status": dashboard.get("overall_status"),
                "hostname": system.get("machine", {}).get("hostname"),
                "os": system.get("machine", {}).get("os"),
                "cpu_brand": system.get("cpu", {}).get("brand"),
                "ram_total_gib": system.get("ram", {}).get("total_gib"),
            }
        ],
        "pcbench_metrics": _metric_rows(run_id, dashboard),
        "pcbench_findings": _finding_rows(run_id, results.get("security_audit")),
    }


def _metric_rows(run_id: str, dashboard: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in dashboard.get("rows", []):
        rows.append(
            {
                "run_id": run_id,
                "area": row.get("area"),
                "score": row.get("score"),
                "status": row.get("status"),
                "detail": row.get("detail"),
            }
        )
    return rows


def _finding_rows(run_id: str, security: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not security:
        return []
    return [
        {
            "run_id": run_id,
            "severity": finding.get("severity"),
            "area": finding.get("area"),
            "message": finding.get("message"),
        }
        for finding in security.get("findings", [])
    ]


def _run_id(report: dict[str, Any]) -> str:
    raw = f"{report.get('started_at', '')}-{report.get('profile', 'normal')}"
    return raw.replace(":", "").replace(".", "").replace("+", "_")
