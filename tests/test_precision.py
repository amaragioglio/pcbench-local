from pcbench.benchmarks.stats import confidence_from_cv, summarize


def test_summarize_uses_median_and_flags_noise() -> None:
    steady = summarize([100, 101, 99])
    noisy = summarize([100, 160, 60])
    assert steady["median"] == 100
    assert steady["confidence"] == "high"
    assert noisy["confidence"] == "low"


def test_summarize_ignores_single_outlier() -> None:
    assert summarize([100, 102, 20])["median"] == 100


def test_confidence_thresholds() -> None:
    assert confidence_from_cv(2) == "high"
    assert confidence_from_cv(10) == "medium"
    assert confidence_from_cv(30) == "low"


def test_cpu_benchmark_reports_trials_and_confidence() -> None:
    from pcbench.benchmarks.cpu import run_cpu_benchmark

    result = run_cpu_benchmark(1)
    assert result["trials"] == 3
    assert len(result["single_core"]["samples"]) == 3
    assert result["confidence"] in {"high", "medium", "low"}
    assert result["score"]["multi_core"] > 0


def test_ram_bandwidth_measures_memory_not_interpreter() -> None:
    from pcbench.benchmarks.memory import _run_bandwidth_test

    result = _run_bandwidth_test(64)
    # A Python-loop read is ~200 MiB/s; memchr over RAM is far above 1 GiB/s.
    assert result["read_mib_per_second"] > 1000
    assert result["method_version"] == 2


def test_disk_read_reports_cache_status(tmp_path, monkeypatch) -> None:
    from pcbench.benchmarks import disk

    monkeypatch.setattr(disk, "TEST_DIR", tmp_path)
    monkeypatch.setattr(disk, "TEST_PATH", tmp_path / "t.tmp")
    result = disk.run_disk_benchmark(64)
    assert "cache_bypassed" in result["read"]
    assert len(result["read"]["samples"]) == 3
