from pcbench.reports.sanitize import sanitize_report


def test_sanitize_report_redacts_shareable_identifiers() -> None:
    report = {
        "tool": "pcbench-local",
        "results": {
            "system_info": {
                "machine": {"hostname": "andres-pc", "os": "Windows"},
                "network": {"hostname": "andres-pc", "local_ip": "192.168.1.50"},
            },
            "disk_benchmark": {
                "test_path": "C:\\Users\\andres\\AppData\\Local\\Temp\\pcbench-local\\disk_benchmark.tmp",
            },
            "security_audit": {
                "local_admins": {
                    "data": [{"Name": "DESKTOP\\andres", "ObjectClass": "User"}],
                },
                "startup_items": {
                    "data": [{"User": "andres", "Command": "C:\\Users\\andres\\AppData\\tool.exe"}],
                },
                "listening_ports": [{"ip": "0.0.0.0", "port": 3389}],
                "active_connections": {
                    "sample": [{"local": "192.168.1.50:51000", "remote": "93.184.216.34:443"}],
                },
                "sudo_users": {"users": ["andres"]},
            },
        },
    }

    sanitized = sanitize_report(report)
    rendered = str(sanitized)

    assert sanitized["sanitized"] is True
    assert "andres-pc" not in rendered
    assert "192.168.1.50" not in rendered
    assert "DESKTOP\\andres" not in rendered
    assert "C:\\Users\\andres" not in rendered
    assert "93.184.216.34" not in rendered
    assert sanitized["results"]["system_info"]["machine"]["hostname"].startswith("host_")
