import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pcbench import logging_setup


def test_setup_file_logger_creates_rotating_log(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "pcbench.log"

    logger = logging_setup.setup_file_logger(tmp_path)
    logger.info("test message")

    for handler in logger.handlers:
        handler.flush()

    assert log_path.exists()
    assert "test message" in log_path.read_text(encoding="utf-8")
    assert any(isinstance(handler, RotatingFileHandler) for handler in logger.handlers)

    _close_logger(logger)


def test_setup_file_logger_does_not_duplicate_handlers(tmp_path: Path, monkeypatch) -> None:
    logger = logging_setup.setup_file_logger(tmp_path)
    first_count = len(logger.handlers)
    logger = logging_setup.setup_file_logger(tmp_path)

    assert len(logger.handlers) == first_count

    _close_logger(logger)


def _close_logger(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
