from pcbench.security.linux_audit import _build_findings, _summarize_findings


def test_linux_findings_include_firewall_warning() -> None:
    findings = _build_findings(
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
