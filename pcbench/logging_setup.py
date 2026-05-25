from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path("reports")
LOG_PATH = LOG_DIR / "pcbench.log"
MAX_BYTES = 1_000_000
BACKUP_COUNT = 3


def setup_file_logger() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("pcbench")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(isinstance(handler, RotatingFileHandler) and handler.baseFilename == str(LOG_PATH.resolve()) for handler in logger.handlers):
        handler = RotatingFileHandler(LOG_PATH, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

    return logger
