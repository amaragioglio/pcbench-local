from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

from pcbench import __version__
from pcbench.benchmarks.cpu import run_cpu_benchmark
from pcbench.benchmarks.disk import run_disk_benchmark
from pcbench.benchmarks.gpu import run_gpu_benchmark
from pcbench.benchmarks.memory import run_memory_benchmark
from pcbench.benchmarks.network import run_network_benchmark
from pcbench.benchmarks.system_info import collect_basic_system_info
from pcbench.reports.html_report import save_html_report
from pcbench.reports.docx_report import save_docx_report
from pcbench.reports.json_report import save_json_report
from pcbench.reports.markdown_report import save_markdown_report
from pcbench.reports.metrics import build_dashboard
from pcbench.reports.supabase_report import save_supabase_report
from pcbench.security.audit import run_security_audit
from pcbench.terminal_ui import print_report_summary, run_step


Emit = Callable[[str], None]


def run_benchmarks(args: Any, console: Console) -> dict[str, Path | None]:
    started_at = datetime.now().astimezone()
    report: dict[str, Any] = {
        "tool": "pcbench-local",
        "version": __version__,
        "started_at": started_at.isoformat(),
        "profile": _profile_name(args),
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

    system_info = run_step(
        console,
        f"[{step}/{total_steps}] SYSINFO // fingerprint local",
        lambda emit: _with_events(emit, ["Consultando OS, CPU, RAM, discos e IP"], collect_basic_system_info),
    )
    report["results"]["system_info"] = system_info

    memory_benchmark = None
    if not args.skip_ram:
        step += 1
        memory_benchmark = run_step(
            console,
            f"[{step}/{total_steps}] RAM // asignacion y ancho de banda",
            lambda emit: _with_events(
                emit,
                ["Calculando limite seguro", "Ejecutando asignacion progresiva", "Midiendo lectura/escritura"],
                lambda: run_memory_benchmark(args.ram_mib),
            ),
        )
        report["results"]["memory_benchmark"] = memory_benchmark

    cpu_benchmark = None
    if not args.skip_cpu:
        step += 1
        cpu_benchmark = run_step(
            console,
            f"[{step}/{total_steps}] CPU // single-core + multi-core",
            lambda emit: _with_events(
                emit,
                [f"Preparando carga de {args.cpu_seconds}s", "Ejecutando single-core", "Ejecutando multi-core"],
                lambda: run_cpu_benchmark(args.cpu_seconds),
            ),
        )
        report["results"]["cpu_benchmark"] = cpu_benchmark

    disk_benchmark = None
    if not args.skip_disk:
        step += 1
        disk_benchmark = run_step(
            console,
            f"[{step}/{total_steps}] DISK // lectura escritura latencia",
            lambda emit: _with_events(
                emit,
                [f"Creando archivo temporal de {args.disk_mib} MiB", "Midiendo escritura", "Midiendo lectura", "Limpiando temporal"],
                lambda: run_disk_benchmark(args.disk_mib),
            ),
        )
        report["results"]["disk_benchmark"] = disk_benchmark

    network_benchmark = None
    if not args.skip_network:
        step += 1
        network_benchmark = run_step(
            console,
            f"[{step}/{total_steps}] NET // ping dns tcp",
            lambda emit: _with_events(
                emit,
                [f"Ping a {args.ping_host}", f"Resolviendo DNS {args.dns_host}", "Probando conexion TCP"],
                lambda: run_network_benchmark(args.ping_host, args.dns_host, args.speedtest),
            ),
        )
        report["results"]["network_benchmark"] = network_benchmark

    gpu_benchmark = None
    if not args.skip_gpu:
        step += 1
        gpu_benchmark = run_step(
            console,
            f"[{step}/{total_steps}] GPU // driver vram sensores",
            lambda emit: _with_events(
                emit,
                ["Consultando WMI", "Consultando GPUtil", "Consultando nvidia-smi si existe"],
                run_gpu_benchmark,
            ),
        )
        report["results"]["gpu_benchmark"] = gpu_benchmark

    security_audit = None
    if not args.skip_security:
        step += 1
        security_audit = run_step(
            console,
            f"[{step}/{total_steps}] SEC // defender firewall puertos",
            lambda emit: _with_events(
                emit,
                ["Consultando Defender", "Consultando firewall", "Enumerando puertos y conexiones", "Revisando inicio automatico"],
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
        selected_reports = _selected_reports(args)
        if "json" in selected_reports:
            json_path = save_json_report(report)
        if "html" in selected_reports:
            html_path = save_html_report(report, json_path)
        if "docx" in selected_reports:
            document_path = save_docx_report(report)
        if "md" in selected_reports:
            markdown_path = save_markdown_report(report)
        if "supabase" in selected_reports:
            supabase_path = save_supabase_report(report)

    print_report_summary(
        console,
        system_info,
        memory_benchmark,
        cpu_benchmark,
        disk_benchmark,
        network_benchmark,
        gpu_benchmark,
        security_audit,
        json_path,
        html_path,
        document_path,
        markdown_path,
        supabase_path,
    )
    return {"json": json_path, "html": html_path, "document": document_path, "markdown": markdown_path, "supabase": supabase_path}


def _with_events(emit: Emit, messages: list[str], task: Callable[[], Any]) -> Any:
    for message in messages:
        emit(message)
    return task()


def _profile_name(args: Any) -> str:
    if getattr(args, "quick", False):
        return "quick"
    if getattr(args, "full", False):
        return "full"
    return "normal"


def _selected_reports(args: Any) -> set[str]:
    raw = getattr(args, "reports", None) or "json,html,docx,md"
    return {item.strip().lower() for item in raw.split(",") if item.strip()}
