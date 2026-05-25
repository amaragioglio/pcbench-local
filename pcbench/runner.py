from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import logging
from pathlib import Path
import signal
from typing import Any

from rich.console import Console

from pcbench import __version__
from pcbench.benchmarks.cpu import run_cpu_benchmark
from pcbench.benchmarks.disk import cleanup_disk_temp_file, run_disk_benchmark
from pcbench.benchmarks.gpu import run_gpu_benchmark
from pcbench.benchmarks.memory import run_memory_benchmark
from pcbench.benchmarks.network import run_network_benchmark
from pcbench.benchmarks.system_info import collect_basic_system_info
from pcbench.logging_setup import setup_file_logger
from pcbench.reports.html_report import save_html_report
from pcbench.reports.docx_report import save_docx_report
from pcbench.reports.json_report import save_json_report
from pcbench.reports.markdown_report import save_markdown_report
from pcbench.reports.metrics import build_dashboard
from pcbench.reports.sanitize import sanitize_report
from pcbench.reports.supabase_report import save_supabase_report
from pcbench.security.audit import run_security_audit
from pcbench.terminal_ui import print_report_summary, run_step


Emit = Callable[[str], None]


def _safe_step(
    console: Console,
    logger: logging.Logger,
    title: str,
    task: Callable[[Callable[[str], None]], Any],
) -> Any:
    logger.info("step_start title=%s", title)
    try:
        result = run_step(console, title, task)
        logger.info("step_ok title=%s", title)
        return result
    except Exception as error:  # noqa: BLE001 - keep module failures isolated.
        logger.exception("step_failed title=%s error=%s", title, error)
        console.print(f"[warn]FAIL[/warn] [muted]{title}[/muted] :: {type(error).__name__}: {error}")
        return {"status": "failed", "error": f"{type(error).__name__}: {error}"}


def run_benchmarks(args: Any, console: Console) -> dict[str, Path | None]:
    logger = setup_file_logger()
    previous_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, _build_sigint_handler(logger))
    try:
        return _run_benchmarks(args, console, logger)
    except KeyboardInterrupt:
        cleanup_disk_temp_file()
        logger.warning("run_cancelled")
        console.print("[warn]CANCEL[/warn] [muted]Ejecucion cancelada. Temporales limpiados.[/muted]")
        return {"json": None, "html": None, "document": None, "markdown": None, "supabase": None}
    finally:
        signal.signal(signal.SIGINT, previous_handler)


