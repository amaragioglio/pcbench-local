from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any

import psutil

from pcbench.elevation import is_windows_admin
from pcbench.security.linux_audit import run_linux_security_audit


# Absolute path: a bare "powershell" could resolve to a planted powershell.exe
# in the current folder (for example, a Downloads folder).
POWERSHELL = str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe")
POSTURE_SCRIPT = Path(__file__).with_name("windows_posture.ps1")
LOOPBACK = ("127.", "::1")
COMMON_EXPOSED_PORTS = {21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 389, 443, 445, 3389, 5985, 5986}


def run_security_audit() -> dict[str, Any]:
    if platform.system().lower() == "linux":
        return run_linux_security_audit()

    privileges = _collect_privileges()
    posture = _collect_posture()
    firewall = _collect_firewall_status()
    local_admins = _collect_local_admins()
    listening_ports = _collect_listening_ports()
    active_connections = _collect_active_connections()
    startup_items = _collect_startup_items()
    findings = build_windows_findings(
        privileges, posture.get("data") or {}, firewall, local_admins, listening_ports
    )

    return {
        "platform": "windows",
        "partial": not privileges["is_admin"],
        "privileges": privileges,
        "posture": posture,
        "defender": {"status": posture.get("status"), "data": (posture.get("data") or {}).get("defender")},
        "firewall": firewall,
        "local_admins": local_admins,
        "listening_ports": listening_ports,
        "active_connections": active_connections,
        "startup_items": startup_items,
        "findings": findings,
        "summary": _summarize_findings(findings),
        "notes": [
            "Read-only local audit: nothing is changed and no passwords are read.",
            "Not an antivirus: it checks how the PC is configured, not whether it is infected.",
            "Running as administrator unlocks disk-encryption and some service checks.",
        ],
    }


def _collect_posture() -> dict[str, Any]:
    try:
        script = POSTURE_SCRIPT.read_text(encoding="utf-8")
    except OSError as error:
        return {"status": "failed", "error": str(error)}
    return _run_powershell_json(script, timeout=60)


def _collect_privileges() -> dict[str, Any]:
    try:
        is_admin = is_windows_admin()
        return {
            "status": "passed",
            "is_admin": is_admin,
            "scope": "elevated" if is_admin else "limited",
        }
    except (AttributeError, OSError) as error:
        return {
            "status": "failed",
            "is_admin": False,
            "scope": "unknown",
            "error": str(error),
        }


def _collect_firewall_status() -> dict[str, Any]:
    command = """
    Get-NetFirewallProfile |
      Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
      ConvertTo-Json -Compress
    """
    result = _run_powershell_json(command)
    if isinstance(result.get("data"), dict):
        result["data"] = [result["data"]]
    return result


def _collect_local_admins() -> dict[str, Any]:
    command = """
    $group = Get-LocalGroup | Where-Object { $_.SID -like '*-544' } | Select-Object -First 1
    if ($null -eq $group) { @() | ConvertTo-Json -Compress }
    else {
      Get-LocalGroupMember -Group $group.Name |
        Select-Object Name, ObjectClass, PrincipalSource |
        ConvertTo-Json -Compress
    }
    """
    result = _run_powershell_json(command)
    if isinstance(result.get("data"), dict):
        result["data"] = [result["data"]]
    if result.get("data") is None:
        result["data"] = []
    return result


def _collect_startup_items() -> dict[str, Any]:
    command = """
    Get-CimInstance Win32_StartupCommand |
      Select-Object Name, Command, Location, User |
      ConvertTo-Json -Compress
    """
    result = _run_powershell_json(command)
    if isinstance(result.get("data"), dict):
        result["data"] = [result["data"]]
    if result.get("data") is None:
        result["data"] = []
    return result


