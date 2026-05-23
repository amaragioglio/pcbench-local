from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPORTS_DIR = Path("reports")


def save_json_report(report: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"pcbench_report_{timestamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    return path
