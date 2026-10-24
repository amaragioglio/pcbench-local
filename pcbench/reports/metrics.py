from __future__ import annotations

from typing import Any


MetricRow = dict[str, Any]


def build_dashboard(report: dict[str, Any]) -> dict[str, Any]:
    results = report.get("results", {})

    def _live(key: str) -> dict | None:
        data = results.get(key)
        if isinstance(data, dict) and data.get("status") == "failed":
            return None
        return data

    rows = [
        _cpu_score(_live("cpu_benchmark")),
        _ram_score(_live("memory_benchmark")),
        _disk_score(_live("disk_benchmark")),
        _network_score(_live("network_benchmark")),
        _gpu_score(_live("gpu_benchmark")),
        _security_score(_live("security_audit")),
    ]
    rows = [row for row in rows if row is not None]
    overall = round(sum(row["score"] for row in rows) / len(rows), 1) if rows else None
    return {
        "overall_score": overall,
        "overall_status": status_from_score(overall),
        "rows": rows,
    }


def status_from_score(score: float | int | None) -> str:
    if score is None:
        return "N/A"
    if score >= 85:
        return "GOOD"
    if score >= 65:
        return "OK"
    if score >= 40:
        return "WARN"
    return "LOW"


def score_bar(score: float | int | None, width: int = 24) -> str:
    if score is None:
        return "-" * width
    filled = round(max(0, min(100, float(score))) / 100 * width)
    return "#" * filled + "-" * (width - filled)


def _cpu_score(data: dict | None) -> MetricRow | None:
    if not data:
        return None
    multi = _num(data, "score", "multi_core")
    single = _num(data, "score", "single_core")
    scaling = _num(data, "score", "scaling_factor")
    score = _average(
        _cap(multi, 30000),
        _cap(single, 8000),
        _cap(scaling, 8),
    )
    return _row("CPU", score, f"{multi} multi pts | {single} single pts")


def _ram_score(data: dict | None) -> MetricRow | None:
    if not data:
        return None
    read = _num(data, "bandwidth", "read_mib_per_second")
    write = _num(data, "bandwidth", "write_mib_per_second")
    allocation = 100 if data.get("allocation", {}).get("status") == "passed" else 30
    if (data.get("bandwidth") or {}).get("method_version", 1) >= 2:
        # Real memory bandwidth (memcpy/memchr). References: ~15 GiB/s read and
        # ~10 GiB/s write single-threaded on a current desktop.
        score = _average(_cap(read, 15000), _cap(write, 10000), allocation)
    else:  # reports from 0.3.x measured the Python interpreter, not RAM
        score = _average(_cap(read, 1000), _cap(write, 5000), allocation)
    return _row("RAM", score, f"{write} MiB/s write | {read} MiB/s read")


def _disk_score(data: dict | None) -> MetricRow | None:
    if not data:
        return None
    read = _num(data, "read", "mib_per_second")
    write = _num(data, "write", "mib_per_second")
    latency = _num(data, "latency", "average_ms")
    # A read served from the OS cache measures RAM, not the disk: leave it out.
    trusted_read = read if (data.get("read") or {}).get("cache_bypassed", False) else None
    score = _average(_cap(trusted_read, 3500), _cap(write, 2000), _inverse_cap(latency, 5))
    return _row("DISK", score, f"{write} MiB/s write | {read} MiB/s read | {latency} ms")


def _network_score(data: dict | None) -> MetricRow | None:
    if not data:
        return None
    ping = _num(data, "ping", "average_ms")
    jitter = _num(data, "ping", "jitter_ms")
    packet_loss = _num(data, "ping", "packet_loss_percent") or 0
    score = _average(_inverse_cap(ping, 100), _inverse_cap(jitter, 30), _inverse_cap(packet_loss, 10))
    return _row("NET", score, f"{ping} ms ping | {jitter} ms jitter | {packet_loss}% loss")


def _gpu_score(data: dict | None) -> MetricRow | None:
    if not data:
        return None
    nvidia = data.get("nvidia_smi", {})
    if nvidia.get("status") == "passed" and nvidia.get("gpus"):
        gpu = nvidia["gpus"][0]
        temp = gpu.get("temperature_c")
        used = gpu.get("memory_used_mib") or 0
        total = gpu.get("memory_total_mib") or 1
        vram_headroom = 100 - _cap(used, total)
        score = _average(_inverse_cap(temp, 95), vram_headroom)
        detail = f"{gpu.get('name')} | {used}/{total} MiB | {temp} C"
        return _row("GPU", score, detail)
    detected = data.get("detected_count", 0)
    score = 55 if detected else 0
    return _row("GPU", score, f"{detected} GPU(s) detected; sensors unavailable")


def _security_score(data: dict | None) -> MetricRow | None:
    if not data:
        return None
    summary = data.get("summary", {})
    critical = summary.get("critical", 0)
    warnings = summary.get("warning", 0)
    # A critical issue (no antivirus, SMBv1, open RDP...) weighs more than a warning.
    score = max(0, 100 - critical * 35 - warnings * 15)
    detail = f"{critical} critical | {warnings} warnings | {summary.get('ok', 0)} ok | {summary.get('info', 0)} info"
    return _row("SEC", score, detail)


def _row(area: str, score: float, detail: str) -> MetricRow:
    score = round(score, 1)
    return {
        "area": area,
        "score": score,
        "status": status_from_score(score),
        "detail": detail,
    }


def _average(*values: float | int | None) -> float:
    present = [float(value) for value in values if value is not None]
    return sum(present) / len(present) if present else 0.0


def _cap(value: float | int | None, max_value: float | int) -> float | None:
    if value is None or not max_value:
        return None
    return max(0.0, min(100.0, (float(value) / float(max_value)) * 100))


def _inverse_cap(value: float | int | None, max_value: float | int) -> float | None:
    capped = _cap(value, max_value)
    if capped is None:
        return None
    return 100 - capped


def _num(data: dict, *path: str) -> float | None:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current if isinstance(current, (int, float)) else None
