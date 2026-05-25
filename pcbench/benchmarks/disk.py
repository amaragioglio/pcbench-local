from __future__ import annotations

import os
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

import psutil


BYTES_IN_MIB = 1024**2
DEFAULT_TEST_MIB = 512
MIN_TEST_MIB = 64
MAX_TEST_MIB = 4096
BLOCK_MIB = 4
LATENCY_SAMPLES = 128
LATENCY_BLOCK_BYTES = 4096
TEST_DIR = Path(tempfile.gettempdir()) / "pcbench-local"
TEST_PATH = TEST_DIR / "disk_benchmark.tmp"


def run_disk_benchmark(test_mib: int = DEFAULT_TEST_MIB) -> dict[str, Any]:
    test_mib = _clamp_test_size(test_mib)
    TEST_DIR.mkdir(exist_ok=True)
    size_bytes = test_mib * BYTES_IN_MIB
    block = os.urandom(BLOCK_MIB * BYTES_IN_MIB)

    disk_before = psutil.disk_usage(str(TEST_DIR))

    try:
        write_result = _write_test_file(TEST_PATH, size_bytes, block)
        read_result = _read_test_file(TEST_PATH, size_bytes)
        latency_result = _latency_test(TEST_PATH)
    finally:
        cleanup_disk_temp_file()

    disk_after = psutil.disk_usage(str(TEST_DIR))

    return {
        "test_path": str(TEST_PATH),
        "test_size_mib": test_mib,
        "filesystem": {
            "total_gib": _gib(disk_before.total),
            "free_before_gib": _gib(disk_before.free),
            "free_after_gib": _gib(disk_after.free),
        },
        "write": write_result,
        "read": read_result,
        "latency": latency_result,
        "notes": [
            "Benchmark de archivo temporal local.",
            "Los resultados pueden variar por cache del sistema, antivirus y carga del disco.",
            "La metrica de latencia mide overhead de fsync sobre 128 escrituras de 4 KiB ciclando los primeros 512 KiB del archivo, no latencia de sectores fisicos arbitrarios.",
        ],
    }


def _write_test_file(path: Path, size_bytes: int, block: bytes) -> dict[str, Any]:
    written = 0
    started = time.perf_counter()

    with path.open("wb") as file:
        while written < size_bytes:
            remaining = size_bytes - written
            data = block if remaining >= len(block) else block[:remaining]
            file.write(data)
            written += len(data)
        file.flush()
        os.fsync(file.fileno())

    elapsed = time.perf_counter() - started
    return {
        "elapsed_seconds": round(elapsed, 3),
        "mib_per_second": _mib_per_second(written, elapsed),
    }


def _read_test_file(path: Path, size_bytes: int) -> dict[str, Any]:
    read = 0
    checksum = 0
    started = time.perf_counter()

    with path.open("rb") as file:
        while chunk := file.read(BLOCK_MIB * BYTES_IN_MIB):
            read += len(chunk)
            checksum ^= chunk[0]

    elapsed = time.perf_counter() - started
    return {
        "elapsed_seconds": round(elapsed, 3),
        "mib_per_second": _mib_per_second(read or size_bytes, elapsed),
        "checksum": checksum,
    }


def _latency_test(path: Path) -> dict[str, Any]:
    samples_ms: list[float] = []
    block = b"\0" * LATENCY_BLOCK_BYTES
    file_size = max(LATENCY_BLOCK_BYTES, path.stat().st_size)

    with path.open("r+b") as file:
        for sample in range(LATENCY_SAMPLES):
            offset = (sample * LATENCY_BLOCK_BYTES) % file_size
            started = time.perf_counter()
            file.seek(offset)
            file.write(block)
            file.flush()
            os.fsync(file.fileno())
            samples_ms.append((time.perf_counter() - started) * 1000)

    return {
        "samples": len(samples_ms),
        "block_bytes": LATENCY_BLOCK_BYTES,
        "average_ms": round(statistics.mean(samples_ms), 3),
        "median_ms": round(statistics.median(samples_ms), 3),
        "min_ms": round(min(samples_ms), 3),
        "max_ms": round(max(samples_ms), 3),
        "measurement": "fsync_overhead",
    }


def _clamp_test_size(test_mib: int) -> int:
    return min(MAX_TEST_MIB, max(MIN_TEST_MIB, test_mib))


def _mib_per_second(size_bytes: int, elapsed_seconds: float) -> float:
    if elapsed_seconds <= 0:
        return 0.0
    return round((size_bytes / BYTES_IN_MIB) / elapsed_seconds, 2)


def _gib(value: int | float) -> float:
    return round(value / (1024**3), 2)


def _safe_remove(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def cleanup_disk_temp_file() -> None:
    _safe_remove(TEST_PATH)
