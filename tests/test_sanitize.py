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


def test_sanitized_tokens_cannot_be_reversed_by_hashing() -> None:
    import hashlib

    report = {"results": {"system_info": {"network": {"local_ip": "192.168.1.57"}}}}
    token = sanitize_report(report)["results"]["system_info"]["network"]["local_ip"]
    digest = token.split("_", 1)[1]
    candidates = (f"192.168.{c}.{d}" for c in range(256) for d in range(256))
    assert not any(hashlib.sha256(ip.encode()).hexdigest()[:12] == digest for ip in candidates)


def test_sanitized_tokens_are_consistent_within_a_run() -> None:
    report = {"a": {"hostname": "andres-pc"}, "b": {"hostname": "andres-pc"}}
    sanitized = sanitize_report(report)
    assert sanitized["a"]["hostname"] == sanitized["b"]["hostname"]


def test_sanitize_text_hides_user_folders_and_mac_addresses() -> None:
    from pcbench.reports.sanitize import sanitize_text

    text = sanitize_text(r"C:\Users\andres\AppData\x.exe /home/andres/.cache aa:bb:cc:dd:ee:ff")
    assert "andres" not in text
    assert "aa:bb:cc:dd:ee:ff" not in text
