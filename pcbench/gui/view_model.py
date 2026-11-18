"""Turn a raw PCBench report into the plain-language inspection sheet.

Each line has a light: red (fix now), amber (should fix), green (fine).
Informational findings are "notes": no light lit, not counted as problems.
"""

from __future__ import annotations

from typing import Any

from pcbench.gui.i18n import t
from pcbench.security.advice import advice_for

LIGHT_BY_SEVERITY = {"critical": "red", "warning": "amber", "ok": "green", "info": "note"}
LIGHT_ORDER = {"red": 0, "amber": 1, "green": 2, "note": 3, "grey": 4}
GROUP_BY_ID = {
    "av_ok": "protection", "av_off": "protection", "av_outdated": "protection", "tamper_off": "protection",
    "firewall_ok": "protection", "firewall_off": "protection", "linux_firewall_off": "protection",
    "smartscreen_off": "protection", "secure_boot_off": "protection", "disk_not_encrypted": "protection",
    "updates_ok": "updates", "updates_old": "updates", "reboot_pending": "updates",
    "uac_off": "accounts", "uac_silent": "accounts", "guest_on": "accounts", "autologon_on": "accounts",
    "autologon_password": "accounts", "many_admins": "accounts",
    "rdp_on": "remote", "rdp_no_nla": "remote", "smb1_on": "remote", "ports_exposed": "remote",
}
GROUP_ORDER = ["protection", "updates", "accounts", "remote", "system"]
HIDDEN_IDS = {"partial_scan"}  # shown as the admin badge in the header instead
STATUS_LIGHT = {"GOOD": "green", "OK": "green", "WARN": "amber", "LOW": "red"}
STATUS_WORD = {"GOOD": "good", "OK": "ok", "WARN": "warn", "LOW": "low"}


def build_view(report: dict[str, Any] | None, previous: dict[str, Any] | None, language: str) -> dict[str, Any]:
    if not report:
        return {"state": "empty"}
    results = report.get("results", {})
    security = _security_lines(results.get("security_audit"), previous, language)
    performance = _performance_lines(report, language)
    tally = {
        "red": sum(1 for line in security if line["light"] == "red"),
        "amber": sum(1 for line in security if line["light"] == "amber"),
        "green": sum(1 for line in security if line["light"] == "green" and not line["resolved"]),
    }
    level = "critical" if tally["red"] else ("warning" if tally["amber"] else "ok")
    audit = results.get("security_audit") or {}
    return {
        "state": "done",
        "finished_at": report.get("finished_at"),
        "verdict": {"level": level, "title": t(language, f"verdict_{level}"), "subtitle": t(language, f"verdict_sub_{level}")},
        "tally": tally,
        "partial": bool(audit.get("partial")),
        "overall_score": (report.get("dashboard") or {}).get("overall_score"),
        "security": _grouped(security, language),
        "performance": [{"group": t(language, "group_performance"), "lines": performance}],
        "performance_attention": sum(1 for line in performance
                                     if line["light"] in ("red", "amber") and line["id"] != "perf_score"),
    }


def _security_lines(audit: dict | None, previous: dict | None, language: str) -> list[dict[str, Any]]:
    if not isinstance(audit, dict) or audit.get("status") == "failed":
        return [{"id": "security_failed", "group": "system", "light": "grey", "title": t(language, "failed"),
                 "why": "", "fix": [], "detail": "", "note": False, "resolved": False}]
    lines = []
    current_problems = set()
    for finding in audit.get("findings", []):
        fid = str(finding.get("id", ""))
        if fid in HIDDEN_IDS:
            continue
        severity = str(finding.get("severity", "info"))
        if severity in ("critical", "warning"):
            current_problems.add(fid)
        advice = advice_for(finding, language)
        lines.append({
            "id": fid or finding.get("area", ""),
            "group": GROUP_BY_ID.get(fid, "system"),
            "light": LIGHT_BY_SEVERITY.get(severity, "green"),
            "note": severity == "info",
            "resolved": False,
            "title": advice["title"],
            "why": advice.get("why", ""),
            "fix": advice.get("fix", []),
            "detail": _detail(fid, str(finding.get("message", "")), language),
        })
    lines.extend(_resolved_since(previous, current_problems, language))
    return lines


def _detail(fid: str, message: str, language: str) -> str:
    """Keep only details that add facts (days, product names, ports), in the user's language."""
    import re

    days = re.search(r"(\d+) days", message)
    if fid in ("updates_ok", "updates_old") and days:
        return f"Última actualización hace {days.group(1)} días" if language == "es" else f"Last update {days.group(1)} days ago"
    if fid == "av_outdated" and days:
        return f"Firmas de hace {days.group(1)} días" if language == "es" else f"Definitions {days.group(1)} days old"
    if fid in ("av_ok", "firewall_ok") and message.startswith("Active: "):
        return message.replace("Active: ", "Activo: " if language == "es" else "Active: ").rstrip(".")
    if fid == "firewall_off" and ":" in message:
        names = message.split(":", 1)[1].strip().rstrip(".")
        return f"Redes sin firewall: {names}" if language == "es" else f"Networks without firewall: {names}"
    if fid == "ports_exposed" and ":" in message:
        ports = message.split(":", 1)[1].strip().rstrip(".")
        return f"Puertos: {ports}" if language == "es" else f"Ports: {ports}"
    if fid == "many_admins":
        count = message.split(" ", 1)[0]
        return f"{count} administradores" if language == "es" else f"{count} administrators"
    return ""


