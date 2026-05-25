from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pcbench.reports.paths import ensure_reports_dir


def save_json_report(report: dict[str, Any], output_dir: Path | str | None = None) -> Path:
    reports_dir = ensure_reports_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"pcbench_report_{timestamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    return path
