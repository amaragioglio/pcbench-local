from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

from rich.console import Console
from rich.theme import Theme
from pcbench.reports.metrics import score_bar


T = TypeVar("T")


HACKER_THEME = Theme(
    {
        "accent": "bright_green",
        "muted": "green3",
        "danger": "red",
        "warn": "yellow",
        "ok": "bright_green",
        "label": "green",
        "value": "white",
        "dim": "grey50",
    }
)


def build_console() -> Console:
    return Console(theme=HACKER_THEME)


def print_header(console: Console, version: str) -> None:
    console.print()
    console.print("[accent]PCBENCH LOCAL[/accent] [muted]//[/muted] [value]terminal hardware intelligence[/value]")
    console.print(f"[muted]version {version} | local benchmark | security audit | report engine[/muted]")
    _line(console)


def run_step(console: Console, title: str, task: Callable[[Callable[[str], None]], T]) -> T:
    console.print()
    console.print(f"[accent]:: {title}[/accent]")
    emit = _build_emit(console)
    emit("Starting module")
    result = task(emit)
    emit("Module completed")
    console.print(f"[ok]OK[/ok] [muted]{title}[/muted]")
    return result


def print_report_summary(
    console: Console,
    system_info: dict | None,
    memory_benchmark: dict | None,
    cpu_benchmark: dict | None,
    disk_benchmark: dict | None,
    network_benchmark: dict | None,
    gpu_benchmark: dict | None,
    security_audit: dict | None,
    report_path: Path | None,
    html_path: Path | None = None,
    document_path: Path | None = None,
    markdown_path: Path | None = None,
    supabase_path: Path | None = None,
) -> None:
    console.print()
    _print_dashboard(console, {
        "results": {
            "memory_benchmark": memory_benchmark,
            "cpu_benchmark": cpu_benchmark,
            "disk_benchmark": disk_benchmark,
            "network_benchmark": network_benchmark,
            "gpu_benchmark": gpu_benchmark,
            "security_audit": security_audit,
        }
    })

    _section(console, "SUMMARY")

    if system_info:
        machine = system_info["machine"]
        cpu = system_info["cpu"]
        ram = system_info["ram"]
        _kv(console, "System", f"{machine['system']} {machine['release']} ({machine['architecture']})")
        _kv(console, "CPU", f"{cpu['brand']} | {cpu['physical_cores']} cores / {cpu['logical_threads']} threads")
        _kv(console, "RAM", f"{ram['total_gib']} GiB total | {ram['available_gib']} GiB available")
        _kv(console, "Disks", len(system_info["disks"]))
        _kv(console, "Local IP", system_info["network"]["local_ip"] or "Not detected")
    else:
        _metric(console, "System", "SYSINFO failed", "warn")

    if memory_benchmark:
        console.print()
        console.print("[accent]RAM[/accent]")
        bandwidth = memory_benchmark["bandwidth"]
        allocation = memory_benchmark["allocation"]
        _metric(console, "Allocation", allocation["status"], "ok" if allocation["status"] == "passed" else "warn")
        _bar_metric(console, "Read", bandwidth["read_mib_per_second"], "MiB/s", 15000)
        _bar_metric(console, "Write", bandwidth["write_mib_per_second"], "MiB/s", 10000)
        _kv(console, "Largest OK block", f"{allocation['largest_successful_mib']} MiB")

    if cpu_benchmark:
        console.print()
        console.print("[accent]CPU[/accent]")
        score = cpu_benchmark["score"]
        _bar_metric(console, "Single-core", score["single_core"], "pts", 8000)
        _bar_metric(console, "Multi-core", score["multi_core"], "pts", 30000)
        _bar_metric(console, "Scaling", score["scaling_factor"], "x", max(score["scaling_factor"] or 1, 12))
        _kv(console, "Workers", cpu_benchmark["multi_core"]["workers"])

    if disk_benchmark:
        console.print()
        console.print("[accent]DISK[/accent]")
        _bar_metric(console, "Read", disk_benchmark["read"]["mib_per_second"], "MiB/s", 3500)
        _bar_metric(console, "Write", disk_benchmark["write"]["mib_per_second"], "MiB/s", 2000)
        _bar_metric(console, "Latency", disk_benchmark["latency"]["average_ms"], "ms", 5, lower_is_better=True)

    if network_benchmark:
        console.print()
        console.print("[accent]NETWORK[/accent]")
        ping = network_benchmark["ping"]
        _bar_metric(console, "Ping", ping.get("average_ms"), "ms", 100, lower_is_better=True)
        _bar_metric(console, "Jitter", ping.get("jitter_ms"), "ms", 30, lower_is_better=True)
        _metric(console, "Packet loss", _format_optional_percent(ping.get("packet_loss_percent")))
        _metric(console, "DNS", _format_dns(network_benchmark["dns"]))

    if gpu_benchmark:
        console.print()
        console.print("[accent]GPU[/accent]")
        nvidia = gpu_benchmark.get("nvidia_smi", {})
        wmi_gpus = [gpu for gpu in gpu_benchmark.get("wmi", []) if gpu.get("name")]
        if wmi_gpus:
            _kv(console, "Detected", ", ".join(gpu["name"] for gpu in wmi_gpus))
        if nvidia.get("status") == "passed" and nvidia.get("gpus"):
            primary = nvidia["gpus"][0]
            _bar_metric(console, "Usage", primary.get("utilization_percent"), "%", 100)
            _bar_metric(console, "VRAM", primary.get("memory_used_mib"), "MiB", primary.get("memory_total_mib") or 1)
            _bar_metric(console, "Temperature", primary.get("temperature_c"), "C", 95, lower_is_better=True)
        else:
            _metric(console, "NVIDIA SMI", "Unavailable", "warn")

    if security_audit:
        console.print()
        console.print("[accent]SECURITY[/accent]")
        summary = security_audit["summary"]
        if security_audit.get("partial"):
            _metric(console, "Scope", "partial: run as admin/root for more detail", "warn")
        _bar_metric(console, "Warnings", summary["warning"], "", max(summary["warning"], 5), lower_is_better=True)
        _kv(console, "Listening ports", len(security_audit["listening_ports"]))
        _kv(console, "Active connections", security_audit["active_connections"]["established_count"])
        if security_audit.get("platform"):
            _kv(console, "Audit platform", security_audit["platform"])
        if security_audit.get("privileges"):
            _kv(console, "Privileges", security_audit["privileges"].get("scope", "unknown"))
        if "local_admins" in security_audit:
            local_admins = security_audit["local_admins"].get("data") or []
            _kv(console, "Local admins", len(local_admins))
        if "sudo_users" in security_audit:
            _kv(console, "Sudo users", security_audit["sudo_users"].get("count", 0))
        if "services" in security_audit:
            _kv(console, "Services", security_audit["services"].get("active_count") or "Unavailable")
        for finding in security_audit["findings"][:5]:
            style = "ok" if finding["severity"] == "ok" else "warn" if finding["severity"] == "warning" else "muted"
            _metric(console, finding["area"], f"{finding['severity']}: {finding['message']}", style)

    console.print()
    _section(console, "ARTIFACTS")
    if report_path:
        _kv(console, "JSON", report_path)
    if html_path:
        _kv(console, "HTML", html_path)
    if document_path:
        _kv(console, "Document", document_path)
    if markdown_path:
        _kv(console, "Markdown", markdown_path)
    if supabase_path:
        _kv(console, "Supabase JSON", supabase_path)


