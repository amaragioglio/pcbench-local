from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pcbench.reports.paths import ensure_reports_dir


MAX_BYTES = 1_000_000
BACKUP_COUNT = 3


def setup_file_logger(output_dir: Path | str | None = None) -> logging.Logger:
    log_dir = ensure_reports_dir(output_dir)
    log_path = log_dir / "pcbench.log"
    logger = logging.getLogger("pcbench")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(isinstance(handler, RotatingFileHandler) and handler.baseFilename == str(log_path.resolve()) for handler in logger.handlers):
        handler = RotatingFileHandler(log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

    return logger
