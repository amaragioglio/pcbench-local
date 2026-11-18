"""Console-free scan used by the desktop window.

Same engine as the CLI, different order: security first, because the first
question a non-technical user has is "is my PC safe?". Each step reports
progress through a callback so the window can fill its checklist live.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from pcbench import __version__
from pcbench.benchmarks.cpu import run_cpu_benchmark
from pcbench.benchmarks.disk import cleanup_disk_temp_file, run_disk_benchmark
from pcbench.benchmarks.gpu import run_gpu_benchmark
from pcbench.benchmarks.memory import run_memory_benchmark
from pcbench.benchmarks.network import DEFAULT_DNS_HOST, DEFAULT_PING_HOST, run_network_benchmark
from pcbench.benchmarks.system_info import collect_basic_system_info
from pcbench.history import save_run_to_history
from pcbench.logging_setup import setup_file_logger
from pcbench.reports.html_report import save_html_report
from pcbench.reports.json_report import save_json_report
from pcbench.reports.metrics import build_dashboard
from pcbench.reports.paths import ensure_reports_dir
from pcbench.reports.sanitize import sanitize_report
from pcbench.security.audit import run_security_audit

Progress = Callable[[int, int, str], None]

def plan_steps(include_network: bool = True) -> list[str]:
    steps = ["system", "security", "cpu", "memory", "disk"]
    if include_network:
        steps.append("network")
    steps.append("gpu")
    return steps


def run_scan(
    progress: Progress | None = None,
    include_network: bool = True,
    output_dir: Path | str | None = None,
    cpu_seconds: int = 4,
    ram_mib: int | None = 512,
    disk_mib: int = 256,
) -> dict[str, Any]:
    """Run every check and return the full report (not saved yet)."""
    logger = setup_file_logger(output_dir)
    progress = progress or (lambda *_: None)
    steps = plan_steps(include_network)
    tasks: dict[str, tuple[str, Callable[[], Any]]] = {
        "system": ("system_info", collect_basic_system_info),
        "security": ("security_audit", run_security_audit),
        "cpu": ("cpu_benchmark", lambda: run_cpu_benchmark(cpu_seconds)),
        "memory": ("memory_benchmark", lambda: run_memory_benchmark(ram_mib)),
        "disk": ("disk_benchmark", lambda: run_disk_benchmark(disk_mib)),
        "network": ("network_benchmark", lambda: run_network_benchmark(DEFAULT_PING_HOST, DEFAULT_DNS_HOST, False)),
        "gpu": ("gpu_benchmark", run_gpu_benchmark),
    }
    report: dict[str, Any] = {
        "tool": "pcbench-local",
        "version": __version__,
        "started_at": datetime.now().astimezone().isoformat(),
        "profile": "app",
        "results": {},
    }
    try:
        for index, name in enumerate(steps, start=1):
            progress(index, len(steps), name)
            key, task = tasks[name]
            report["results"][key] = _safe(task, name, logger)
    finally:
        cleanup_disk_temp_file()
    progress(len(steps), len(steps), "done")
    report["finished_at"] = datetime.now().astimezone().isoformat()
    report["dashboard"] = build_dashboard(report)
    return report


def _safe(task: Callable[[], Any], name: str, logger: logging.Logger) -> Any:
    try:
        result = task()
        logger.info("step_ok name=%s", name)
        return result
    except Exception as error:  # noqa: BLE001 - one failing module must not stop the scan
        logger.exception("step_failed name=%s", name)
        return {"status": "failed", "error": f"{type(error).__name__}: {error}"}


def latest_saved_report(output_dir: Path | str | None = None) -> dict[str, Any] | None:
    """The most recent JSON report, used to show what was fixed since then."""
    reports_dir = ensure_reports_dir(output_dir)
    candidates = sorted(reports_dir.glob("pcbench_report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    return None


def save_scan(report: dict[str, Any], output_dir: Path | str | None = None, sanitize: bool = True) -> dict[str, Path]:
    """Save JSON + HTML (and history). Sanitized by default for safe sharing."""
    to_save = sanitize_report(report) if sanitize else report
    save_run_to_history(to_save, output_dir)
    json_path = save_json_report(to_save, output_dir)
    html_path = save_html_report(to_save, json_path, output_dir)
    return {"json": json_path, "html": html_path}
