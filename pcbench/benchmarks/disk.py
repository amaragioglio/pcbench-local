from __future__ import annotations

import os
import sys
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

import psutil

from pcbench.benchmarks.stats import summarize


BYTES_IN_MIB = 1024**2
DEFAULT_TEST_MIB = 512
MIN_TEST_MIB = 64
MAX_TEST_MIB = 4096
BLOCK_MIB = 4
LATENCY_SAMPLES = 128
READ_TRIALS = 3
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
            "Local temporary-file benchmark.",
            "Reads bypass the OS file cache when possible (see read.cache_bypassed).",
            "Results may vary with antivirus scans and other disk activity.",
            "Latency measures fsync overhead across 128 writes of 4 KiB cycling through the first 512 KiB of the file, not arbitrary physical-sector latency.",
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
    """Sequential read that bypasses the OS file cache when the platform allows it.

    Right after writing, the whole file sits in RAM; a plain read would report
    RAM speed (several GB/s) instead of the disk. `cache_bypassed` tells the
    report whether the number is trustworthy.
    """
    rates: list[float] = []
    bypassed = True
    checksum = 0
    for _ in range(READ_TRIALS):
        if sys.platform == "win32":
            result = _read_windows_unbuffered(path)
        else:
            result = _read_posix_dropping_cache(path)
        if result is None:  # bypass not available: fall back to a cached read
            bypassed = False
            result = _read_plain(path)
        read_bytes, elapsed, checksum = result
        rates.append(_mib_per_second(read_bytes or size_bytes, elapsed))

    summary = summarize(rates)
    return {
        "mib_per_second": summary["median"],
        "samples": summary["samples"],
        "cv_percent": summary["cv_percent"],
        "confidence": summary["confidence"] if bypassed else "low",
        "cache_bypassed": bypassed,
        "checksum": checksum,
    }


def _read_plain(path: Path) -> tuple[int, float, int]:
    read = checksum = 0
    started = time.perf_counter()
    with path.open("rb", buffering=0) as file:
        while chunk := file.read(BLOCK_MIB * BYTES_IN_MIB):
            read += len(chunk)
            checksum ^= chunk[0]
    return read, time.perf_counter() - started, checksum


def _read_posix_dropping_cache(path: Path) -> tuple[int, float, int] | None:
    fd = os.open(path, os.O_RDONLY)
    try:
        if hasattr(os, "posix_fadvise"):
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)  # Linux: evict clean pages
        elif sys.platform == "darwin":
            import fcntl
            fcntl.fcntl(fd, 48, 1)  # F_NOCACHE
        else:
            return None
        read = checksum = 0
        started = time.perf_counter()
        while chunk := os.read(fd, BLOCK_MIB * BYTES_IN_MIB):
            read += len(chunk)
            checksum ^= chunk[0]
        return read, time.perf_counter() - started, checksum
    except OSError:
        return None
    finally:
        os.close(fd)


def _read_windows_unbuffered(path: Path) -> tuple[int, float, int] | None:
    """ReadFile with FILE_FLAG_NO_BUFFERING into a page-aligned buffer."""
    try:
        import ctypes
        import mmap
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                         wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel32.ReadFile.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                                      ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

        generic_read, share_read, open_existing = 0x80000000, 0x1, 3
        no_buffering, sequential = 0x20000000, 0x08000000
        handle = kernel32.CreateFileW(str(path), generic_read, share_read, None, open_existing,
                                      no_buffering | sequential, None)
        if handle in (None, wintypes.HANDLE(-1).value):
            return None
        block = BLOCK_MIB * BYTES_IN_MIB  # multiple of every common sector size
        buffer = mmap.mmap(-1, block)     # anonymous mapping: page aligned
        address = ctypes.addressof(ctypes.c_char.from_buffer(buffer))
        got = wintypes.DWORD(0)
        read = checksum = 0
        try:
            started = time.perf_counter()
            while True:
                if not kernel32.ReadFile(handle, address, block, ctypes.byref(got), None):
                    return None
                if got.value == 0:
                    break
                read += got.value
                checksum ^= buffer[0]
            elapsed = time.perf_counter() - started
        finally:
            kernel32.CloseHandle(handle)
            buffer.close()
        return read, elapsed, checksum
    except (OSError, AttributeError, ValueError, TypeError):
        return None


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
