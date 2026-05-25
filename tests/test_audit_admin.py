from pcbench.security.audit import _build_findings


def test_windows_findings_mark_limited_privileges() -> None:
    findings = _build_findings(
        privileges={"is_admin": False},
        defender={"status": "passed", "data": {"AntivirusEnabled": True, "RealTimeProtectionEnabled": True}},
        firewall={"status": "passed", "data": [{"Name": "Domain", "Enabled": True}]},
        local_admins={"status": "passed", "data": []},
        listening_ports=[],
    )

    assert any(finding["area"] == "Privileges" and finding["severity"] == "warning" for finding in findings)