def _resolved_since(previous: dict | None, current_problems: set[str], language: str) -> list[dict[str, Any]]:
    """Problems from the last scan that are gone now stay on the sheet, marked fixed."""
    audit = ((previous or {}).get("results") or {}).get("security_audit") or {}
    resolved = []
    seen = set()
    for finding in audit.get("findings", []) if isinstance(audit, dict) else []:
        fid = str(finding.get("id", ""))
        if finding.get("severity") in ("critical", "warning") and fid and fid not in current_problems and fid not in seen:
            seen.add(fid)
            advice = advice_for(finding, language)
            resolved.append({"id": f"resolved_{fid}", "group": GROUP_BY_ID.get(fid, "system"), "light": "green",
                             "note": False, "resolved": True, "title": advice["title"],
                             "why": t(language, "resolved"), "fix": [], "detail": ""})
    return resolved


def _grouped(lines: list[dict[str, Any]], language: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for line in lines:
        groups.setdefault(line["group"], []).append(line)
    ordered = []
    for name, items in groups.items():
        items.sort(key=lambda line: (LIGHT_ORDER[line["light"]], line["resolved"], line["note"]))
        ordered.append({"key": name, "group": t(language, f"group_{name}"), "lines": items})
    ordered.sort(key=lambda g: (min(LIGHT_ORDER[line["light"]] for line in g["lines"]), GROUP_ORDER.index(g["key"])
                                if g["key"] in GROUP_ORDER else 99))
    return ordered


def _performance_lines(report: dict[str, Any], language: str) -> list[dict[str, Any]]:
    results = report.get("results", {})
    rows = {row["area"]: row for row in (report.get("dashboard") or {}).get("rows", [])}
    lines: list[dict[str, Any]] = []

    def scored(area: str, prefix: str, data_key: str, why: str = "") -> None:
        row = rows.get(area)
        data = results.get(data_key)
        if not row:
            if isinstance(data, dict) and data.get("status") == "failed":
                lines.append(_line(prefix, "grey", t(language, "failed"), "", ""))
            return
        status = str(row.get("status"))
        light = STATUS_LIGHT.get(status, "grey")
        confidence = (data or {}).get("confidence") or ((data or {}).get("bandwidth") or {}).get("confidence")
        note = t(language, "confidence_low") if confidence == "low" else ""
        lines.append(_line(prefix, light, t(language, f"{prefix}_{STATUS_WORD.get(status, 'ok')}"),
                           f"{float(row['score']):.0f}/100", why if light != "green" else "", note))

    scored("CPU", "cpu", "cpu_benchmark")
    scored("RAM", "ram", "memory_benchmark")
    scored("DISK", "disk", "disk_benchmark", t(language, "disk_slow_why"))
    scored("NET", "net", "network_benchmark", t(language, "net_why"))

    system = results.get("system_info") or {}
    ram = system.get("ram") or {}
    used = ram.get("used_percent")
    if isinstance(used, (int, float)) and used >= 85:
        lines.append(_line("ram_full", "amber", t(language, "ram_full"), t(language, "used_of", used=round(used)),
                           t(language, "ram_full_why")))

    disk = _system_disk(system.get("disks") or [])
    if disk:
        free_pct = 100 - float(disk.get("used_percent", 0))
        light = "red" if free_pct < 5 else ("amber" if free_pct < 10 else "green")
        lines.append(_line("space", light, t(language, "space_low" if light != "green" else "space_ok"),
                           t(language, "free_of", free=f"{disk.get('free_gib')} GB", total=f"{disk.get('total_gib')} GB"),
                           t(language, "space_low_why") if light != "green" else ""))

    gpu = ((results.get("gpu_benchmark") or {}).get("nvidia_smi") or {}).get("gpus") or []
    if gpu:
        temp = gpu[0].get("temperature_c")
        hot = isinstance(temp, (int, float)) and temp >= 85
        lines.append(_line("gpu", "amber" if hot else "green", t(language, "gpu_hot" if hot else "gpu_ok"),
                           f"{temp} °C" if temp is not None else str(gpu[0].get("name", "")),
                           t(language, "gpu_hot_why") if hot else ""))

    lines.sort(key=lambda line: LIGHT_ORDER[line["light"]])

    # One line that answers "is it performing well?" (security excluded: it has its own tab).
    perf_scores = [float(row["score"]) for area, row in rows.items() if area != "SEC"]
    if perf_scores:
        average = sum(perf_scores) / len(perf_scores)
        light = "green" if average >= 65 else ("amber" if average >= 40 else "red")
        lines.insert(0, _line("perf_score", light, t(language, "perf_score"), f"{average:.0f}/100"))
    return lines


def _line(lid: str, light: str, title: str, value: str, why: str = "", note: str = "") -> dict[str, Any]:
    return {"id": lid, "light": light, "title": title, "value": value, "why": why, "fix": [],
            "detail": note, "note": False, "resolved": False}


def _system_disk(disks: list[dict[str, Any]]) -> dict[str, Any] | None:
    import os

    system_root = (os.environ.get("SystemDrive", "C:") + "\\").upper()
    for disk in disks:
        mount = str(disk.get("mountpoint", "")).upper()
        if mount in (system_root, "/"):
            return disk
    return None
