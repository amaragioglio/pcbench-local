from __future__ import annotations

import re
import socket
import statistics
import subprocess
import time
from typing import Any

import psutil


DEFAULT_PING_HOST = "1.1.1.1"
DEFAULT_DNS_HOST = "google.com"
PING_COUNT = 4


def run_network_benchmark(
    ping_host: str = DEFAULT_PING_HOST,
    dns_host: str = DEFAULT_DNS_HOST,
    include_speedtest: bool = False,
) -> dict[str, Any]:
    adapters = _collect_adapters()
    ping = _run_ping(ping_host)
    dns = _resolve_dns(dns_host)
    connectivity = _tcp_connectivity_check("1.1.1.1", 443)
    speedtest = _run_speedtest() if include_speedtest else None

    return {
        "adapters": adapters,
        "ping_host": ping_host,
        "dns_host": dns_host,
        "ping": ping,
        "dns": dns,
        "connectivity": connectivity,
        "speedtest": speedtest,
        "notes": [
            "Ping mide latencia hacia un host externo, no velocidad de descarga.",
            "Speedtest es opcional porque tarda mas y depende de internet/servidores externos.",
        ],
    }


def _collect_adapters() -> list[dict[str, Any]]:
    adapters: list[dict[str, Any]] = []
    stats = psutil.net_if_stats()
    addresses = psutil.net_if_addrs()

    for name, adapter_stats in stats.items():
        ipv4 = [
            addr.address
            for addr in addresses.get(name, [])
            if addr.family == socket.AF_INET and not addr.address.startswith("169.254.")
        ]
        adapters.append(
            {
                "name": name,
                "is_up": adapter_stats.isup,
                "speed_mbps": adapter_stats.speed,
                "mtu": adapter_stats.mtu,
                "ipv4": ipv4,
            }
        )

    return adapters


def _run_ping(host: str) -> dict[str, Any]:
    command = ["ping", "-n", str(PING_COUNT), host]
    started = time.perf_counter()

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "status": "failed",
            "error": str(error),
            "host": host,
        }

    elapsed = time.perf_counter() - started
    latencies = _extract_ping_latencies(completed.stdout)
    packet_loss = _extract_packet_loss(completed.stdout)

    return {
        "status": "passed" if completed.returncode == 0 and latencies else "failed",
        "host": host,
        "samples": len(latencies),
        "packet_loss_percent": packet_loss,
        "average_ms": round(statistics.mean(latencies), 3) if latencies else None,
        "median_ms": round(statistics.median(latencies), 3) if latencies else None,
        "min_ms": round(min(latencies), 3) if latencies else None,
        "max_ms": round(max(latencies), 3) if latencies else None,
        "jitter_ms": _jitter(latencies),
        "elapsed_seconds": round(elapsed, 3),
    }


def _extract_ping_latencies(output: str) -> list[float]:
    latencies: list[float] = []
    for match in re.finditer(r"(?:time|tiempo)[=<]?\s*(\d+(?:\.\d+)?)\s*ms", output, flags=re.IGNORECASE):
        latencies.append(float(match.group(1)))
    return latencies


def _extract_packet_loss(output: str) -> float | None:
    match = re.search(r"\((\d+(?:\.\d+)?)%\s*(?:loss|perdidos)", output, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))

    match = re.search(r"(\d+(?:\.\d+)?)%\s*(?:loss|perdidos)", output, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))

    return None


def _jitter(latencies: list[float]) -> float | None:
    if len(latencies) < 2:
        return None
    deltas = [abs(right - left) for left, right in zip(latencies, latencies[1:])]
    return round(statistics.mean(deltas), 3)


def _resolve_dns(host: str) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        addresses = sorted({info[4][0] for info in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
    except OSError as error:
        return {
            "status": "failed",
            "host": host,
            "error": str(error),
        }

    elapsed = time.perf_counter() - started
    return {
        "status": "passed",
        "host": host,
        "addresses": addresses,
        "elapsed_ms": round(elapsed * 1000, 3),
    }


def _tcp_connectivity_check(host: str, port: int) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=5):
            elapsed = time.perf_counter() - started
            return {
                "status": "passed",
                "host": host,
                "port": port,
                "elapsed_ms": round(elapsed * 1000, 3),
            }
    except OSError as error:
        return {
            "status": "failed",
            "host": host,
            "port": port,
            "error": str(error),
        }


def _run_speedtest() -> dict[str, Any]:
    try:
        import speedtest

        test = speedtest.Speedtest()
        test.get_best_server()
        download_bps = test.download()
        upload_bps = test.upload()
        result = test.results.dict()
    except Exception as error:  # speedtest can fail for network/server reasons.
        return {
            "status": "failed",
            "error": str(error),
        }

    return {
        "status": "passed",
        "download_mbps": round(download_bps / 1_000_000, 2),
        "upload_mbps": round(upload_bps / 1_000_000, 2),
        "ping_ms": round(result.get("ping", 0.0), 3),
        "server": result.get("server", {}),
    }
