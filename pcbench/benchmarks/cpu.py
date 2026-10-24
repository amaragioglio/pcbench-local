from __future__ import annotations

import multiprocessing as mp
import time
from typing import Any

import psutil

from pcbench.benchmarks.stats import summarize


DEFAULT_SECONDS = 5
MIN_SECONDS = 1
MAX_SECONDS = 60
TRIALS = 3
WARMUP_SECONDS = 0.5
METHOD_VERSION = 2


def run_cpu_benchmark(duration_seconds: int = DEFAULT_SECONDS) -> dict[str, Any]:
    """Integer workload measured in TRIALS slices; the median is the score.

    Accuracy notes:
    - A short warm-up lets the CPU reach its boost clock before timing.
    - Multi-core workers start together at a shared wall-clock instant and
      each one times only its own work, so process start-up (slow on
      Windows) is not counted.
    """
    duration_seconds = _clamp_duration(duration_seconds)
    logical_threads = psutil.cpu_count(logical=True) or 1
    physical_cores = psutil.cpu_count(logical=False)
    frequency_before = _safe_frequency()
    usage_before = psutil.cpu_percent(interval=0.2)
    slice_seconds = max(0.5, duration_seconds / TRIALS)

    _cpu_work_until(time.perf_counter() + WARMUP_SECONDS)
    single_rates = [_single_trial(slice_seconds) for _ in range(TRIALS)]

    with mp.Pool(processes=logical_threads) as pool:
        pool.map(_noop, range(logical_threads))  # make sure every worker is alive
        multi_trials = [_multi_trial(pool, logical_threads, slice_seconds) for _ in range(TRIALS)]

    usage_after = psutil.cpu_percent(interval=0.2)
    frequency_after = _safe_frequency()

    single = summarize([rate / 1000 for rate in single_rates])
    multi = summarize([trial["rate"] / 1000 for trial in multi_trials])
    best_multi = max(multi_trials, key=lambda trial: trial["rate"])

    return {
        "method_version": METHOD_VERSION,
        "duration_seconds": duration_seconds,
        "trials": TRIALS,
        "physical_cores": physical_cores,
        "logical_threads": logical_threads,
        "frequency_before_mhz": frequency_before,
        "frequency_after_mhz": frequency_after,
        "cpu_usage_before_percent": usage_before,
        "cpu_usage_after_percent": usage_after,
        "single_core": {**single, "score": single["median"]},
        "multi_core": {**multi, "score": multi["median"], "workers": logical_threads,
                       "operations_by_worker": best_multi["operations_by_worker"]},
        "score": {
            "single_core": single["median"],
            "multi_core": multi["median"],
            "scaling_factor": _safe_ratio(multi["median"], single["median"]),
        },
        "confidence": _worst(single["confidence"], multi["confidence"]),
        "notes": [
            "Integer operations per second (thousands), median of several trials after a warm-up.",
            "Busy background apps lower the score and the confidence.",
            "Useful for comparing runs of this tool; it does not replace Cinebench.",
        ],
    }


def _single_trial(seconds: float) -> float:
    started = time.perf_counter()
    operations = _cpu_work_until(started + seconds)
    return operations / (time.perf_counter() - started)


def _multi_trial(pool: Any, workers: int, seconds: float) -> dict[str, Any]:
    start_at = time.time() + 0.15
    results = pool.map(_timed_worker, [(start_at, seconds)] * workers)
    return {
        "rate": sum(ops / elapsed for ops, elapsed in results if elapsed > 0),
        "operations_by_worker": [ops for ops, _ in results],
    }


def _timed_worker(args: tuple[float, float]) -> tuple[int, float]:
    start_at, seconds = args
    delay = start_at - time.time()
    if delay > 0:
        time.sleep(delay)
    started = time.perf_counter()
    operations = _cpu_work_until(started + seconds)
    return operations, time.perf_counter() - started


def _noop(_: int) -> None:
    return None


def _worst(*levels: str) -> str:
    order = ["low", "medium", "high"]
    return min(levels, key=order.index)


def _cpu_work_until(deadline: float) -> int:
    operations = 0
    value = 0x12345678

    while time.perf_counter() < deadline:
        for index in range(20_000):
            value = ((value * 1664525 + 1013904223 + index) & 0xFFFFFFFF)
            value ^= value >> 13
            operations += 1

    return operations + (value & 1)


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
