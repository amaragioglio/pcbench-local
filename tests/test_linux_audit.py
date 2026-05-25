from pcbench.security.linux_audit import _build_findings, _summarize_findings


def test_linux_findings_include_firewall_warning() -> None:
    findings = _build_findings(
        privileges={"is_root": True},
        firewall={"enabled": False, "manager": "ufw"},
        sudo_users={"count": 1},
        listening_ports=[{"port": 22, "is_common_exposed_port": True}],
        services={"status": "unavailable"},
        container={"detected": True},
    )

    summary = _summarize_findings(findings)

    assert summary["warning"] == 1
    assert any(finding["area"] == "Firewall" for finding in findings)
    assert any(finding["area"] == "Contenedor" for finding in findings)


def test_linux_findings_mark_limited_privileges() -> None:
    findings = _build_findings(
        privileges={"is_root": False},
        firewall={"enabled": True, "manager": "ufw"},
        sudo_users={"count": 0},
        listening_ports=[],
        services={"status": "passed", "active_count": 0},
        container={"detected": False},
    )

    assert any(finding["area"] == "Privilegios" and finding["severity"] == "warning" for finding in findings)
