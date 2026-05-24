from __future__ import annotations

from typing import Any


MetricRow = dict[str, Any]


def build_dashboard(report: dict[str, Any]) -> dict[str, Any]:
    results = report.get("results", {})
    rows = [
        _cpu_score(results.get("cpu_benchmark")),
        _ram_score(results.get("memory_benchmark")),
        _disk_score(results.get("disk_benchmark")),
        _network_score(results.get("network_benchmark")),
        _gpu_score(results.get("gpu_benchmark")),
        _security_score(results.get("security_audit")),
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
    score = _average(_cap(read, 1000), _cap(write, 5000), allocation)
    return _row("RAM", score, f"{write} MiB/s write | {read} MiB/s read")


def _disk_score(data: dict | None) -> MetricRow | None:
    if not data:
        return None
    read = _num(data, "read", "mib_per_second")
    write = _num(data, "write", "mib_per_second")
    latency = _num(data, "latency", "average_ms")
    score = _average(_cap(read, 3500), _cap(write, 2000), _inverse_cap(latency, 5))
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
    return _row("GPU", score, f"{detected} GPU(s) detectadas; sensores no disponibles")


def _security_score(data: dict | None) -> MetricRow | None:
    if not data:
        return None
    summary = data.get("summary", {})
    warnings = summary.get("warning", 0)
    score = max(0, 100 - warnings * 25)
    return _row("SEC", score, f"{summary.get('ok', 0)} ok | {warnings} warnings | {summary.get('info', 0)} info")


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
