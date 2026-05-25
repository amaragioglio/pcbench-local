from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pcbench.reports.paths import resolve_reports_dir


METRICS = [
    ("CPU single-core", ("results", "cpu_benchmark", "score", "single_core"), "higher"),
    ("CPU multi-core", ("results", "cpu_benchmark", "score", "multi_core"), "higher"),
    ("RAM lectura", ("results", "memory_benchmark", "bandwidth", "read_mib_per_second"), "higher"),
    ("RAM escritura", ("results", "memory_benchmark", "bandwidth", "write_mib_per_second"), "higher"),
    ("Disco lectura", ("results", "disk_benchmark", "read", "mib_per_second"), "higher"),
    ("Disco escritura", ("results", "disk_benchmark", "write", "mib_per_second"), "higher"),
    ("Disco latencia", ("results", "disk_benchmark", "latency", "average_ms"), "lower"),
    ("Ping", ("results", "network_benchmark", "ping", "average_ms"), "lower"),
    ("Seguridad warnings", ("results", "security_audit", "summary", "warning"), "lower"),
]


def latest_json_reports(limit: int = 2, profile: str | None = None, output_dir: Path | str | None = None) -> list[Path]:
    reports_dir = resolve_reports_dir(output_dir)
    reports = sorted(reports_dir.glob("pcbench_report_*.json"), key=lambda path: path.name)
    if profile:
        reports = [path for path in reports if _report_profile(path) == profile]
    return reports[-limit:]


def compare_latest_reports(profile: str | None = None, output_dir: Path | str | None = None) -> dict[str, Any]:
    paths = latest_json_reports(2, profile, output_dir)
    if len(paths) < 2:
        suffix = f" para perfil {profile}" if profile else ""
        return {"status": "failed", "error": f"Se necesitan al menos dos reportes JSON{suffix}.", "paths": paths}
    return compare_reports(paths[0], paths[1])


def compare_reports(base_path: Path, current_path: Path) -> dict[str, Any]:
    base = json.loads(base_path.read_text(encoding="utf-8"))
    current = json.loads(current_path.read_text(encoding="utf-8"))
    rows = []
    for label, path, direction in METRICS:
        before = _get(base, path)
        after = _get(current, path)
        rows.append(_compare_metric(label, before, after, direction))
    return {
        "status": "passed",
        "base_path": str(base_path),
        "current_path": str(current_path),
        "base_profile": base.get("profile"),
        "current_profile": current.get("profile"),
        "profile_warning": base.get("profile") != current.get("profile"),
        "rows": rows,
    }


def _compare_metric(label: str, before: Any, after: Any, direction: str) -> dict[str, Any]:
    if not isinstance(before, (int, float)) or not isinstance(after, (int, float)):
        return {"metric": label, "before": before, "after": after, "delta": None, "percent": None, "result": "sin datos"}
    delta = round(after - before, 3)
    percent = round((delta / before) * 100, 2) if before else None
    improved = delta > 0 if direction == "higher" else delta < 0
    result = "mejor" if improved else "peor" if delta else "igual"
    return {"metric": label, "before": before, "after": after, "delta": delta, "percent": percent, "result": result}


def _get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _report_profile(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    profile = data.get("profile")
    return profile if isinstance(profile, str) else None
