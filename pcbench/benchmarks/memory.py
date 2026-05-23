from __future__ import annotations

import gc
import time
from typing import Any

import psutil


BYTES_IN_MIB = 1024**2
PAGE_SIZE = 4096
DEFAULT_MAX_TEST_MIB = 1024
MIN_AVAILABLE_AFTER_TEST_MIB = 1024


def run_memory_benchmark(requested_mib: int | None = None) -> dict[str, Any]:
    memory = psutil.virtual_memory()
    target_mib = _choose_target_mib(memory.available, requested_mib)
    allocation_results = _run_progressive_allocation_test(target_mib)
    bandwidth_results = _run_bandwidth_test(target_mib)
    memory_after = psutil.virtual_memory()

    return {
        "total_gib": _gib(memory.total),
        "available_before_gib": _gib(memory.available),
        "available_after_gib": _gib(memory_after.available),
        "target_test_mib": target_mib,
        "allocation": allocation_results,
        "bandwidth": bandwidth_results,
        "notes": [
            "Esta prueba valida asignacion y velocidad aproximada desde Python.",
            "No reemplaza una prueba profunda tipo MemTest86 para errores fisicos de RAM.",
        ],
    }


def _choose_target_mib(available_bytes: int, requested_mib: int | None) -> int:
    safe_available_mib = max(64, (available_bytes // BYTES_IN_MIB) - MIN_AVAILABLE_AFTER_TEST_MIB)
    automatic_mib = min(DEFAULT_MAX_TEST_MIB, max(128, safe_available_mib // 4))

    if requested_mib is None:
        return automatic_mib

    if requested_mib < 64:
        return 64

    return min(requested_mib, safe_available_mib)


def _run_progressive_allocation_test(target_mib: int) -> dict[str, Any]:
    checkpoints = _allocation_checkpoints(target_mib)
    passed: list[int] = []
    failed_at_mib = None
    started = time.perf_counter()

    for size_mib in checkpoints:
        try:
            buffer = bytearray(size_mib * BYTES_IN_MIB)
            _touch_pages(buffer)
            passed.append(size_mib)
        except MemoryError:
            failed_at_mib = size_mib
            break
        finally:
            if "buffer" in locals():
                del buffer
            gc.collect()

    elapsed = time.perf_counter() - started
    return {
        "status": "passed" if failed_at_mib is None else "failed",
        "tested_checkpoints_mib": passed,
        "largest_successful_mib": max(passed) if passed else 0,
        "failed_at_mib": failed_at_mib,
        "elapsed_seconds": round(elapsed, 3),
    }


def _allocation_checkpoints(target_mib: int) -> list[int]:
    checkpoints: list[int] = []
    size = 64
    while size < target_mib:
        checkpoints.append(size)
        size *= 2

    if target_mib not in checkpoints:
        checkpoints.append(target_mib)

    return checkpoints


def _touch_pages(buffer: bytearray) -> None:
    for index in range(0, len(buffer), PAGE_SIZE):
        buffer[index] = 1


def _run_bandwidth_test(size_mib: int) -> dict[str, Any]:
    size_bytes = size_mib * BYTES_IN_MIB
    buffer = bytearray(size_bytes)
    chunk = bytes([0xA5]) * BYTES_IN_MIB

    write_started = time.perf_counter()
    for offset in range(0, size_bytes, len(chunk)):
        end = min(offset + len(chunk), size_bytes)
        buffer[offset:end] = chunk[: end - offset]
    write_elapsed = time.perf_counter() - write_started

    read_started = time.perf_counter()
    checksum = sum(buffer)
    read_elapsed = time.perf_counter() - read_started

    del buffer
    gc.collect()

    return {
        "test_size_mib": size_mib,
        "write_seconds": round(write_elapsed, 3),
        "read_seconds": round(read_elapsed, 3),
        "write_mib_per_second": _mib_per_second(size_mib, write_elapsed),
        "read_mib_per_second": _mib_per_second(size_mib, read_elapsed),
        "checksum": checksum,
    }


def _mib_per_second(size_mib: int, elapsed_seconds: float) -> float:
    if elapsed_seconds <= 0:
        return 0.0
    return round(size_mib / elapsed_seconds, 2)


def _gib(value: int | float) -> float:
    return round(value / (1024**3), 2)
