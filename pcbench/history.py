from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from pcbench.reports.paths import ensure_reports_dir, resolve_reports_dir


DB_NAME = "pcbench_history.sqlite"
SCHEMA_VERSION = 1


def history_db_path(output_dir: Path | str | None = None) -> Path:
    return resolve_reports_dir(output_dir) / DB_NAME


def init_history_db(output_dir: Path | str | None = None) -> Path:
    reports_dir = ensure_reports_dir(output_dir)
    db_path = reports_dir / DB_NAME
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                tool TEXT,
                version TEXT,
                profile TEXT,
                started_at TEXT,
                finished_at TEXT,
                overall_score REAL,
                overall_status TEXT,
                sanitized INTEGER NOT NULL DEFAULT 0,
                hostname TEXT,
                os TEXT,
                cpu_brand TEXT,
                ram_total_gib REAL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                area TEXT NOT NULL,
                score REAL,
                status TEXT,
                detail TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                severity TEXT,
                area TEXT,
                message TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)", (SCHEMA_VERSION,))
    return db_path


def save_run_to_history(report: dict[str, Any], output_dir: Path | str | None = None) -> Path:
    db_path = init_history_db(output_dir)
    run_id = _run_id(report)
    dashboard = report.get("dashboard", {})
    results = report.get("results", {})
    system = results.get("system_info", {})
    machine = system.get("machine", {})
    cpu = system.get("cpu", {})
    ram = system.get("ram", {})

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            """
            INSERT OR REPLACE INTO runs (
                run_id, tool, version, profile, started_at, finished_at,
                overall_score, overall_status, sanitized, hostname, os,
                cpu_brand, ram_total_gib, report_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                report.get("tool"),
                report.get("version"),
                report.get("profile"),
                report.get("started_at"),
                report.get("finished_at"),
                dashboard.get("overall_score"),
                dashboard.get("overall_status"),
                1 if report.get("sanitized") else 0,
                machine.get("hostname"),
                machine.get("os"),
                cpu.get("brand"),
                ram.get("total_gib"),
                json.dumps(report, ensure_ascii=True),
            ),
        )
        connection.execute("DELETE FROM metrics WHERE run_id = ?", (run_id,))
        connection.execute("DELETE FROM findings WHERE run_id = ?", (run_id,))
        connection.executemany(
            "INSERT INTO metrics(run_id, area, score, status, detail) VALUES (?, ?, ?, ?, ?)",
            [
                (run_id, row.get("area"), row.get("score"), row.get("status"), row.get("detail"))
                for row in dashboard.get("rows", [])
            ],
        )
        security = results.get("security_audit") or {}
        connection.executemany(
            "INSERT INTO findings(run_id, severity, area, message) VALUES (?, ?, ?, ?)",
            [
                (run_id, finding.get("severity"), finding.get("area"), finding.get("message"))
                for finding in security.get("findings", [])
            ],
        )
    return db_path


def latest_runs(limit: int = 10, output_dir: Path | str | None = None) -> list[dict[str, Any]]:
    db_path = history_db_path(output_dir)
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT run_id, profile, started_at, overall_score, overall_status, sanitized
            FROM runs
            ORDER BY started_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def _run_id(report: dict[str, Any]) -> str:
    raw = f"{report.get('started_at', '')}-{report.get('profile', 'normal')}"
    return raw.replace(":", "").replace(".", "").replace("+", "_")