def _collect_listening_ports() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for connection in psutil.net_connections(kind="inet"):
        if connection.status != psutil.CONN_LISTEN or not connection.laddr:
            continue

        process_name = None
        if connection.pid:
            try:
                process_name = psutil.Process(connection.pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = None

        rows.append(
            {
                "ip": connection.laddr.ip,
                "port": connection.laddr.port,
                "pid": connection.pid,
                "process": process_name,
                "is_common_exposed_port": connection.laddr.port in COMMON_EXPOSED_PORTS,
            }
        )

    return sorted(rows, key=lambda row: (row["port"], row["ip"]))


def _collect_active_connections() -> dict[str, Any]:
    established = []
    for connection in psutil.net_connections(kind="inet"):
        if connection.status != psutil.CONN_ESTABLISHED or not connection.raddr:
            continue
        established.append(
            {
                "local": f"{connection.laddr.ip}:{connection.laddr.port}" if connection.laddr else None,
                "remote": f"{connection.raddr.ip}:{connection.raddr.port}",
                "pid": connection.pid,
            }
        )

    return {
        "established_count": len(established),
        "sample": established[:25],
    }


def _av_state(product_state: Any) -> tuple[bool, bool]:
    """Decode Security Center productState into (enabled, definitions_up_to_date)."""
    try:
        digits = f"{int(product_state):06x}"
    except (TypeError, ValueError):
        return False, False
    return digits[2:4] in ("10", "11"), digits[4:6] == "00"


def _finding(fid: str, severity: str, area: str, message: str) -> dict[str, str]:
    return {"id": fid, "severity": severity, "area": area, "message": message}


def build_windows_findings(
    privileges: dict[str, Any],
    posture: dict[str, Any],
    firewall: dict[str, Any],
    local_admins: dict[str, Any],
    listening_ports: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Turn raw read-only checks into findings. Pure function, easy to test.

    Severities: critical (fix now), warning (should fix), info (worth knowing), ok.
    """
    f: list[dict[str, str]] = []

    # Antivirus: any product registered with Windows Security Center counts,
    # not only Microsoft Defender (avoids a false alarm with Norton, ESET...).
    products = posture.get("antivirus_products") or []
    active = [p for p in products if _av_state(p.get("state"))[0]]
    defender = posture.get("defender") or {}
    if active:
        names = ", ".join(sorted({str(p.get("name")) for p in active}))
        f.append(_finding("av_ok", "ok", "Antivirus", f"Active: {names}."))
        if any(not _av_state(p.get("state"))[1] for p in active):
            f.append(_finding("av_outdated", "warning", "Antivirus", "Definitions are out of date."))
    elif defender.get("antivirus_enabled") and defender.get("realtime_enabled"):
        f.append(_finding("av_ok", "ok", "Antivirus", "Microsoft Defender is active."))
    elif products or defender:
        f.append(_finding("av_off", "critical", "Antivirus", "No antivirus with real-time protection is active."))

    defender_is_active = any("defender" in str(p.get("name", "")).lower() for p in active) or (
        not active and defender.get("realtime_enabled"))
    if defender_is_active:
        age = defender.get("signature_age_days")
        if isinstance(age, (int, float)) and age > 7 and not any(x["id"] == "av_outdated" for x in f):
            f.append(_finding("av_outdated", "warning", "Antivirus", f"Defender definitions are {int(age)} days old."))
        if defender.get("tamper_protected") is False:
            f.append(_finding("tamper_off", "warning", "Antivirus", "Tamper Protection is off."))

    # Firewall: Windows profiles, unless another firewall is registered and on.
    third_party_fw = [p for p in (posture.get("firewall_products") or []) if _av_state(p.get("state"))[0]]
    profiles = firewall.get("data") if firewall.get("status") == "passed" else []
    disabled = [str(p.get("Name")) for p in profiles or [] if not p.get("Enabled")]
    if third_party_fw:
        names = ", ".join(sorted({str(p.get("name")) for p in third_party_fw}))
        f.append(_finding("firewall_ok", "ok", "Firewall", f"Active: {names}."))
    elif disabled:
        severity = "critical" if "Public" in disabled else "warning"
        f.append(_finding("firewall_off", severity, "Firewall", f"Disabled profiles: {', '.join(disabled)}."))
    elif profiles:
        f.append(_finding("firewall_ok", "ok", "Firewall", "Windows Firewall is on for all networks."))

    # Updates
    days = posture.get("last_update_days")
    if isinstance(days, (int, float)):
        if days > 120:
            f.append(_finding("updates_old", "critical", "Updates", f"Last update installed {int(days)} days ago."))
        elif days > 45:
            f.append(_finding("updates_old", "warning", "Updates", f"Last update installed {int(days)} days ago."))
        else:
            f.append(_finding("updates_ok", "ok", "Updates", f"Last update installed {int(days)} days ago."))
    if posture.get("reboot_pending"):
        f.append(_finding("reboot_pending", "info", "Updates", "A restart is pending to finish updates."))

    # Accounts
    if posture.get("uac_enabled") == 0:
        f.append(_finding("uac_off", "critical", "Accounts", "User Account Control is disabled."))
    elif posture.get("uac_admin_prompt") == 0:
        f.append(_finding("uac_silent", "warning", "Accounts", "UAC elevates without prompting."))
    if posture.get("guest_enabled") is True:
        f.append(_finding("guest_on", "warning", "Accounts", "Guest account is enabled."))
    if posture.get("autologon_enabled"):
        if posture.get("autologon_password_stored"):
            f.append(_finding("autologon_password", "critical", "Accounts",
                              "Automatic sign-in with a password stored in the registry."))
        else:
            f.append(_finding("autologon_on", "warning", "Accounts", "Automatic sign-in is enabled."))
    admins = local_admins.get("data") or []
    if len(admins) > 2:
        f.append(_finding("many_admins", "info", "Accounts", f"{len(admins)} local administrator members."))

    # Remote access
    if posture.get("rdp_enabled"):
        if posture.get("rdp_nla"):
            f.append(_finding("rdp_on", "info", "Remote access", "Remote Desktop is enabled with NLA."))
        else:
            f.append(_finding("rdp_no_nla", "critical", "Remote access",
                              "Remote Desktop is enabled without Network Level Authentication."))
    if posture.get("smb1_server"):
        f.append(_finding("smb1_on", "critical", "File sharing", "SMBv1 server is enabled."))
    elif posture.get("smb1_client"):
        f.append(_finding("smb1_on", "warning", "File sharing", "SMBv1 client is enabled."))

    # Boot, disk and downloads
    if posture.get("secure_boot") == 0:
        f.append(_finding("secure_boot_off", "warning", "Boot", "Secure Boot is disabled."))
    bitlocker = posture.get("bitlocker")
    if isinstance(bitlocker, dict) and bitlocker.get("protection_on") is False:
        severity = "warning" if posture.get("is_laptop") else "info"
        f.append(_finding("disk_not_encrypted", severity, "Disk", "System drive is not encrypted."))
    if str(posture.get("smartscreen", "")).lower() == "off":
        f.append(_finding("smartscreen_off", "warning", "Downloads", "SmartScreen is disabled."))

    # Ports reachable from the network (loopback-only services are not exposed)
    exposed = sorted({row["port"] for row in listening_ports
                      if row.get("is_common_exposed_port") and not str(row.get("ip", "")).startswith(LOOPBACK)})
    if exposed:
        f.append(_finding("ports_exposed", "info", "Ports",
                          f"Listening on the network: {', '.join(str(p) for p in exposed[:12])}."))

    if not privileges.get("is_admin"):
        f.append(_finding("partial_scan", "info", "Scope",
                          "Ran without administrator rights; some checks were skipped."))
    return f


def _summarize_findings(findings: list[dict[str, str]]) -> dict[str, int]:
    return {
        "critical": sum(1 for finding in findings if finding["severity"] == "critical"),
        "ok": sum(1 for finding in findings if finding["severity"] == "ok"),
        "warning": sum(1 for finding in findings if finding["severity"] == "warning"),
        "info": sum(1 for finding in findings if finding["severity"] == "info"),
    }


def _run_powershell_json(command: str, timeout: int = 20) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "status": "failed",
            "error": str(error),
        }

    if completed.returncode != 0:
        return {
            "status": "failed",
            "error": completed.stderr.strip() or completed.stdout.strip(),
        }

    output = completed.stdout.strip()
    if not output:
        return {
            "status": "passed",
            "data": None,
        }

    try:
        return {
            "status": "passed",
            "data": json.loads(output),
        }
    except json.JSONDecodeError as error:
        return {
            "status": "failed",
            "error": str(error),
            "raw": output[:1000],
        }