def print_comparison(console: Console, comparison: dict) -> None:
    if comparison.get("status") != "passed":
        console.print(f"[warn]{comparison.get('error', 'Could not compare reports.')}[/warn]")
        return

    console.print()
    _section(console, "COMPARISON")
    for row in comparison["rows"]:
        before = row["before"]
        after = row["after"]
        if row["delta"] is None:
            _metric(console, row["metric"], "no data", "muted")
            continue
        percent = "" if row["percent"] is None else f" / {row['percent']}%"
        style = "ok" if row["result"] == "better" else "warn" if row["result"] == "worse" else "muted"
        _metric(console, row["metric"], f"{before} -> {after} | delta {row['delta']}{percent} | {row['result']}", style)

    console.print()
    _kv(console, "Base", comparison["base_path"])
    _kv(console, "Current", comparison["current_path"])
    if comparison.get("profile_warning"):
        console.print("[warn]WARN[/warn] Compared reports use different profiles.")


def _print_dashboard(console: Console, report: dict[str, Any]) -> None:
    from pcbench.reports.metrics import build_dashboard

    dashboard = build_dashboard(report)
    _section(console, "DASHBOARD")
    _kv(console, "Overall score", f"{dashboard['overall_score']} / 100 [{dashboard['overall_status']}]")
    for row in dashboard["rows"]:
        style = "ok" if row["status"] in {"GOOD", "OK"} else "warn" if row["status"] == "WARN" else "danger"
        console.print(
            f"  [label]{row['area']:<8}[/label] [{style}]{score_bar(row['score'], 18)}[/{style}] "
            f"[value]{row['score']:>5}[/value] [muted]{row['status']:<5}[/muted] {row['detail']}"
        )


def _build_emit(console: Console) -> Callable[[str], None]:
    def emit(message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(f"[dim]{timestamp}[/dim] [accent]>>[/accent] {message}")

    return emit


def _kv(console: Console, label: str, value: Any) -> None:
    console.print(f"[label]{label:<18}[/label] [muted]::[/muted] [value]{value}[/value]")


def _metric(console: Console, label: str, value: Any, style: str = "value") -> None:
    console.print(f"  [label]{label:<16}[/label] [muted]--[/muted] [{style}]{value}[/{style}]")


def _bar_metric(
    console: Console,
    label: str,
    value: float | int | None,
    unit: str,
    max_value: float | int,
    *,
    lower_is_better: bool = False,
) -> None:
    if value is None:
        _metric(console, label, "Not detected", "warn")
        return

    ratio = min(1.0, max(0.0, float(value) / float(max_value))) if max_value else 0.0
    display_ratio = 1.0 - ratio if lower_is_better else ratio
    filled = round(display_ratio * 24)
    bar = "#" * filled + "-" * (24 - filled)
    style = "ok" if display_ratio >= 0.66 else "warn" if display_ratio >= 0.33 else "danger"
    suffix = f" {unit}" if unit else ""
    console.print(f"  [label]{label:<16}[/label] [{style}]{bar}[/{style}] [value]{value}{suffix}[/value]")


def _section(console: Console, title: str) -> None:
    console.print(f"[muted]----[/muted] [accent]{title}[/accent] [muted]{'-' * max(4, 60 - len(title))}[/muted]")


def _line(console: Console) -> None:
    console.print(f"[muted]{'-' * 72}[/muted]")


def _format_dns(dns: dict) -> str:
    if dns.get("status") != "passed":
        return f"failed {dns.get('host')}"
    return f"{dns['elapsed_ms']} ms | {len(dns['addresses'])} IPs"


def _format_optional_percent(value: float | None) -> str:
    return "Not detected" if value is None else f"{value}%"
