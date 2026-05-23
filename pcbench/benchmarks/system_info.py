from __future__ import annotations

import os
import platform
import socket
from typing import Any

import psutil

try:
    import cpuinfo
except ImportError:  # pragma: no cover - dependency is listed, but keep CLI resilient.
    cpuinfo = None


BYTES_IN_GIB = 1024**3


def _gib(value: int | float) -> float:
    return round(value / BYTES_IN_GIB, 2)


def collect_basic_system_info() -> dict[str, Any]:
    memory = psutil.virtual_memory()
    boot_time = psutil.boot_time()
    cpu_details = cpuinfo.get_cpu_info() if cpuinfo else {}

    return {
        "machine": {
            "hostname": socket.gethostname(),
            "os": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "boot_time_epoch": boot_time,
        },
        "cpu": {
            "brand": cpu_details.get("brand_raw") or platform.processor() or "Unknown",
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_threads": psutil.cpu_count(logical=True),
            "current_frequency_mhz": _safe_cpu_frequency(),
        },
        "ram": {
            "total_gib": _gib(memory.total),
            "available_gib": _gib(memory.available),
            "used_percent": memory.percent,
        },
        "disks": _collect_disks(),
        "network": {
            "hostname": socket.gethostname(),
            "local_ip": _safe_local_ip(),
        },
        "process": {
            "pid": os.getpid(),
        },
    }


def _safe_cpu_frequency() -> float | None:
    frequency = psutil.cpu_freq()
    if frequency is None:
        return None
    return round(frequency.current, 2)


def _collect_disks() -> list[dict[str, Any]]:
    disks: list[dict[str, Any]] = []
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            continue

        disks.append(
            {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "filesystem": partition.fstype,
                "total_gib": _gib(usage.total),
                "free_gib": _gib(usage.free),
                "used_percent": usage.percent,
            }
        )
    return disks


def _safe_local_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None