def _run_benchmarks(args: Any, console: Console, logger: logging.Logger) -> dict[str, Path | None]:
    started_at = datetime.now().astimezone()
    profile = _profile_name(args)
    logger.info(
        "run_start profile=%s sanitize=%s reports=%s",
        profile,
        getattr(args, "sanitize", False),
        getattr(args, "reports", None),
    )
    report: dict[str, Any] = {
        "tool": "pcbench-local",
        "version": __version__,
        "started_at": started_at.isoformat(),
        "profile": profile,
        "results": {},
    }

    total_steps = (
        1
        + int(not args.skip_ram)
        + int(not args.skip_cpu)
        + int(not args.skip_disk)
        + int(not args.skip_network)
        + int(not args.skip_gpu)
        + int(not args.skip_security)
    )
    step = 1

    system_info = _safe_step(
        console,
        logger,
        f"[{step}/{total_steps}] SYSINFO // fingerprint local",
        lambda emit: _with_events(emit, logger, ["Consultando OS, CPU, RAM, discos e IP"], collect_basic_system_info),
    )
    report["results"]["system_info"] = system_info

    memory_benchmark = None
    if not args.skip_ram:
        step += 1
        memory_benchmark = _safe_step(
            console,
            logger,
            f"[{step}/{total_steps}] RAM // asignacion y ancho de banda",
            lambda emit: _with_events(
                emit,
                logger,
                ["Calculando limite seguro", "Ejecutando asignacion progresiva", "Midiendo lectura/escritura"],
                lambda: run_memory_benchmark(args.ram_mib),
            ),
        )
        report["results"]["memory_benchmark"] = memory_benchmark

    cpu_benchmark = None
    if not args.skip_cpu:
        step += 1
        cpu_benchmark = _safe_step(
            console,
            logger,
            f"[{step}/{total_steps}] CPU // single-core + multi-core",
            lambda emit: _with_events(
                emit,
                logger,
                [f"Preparando carga de {args.cpu_seconds}s", "Ejecutando single-core", "Ejecutando multi-core"],
                lambda: run_cpu_benchmark(args.cpu_seconds),
            ),
        )
        report["results"]["cpu_benchmark"] = cpu_benchmark

    disk_benchmark = None
    if not args.skip_disk:
        step += 1
        disk_benchmark = _safe_step(
            console,
            logger,
            f"[{step}/{total_steps}] DISK // lectura escritura latencia",
            lambda emit: _with_events(
                emit,
                logger,
                [f"Creando archivo temporal de {args.disk_mib} MiB", "Midiendo escritura", "Midiendo lectura", "Limpiando temporal"],
                lambda: run_disk_benchmark(args.disk_mib),
            ),
        )
        report["results"]["disk_benchmark"] = disk_benchmark

    network_benchmark = None
    if not args.skip_network:
        step += 1
        network_benchmark = _safe_step(
            console,
            logger,
            f"[{step}/{total_steps}] NET // ping dns tcp",
            lambda emit: _with_events(
                emit,
                logger,
                [f"Ping a {args.ping_host}", f"Resolviendo DNS {args.dns_host}", "Probando conexion TCP"],
                lambda: run_network_benchmark(args.ping_host, args.dns_host, args.speedtest),
            ),
        )
        report["results"]["network_benchmark"] = network_benchmark

    gpu_benchmark = None
    if not args.skip_gpu:
        step += 1
        gpu_benchmark = _safe_step(
            console,
            logger,
            f"[{step}/{total_steps}] GPU // driver vram sensores",
            lambda emit: _with_events(
                emit,
                logger,
                ["Consultando WMI", "Consultando GPUtil", "Consultando nvidia-smi si existe"],
                run_gpu_benchmark,
            ),
        )
        report["results"]["gpu_benchmark"] = gpu_benchmark

    security_audit = None
    if not args.skip_security:
        step += 1
        security_audit = _safe_step(
            console,
            logger,
            f"[{step}/{total_steps}] SEC // auditoria local",
            lambda emit: _with_events(
                emit,
                logger,
                ["Detectando plataforma", "Consultando firewall/seguridad", "Enumerando puertos y conexiones", "Revisando usuarios y servicios"],
                run_security_audit,
            ),
        )
        report["results"]["security_audit"] = security_audit

    report["finished_at"] = datetime.now().astimezone().isoformat()
    report["dashboard"] = build_dashboard(report)

    json_path = None
    html_path = None
    document_path = None
    markdown_path = None
    supabase_path = None
    if not args.no_save:
        report_to_save = sanitize_report(report) if getattr(args, "sanitize", False) else report
        selected_reports = _selected_reports(args)
        if "json" in selected_reports:
            json_path = save_json_report(report_to_save)
            logger.info("artifact_json path=%s", json_path)
        if "html" in selected_reports:
            html_path = save_html_report(report_to_save, json_path)
            logger.info("artifact_html path=%s", html_path)
        if "docx" in selected_reports:
            document_path = save_docx_report(report_to_save)
            logger.info("artifact_docx path=%s", document_path)
        if "md" in selected_reports:
            markdown_path = save_markdown_report(report_to_save)
            logger.info("artifact_markdown path=%s", markdown_path)
        if "supabase" in selected_reports:
            supabase_path = save_supabase_report(report_to_save)
            logger.info("artifact_supabase path=%s", supabase_path)

    print_report_summary(
        console,
        _live_or_none(system_info),
        _live_or_none(memory_benchmark),
        _live_or_none(cpu_benchmark),
        _live_or_none(disk_benchmark),
        _live_or_none(network_benchmark),
        _live_or_none(gpu_benchmark),
        _live_or_none(security_audit),
        json_path,
        html_path,
        document_path,
        markdown_path,
        supabase_path,
    )
    logger.info("run_finish profile=%s", report["profile"])
    return {"json": json_path, "html": html_path, "document": document_path, "markdown": markdown_path, "supabase": supabase_path}


def _with_events(emit: Emit, logger: logging.Logger, messages: list[str], task: Callable[[], Any]) -> Any:
    for message in messages:
        logger.info("event message=%s", message)
        emit(message)
    return task()


def _build_sigint_handler(logger: logging.Logger) -> Callable[[int, Any], None]:
    def handler(signum: int, frame: Any) -> None:
        cleanup_disk_temp_file()
        logger.warning("sigint_received signum=%s", signum)
        raise KeyboardInterrupt

    return handler


def _profile_name(args: Any) -> str:
    if getattr(args, "quick", False):
        return "quick"
    if getattr(args, "full", False):
        return "full"
    return "normal"


def _selected_reports(args: Any) -> set[str]:
    raw = getattr(args, "reports", None) or "json,html,docx,md"
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _live_or_none(data: Any) -> Any:
    if isinstance(data, dict) and data.get("status") == "failed":
        return None
    return data
