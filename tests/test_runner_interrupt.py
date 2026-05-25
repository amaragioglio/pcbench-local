import argparse
from pathlib import Path

from rich.console import Console

from pcbench import runner
from pcbench.benchmarks import disk


def test_sigint_handler_cleans_disk_temp(tmp_path: Path, monkeypatch) -> None:
    temp_file = tmp_path / "disk_benchmark.tmp"
    temp_file.write_text("partial", encoding="utf-8")
    monkeypatch.setattr(disk, "TEST_PATH", temp_file)
    monkeypatch.setattr(runner, "cleanup_disk_temp_file", disk.cleanup_disk_temp_file)

    handler = runner._build_sigint_handler(runner.setup_file_logger())

    try:
        handler(2, None)
    except KeyboardInterrupt:
        pass

    assert not temp_file.exists()


def test_run_benchmarks_handles_keyboard_interrupt(monkeypatch) -> None:
    args = argparse.Namespace()
    monkeypatch.setattr(runner, "_run_benchmarks", lambda *_args: (_ for _ in ()).throw(KeyboardInterrupt()))

    result = runner.run_benchmarks(args, Console(file=None))

    assert result == {"json": None, "html": None, "document": None, "markdown": None, "supabase": None}
