from __future__ import annotations

import json
import platform
import subprocess
from typing import Any

import psutil

from pcbench.security.linux_audit import run_linux_security_audit


POWERSHELL = "powershell"
COMMON_EXPOSED_PORTS = {21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 389, 443, 445, 3389, 5985, 5986}


def run_security_audit() -> dict[str, Any]:
    if platform.system().lower() == "linux":
        return run_linux_security_audit()

    defender = _collect_defender_status()
    firewall = _collect_firewall_status()
    local_admins = _collect_local_admins()
    listening_ports = _collect_listening_ports()
    active_connections = _collect_active_connections()
    startup_items = _collect_startup_items()
    findings = _build_findings(defender, firewall, local_admins, listening_ports)

    return {
        "platform": "windows",
        "defender": defender,
        "firewall": firewall,
        "local_admins": local_admins,
        "listening_ports": listening_ports,
        "active_connections": active_connections,
        "startup_items": startup_items,
        "findings": findings,
        "summary": _summarize_findings(findings),
        "notes": [
            "Auditoria local de solo lectura.",
            "No explota vulnerabilidades ni modifica configuracion del sistema.",
        ],
    }


def _collect_defender_status() -> dict[str, Any]:
    command = """
    $status = Get-MpComputerStatus
    [PSCustomObject]@{
      AntivirusEnabled = $status.AntivirusEnabled
      RealTimeProtectionEnabled = $status.RealTimeProtectionEnabled
      AntispywareEnabled = $status.AntispywareEnabled
      BehaviorMonitorEnabled = $status.BehaviorMonitorEnabled
      IoavProtectionEnabled = $status.IoavProtectionEnabled
      AntivirusSignatureLastUpdated = $status.AntivirusSignatureLastUpdated
      QuickScanAge = $status.QuickScanAge
      FullScanAge = $status.FullScanAge
    } | ConvertTo-Json -Compress
    """
    return _run_powershell_json(command)


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


def _build_findings(
    defender: dict[str, Any],
    firewall: dict[str, Any],
    local_admins: dict[str, Any],
    listening_ports: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    defender_data = defender.get("data") if defender.get("status") == "passed" else {}

    if defender.get("status") != "passed":
        findings.append({"severity": "warning", "area": "Defender", "message": "No se pudo consultar Windows Defender."})
    else:
        if not defender_data.get("AntivirusEnabled"):
            findings.append({"severity": "warning", "area": "Defender", "message": "Antivirus desactivado."})
        if not defender_data.get("RealTimeProtectionEnabled"):
            findings.append({"severity": "warning", "area": "Defender", "message": "Proteccion en tiempo real desactivada."})
        if defender_data.get("AntivirusEnabled") and defender_data.get("RealTimeProtectionEnabled"):
            findings.append({"severity": "ok", "area": "Defender", "message": "Antivirus y proteccion en tiempo real activos."})

    firewall_profiles = firewall.get("data") if firewall.get("status") == "passed" else []
    disabled_profiles = [profile.get("Name") for profile in firewall_profiles if not profile.get("Enabled")]
    if firewall.get("status") != "passed":
        findings.append({"severity": "warning", "area": "Firewall", "message": "No se pudo consultar firewall."})
    elif disabled_profiles:
        findings.append({"severity": "warning", "area": "Firewall", "message": f"Perfiles desactivados: {', '.join(disabled_profiles)}."})
    else:
        findings.append({"severity": "ok", "area": "Firewall", "message": "Todos los perfiles consultados estan activos."})

    admins = local_admins.get("data") or []
    if len(admins) > 2:
        findings.append({"severity": "info", "area": "Administradores", "message": f"{len(admins)} miembros en administradores locales."})

    exposed = sorted({row["port"] for row in listening_ports if row["is_common_exposed_port"]})
    if exposed:
        ports = ", ".join(str(port) for port in exposed[:12])
        findings.append({"severity": "info", "area": "Puertos", "message": f"Puertos comunes en escucha: {ports}."})
    else:
        findings.append({"severity": "ok", "area": "Puertos", "message": "No se detectaron puertos comunes expuestos en escucha."})

    return findings


def _summarize_findings(findings: list[dict[str, str]]) -> dict[str, int]:
    return {
        "ok": sum(1 for finding in findings if finding["severity"] == "ok"),
        "warning": sum(1 for finding in findings if finding["severity"] == "warning"),
        "info": sum(1 for finding in findings if finding["severity"] == "info"),
    }


def _run_powershell_json(command: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=20,
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
