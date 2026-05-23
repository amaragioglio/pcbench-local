from __future__ import annotations

import multiprocessing as mp
import time
from typing import Any

import psutil


DEFAULT_SECONDS = 5
MIN_SECONDS = 1
MAX_SECONDS = 60


def run_cpu_benchmark(duration_seconds: int = DEFAULT_SECONDS) -> dict[str, Any]:
    duration_seconds = _clamp_duration(duration_seconds)
    logical_threads = psutil.cpu_count(logical=True) or 1
    physical_cores = psutil.cpu_count(logical=False)
    frequency_before = _safe_frequency()
    usage_before = psutil.cpu_percent(interval=0.2)

    single_core = _run_single_core(duration_seconds)
    multi_core = _run_multi_core(duration_seconds, logical_threads)

    usage_after = psutil.cpu_percent(interval=0.2)
    frequency_after = _safe_frequency()

    return {
        "duration_seconds": duration_seconds,
        "physical_cores": physical_cores,
        "logical_threads": logical_threads,
        "frequency_before_mhz": frequency_before,
        "frequency_after_mhz": frequency_after,
        "cpu_usage_before_percent": usage_before,
        "cpu_usage_after_percent": usage_after,
        "single_core": single_core,
        "multi_core": multi_core,
        "score": {
            "single_core": single_core["score"],
            "multi_core": multi_core["score"],
            "scaling_factor": _safe_ratio(multi_core["score"], single_core["score"]),
        },
        "notes": [
            "Score local basado en operaciones enteras por segundo.",
            "Sirve para comparar ejecuciones en esta misma herramienta, no reemplaza Cinebench.",
        ],
    }


def _run_single_core(duration_seconds: int) -> dict[str, Any]:
    started = time.perf_counter()
    operations = _cpu_work_until(started + duration_seconds)
    elapsed = time.perf_counter() - started
    return _result(operations, elapsed)


def _run_multi_core(duration_seconds: int, workers: int) -> dict[str, Any]:
    started = time.perf_counter()
    deadline = started + duration_seconds

    with mp.Pool(processes=workers) as pool:
        operations_by_worker = pool.map(_cpu_work_until, [deadline] * workers)

    elapsed = time.perf_counter() - started
    return {
        **_result(sum(operations_by_worker), elapsed),
        "workers": workers,
        "operations_by_worker": operations_by_worker,
    }


def _cpu_work_until(deadline: float) -> int:
    operations = 0
    value = 0x12345678

    while time.perf_counter() < deadline:
        for index in range(20_000):
            value = ((value * 1664525 + 1013904223 + index) & 0xFFFFFFFF)
            value ^= value >> 13
            operations += 1

    return operations + (value & 1)


def _result(operations: int, elapsed: float) -> dict[str, Any]:
    operations_per_second = operations / elapsed if elapsed > 0 else 0.0
    return {
        "operations": operations,
        "elapsed_seconds": round(elapsed, 3),
        "operations_per_second": round(operations_per_second, 2),
        "score": round(operations_per_second / 1000, 2),
    }


def _clamp_duration(duration_seconds: int) -> int:
    return min(MAX_SECONDS, max(MIN_SECONDS, duration_seconds))


def _safe_frequency() -> float | None:
    frequency = psutil.cpu_freq()
    if frequency is None:
        return None
    return round(frequency.current, 2)


def _safe_ratio(left: float, right: float) -> float | None:
    if right == 0:
        return None
    return round(left / right, 2)
