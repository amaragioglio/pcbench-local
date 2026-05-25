from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import psutil


COMMON_EXPOSED_PORTS = {21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 389, 443, 445, 3389, 5432, 6379, 8000, 8080, 9200}


def run_linux_security_audit() -> dict[str, Any]:
    privileges = _collect_privileges()
    firewall = _collect_firewall_status()
    sudo_users = _collect_sudo_users()
    listening_ports = _collect_listening_ports()
    active_connections = _collect_active_connections()
    services = _collect_systemd_services()
    container = _detect_container()
    findings = _build_findings(privileges, firewall, sudo_users, listening_ports, services, container)

    return {
        "platform": "linux",
        "partial": not privileges["is_root"],
        "privileges": privileges,
        "firewall": firewall,
        "sudo_users": sudo_users,
        "listening_ports": listening_ports,
        "active_connections": active_connections,
        "services": services,
        "container": container,
        "startup_items": {"status": "not_applicable", "data": []},
        "findings": findings,
        "summary": _summarize_findings(findings),
        "notes": [
            "Auditoria Linux local de solo lectura.",
            "No modifica firewall, servicios, usuarios ni paquetes.",
            "Ejecutar con sudo puede exponer mas datos de procesos, puertos y servicios.",
        ],
    }


def _collect_privileges() -> dict[str, Any]:
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    return {
        "status": "passed",
        "is_root": is_root,
        "scope": "root" if is_root else "limited",
    }


def _collect_firewall_status() -> dict[str, Any]:
    if shutil.which("ufw"):
        completed = _run(["ufw", "status"])
        status_text = completed.get("stdout", "")
        active = "Status: active" in status_text
        return {
            "manager": "ufw",
            "status": completed["status"],
            "enabled": active if completed["status"] == "passed" else None,
            "raw": status_text[:2000],
            "error": completed.get("stderr"),
        }

    if shutil.which("firewall-cmd"):
        completed = _run(["firewall-cmd", "--state"])
        state = completed.get("stdout", "").strip()
        return {
            "manager": "firewalld",
            "status": completed["status"],
            "enabled": state == "running" if completed["status"] == "passed" else None,
            "raw": state,
            "error": completed.get("stderr"),
        }

    if shutil.which("nft"):
        completed = _run(["nft", "list", "ruleset"])
        rules = completed.get("stdout", "")
        return {
            "manager": "nftables",
            "status": completed["status"],
            "enabled": bool(rules.strip()) if completed["status"] == "passed" else None,
            "raw": rules[:2000],
            "error": completed.get("stderr"),
        }

    return {
        "manager": "unknown",
        "status": "unavailable",
        "enabled": None,
        "error": "No supported firewall command found: ufw, firewall-cmd, nft.",
    }


def _collect_sudo_users() -> dict[str, Any]:
    try:
        import grp
    except ImportError:
        return {
            "status": "unavailable",
            "groups": [],
            "users": [],
            "count": 0,
            "error": "grp module is not available on this platform.",
        }

    users = set()
    groups = []
    for group_name in ("sudo", "wheel", "admin"):
        try:
            group = grp.getgrnam(group_name)
        except KeyError:
            continue
        groups.append(group_name)
        users.update(group.gr_mem)

    return {
        "status": "passed",
        "groups": groups,
        "users": sorted(users),
        "count": len(users),
    }


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


def _collect_systemd_services() -> dict[str, Any]:
    if not shutil.which("systemctl"):
        return {
            "status": "unavailable",
            "active_count": None,
            "sample": [],
            "error": "systemctl not found.",
        }

    completed = _run(["systemctl", "list-units", "--type=service", "--state=running", "--no-pager", "--no-legend"])
    if completed["status"] != "passed":
        return {
            "status": "failed",
            "active_count": None,
            "sample": [],
            "error": completed.get("stderr") or completed.get("stdout"),
        }

    services = []
    for line in completed.get("stdout", "").splitlines():
        parts = line.split(None, 4)
        if parts:
            services.append(parts[0])

    return {
        "status": "passed",
        "active_count": len(services),
        "sample": services[:25],
    }


def _detect_container() -> dict[str, Any]:
    cgroup = Path("/proc/1/cgroup")
    docker_env = Path("/.dockerenv").exists()
    text = cgroup.read_text(encoding="utf-8", errors="ignore") if cgroup.exists() else ""
    indicators = ["docker", "containerd", "kubepods", "wsl"]
    detected = docker_env or any(indicator in text.lower() for indicator in indicators)
    return {
        "detected": detected,
        "docker_env": docker_env,
        "cgroup_hint": next((indicator for indicator in indicators if indicator in text.lower()), None),
    }


def _build_findings(
    privileges: dict[str, Any],
    firewall: dict[str, Any],
    sudo_users: dict[str, Any],
    listening_ports: list[dict[str, Any]],
    services: dict[str, Any],
    container: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if not privileges.get("is_root"):
        findings.append(
            {
                "severity": "warning",
                "area": "Privilegios",
                "message": "Auditoria ejecutada sin root/sudo; algunos datos pueden ser parciales.",
            }
        )

    if firewall.get("enabled") is True:
        findings.append({"severity": "ok", "area": "Firewall", "message": f"{firewall.get('manager')} activo."})
    elif firewall.get("enabled") is False:
        findings.append({"severity": "warning", "area": "Firewall", "message": f"{firewall.get('manager')} no esta activo."})
    else:
        findings.append({"severity": "info", "area": "Firewall", "message": "No se pudo determinar el firewall activo."})

    sudo_count = sudo_users.get("count", 0)
    if sudo_count > 0:
        findings.append({"severity": "info", "area": "Sudo", "message": f"{sudo_count} usuario(s) en grupos sudo/wheel/admin."})
    else:
        findings.append({"severity": "ok", "area": "Sudo", "message": "No se detectaron usuarios en grupos sudo/wheel/admin."})

    exposed = sorted({row["port"] for row in listening_ports if row["is_common_exposed_port"]})
    if exposed:
        ports = ", ".join(str(port) for port in exposed[:16])
        findings.append({"severity": "info", "area": "Puertos", "message": f"Puertos comunes en escucha: {ports}."})
    else:
        findings.append({"severity": "ok", "area": "Puertos", "message": "No se detectaron puertos comunes expuestos en escucha."})

    if services.get("status") == "passed":
        findings.append({"severity": "info", "area": "Servicios", "message": f"{services.get('active_count', 0)} servicios systemd activos."})
    else:
        findings.append({"severity": "info", "area": "Servicios", "message": "systemd no disponible o no consultable."})

    if container.get("detected"):
        findings.append({"severity": "info", "area": "Contenedor", "message": "Entorno de contenedor/WSL detectado; hardware y seguridad pueden diferir del host."})

    return findings


def _summarize_findings(findings: list[dict[str, str]]) -> dict[str, int]:
    return {
        "ok": sum(1 for finding in findings if finding["severity"] == "ok"),
        "warning": sum(1 for finding in findings if finding["severity"] == "warning"),
        "info": sum(1 for finding in findings if finding["severity"] == "info"),
    }


def _run(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "status": "failed",
            "stdout": "",
            "stderr": str(error),
        }

    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }
