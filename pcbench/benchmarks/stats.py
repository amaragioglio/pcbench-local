"""Helpers to turn repeated measurements into one trustworthy number."""

from __future__ import annotations

import statistics
from typing import Any


def summarize(samples: list[float]) -> dict[str, Any]:
    """Median of the samples plus how much they disagreed (coefficient of variation).

    The median ignores a single outlier (an antivirus scan, a browser tab waking
    up). The spread tells the user how much to trust the result.
    """
    values = [float(v) for v in samples if v is not None]
    if not values:
        return {"median": 0.0, "samples": [], "cv_percent": None, "confidence": "low"}
    median = statistics.median(values)
    cv = (statistics.pstdev(values) / median * 100) if median and len(values) > 1 else 0.0
    return {
        "median": round(median, 2),
        "samples": [round(v, 2) for v in values],
        "cv_percent": round(cv, 1),
        "confidence": confidence_from_cv(cv),
    }


def confidence_from_cv(cv_percent: float | None) -> str:
    if cv_percent is None:
        return "low"
    if cv_percent < 5:
        return "high"
    if cv_percent < 15:
        return "medium"
    return "low"
