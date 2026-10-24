from pcbench.security.advice import ADVICE, advice_for
from pcbench.security.audit import _av_state, build_windows_findings

HEALTHY = {
    "antivirus_products": [{"name": "Windows Defender", "state": 397568}],  # 0x061100: on, up to date
    "defender": {"antivirus_enabled": True, "realtime_enabled": True, "tamper_protected": True,
                 "signature_age_days": 1},
    "last_update_days": 10, "uac_enabled": 1, "uac_admin_prompt": 5, "guest_enabled": False,
    "autologon_enabled": False, "rdp_enabled": False, "smb1_server": False, "smb1_client": False,
    "secure_boot": 1, "bitlocker": {"protection_on": True}, "smartscreen": "Warn",
}
FIREWALL_ON = {"status": "passed", "data": [{"Name": n, "Enabled": True} for n in ("Domain", "Private", "Public")]}


def _ids(findings, severity=None):
    return {f["id"] for f in findings if severity is None or f["severity"] == severity}


def _run(posture=None, firewall=FIREWALL_ON, admin=True, ports=()):
    return build_windows_findings({"is_admin": admin}, {**HEALTHY, **(posture or {})}, firewall,
                                  {"status": "passed", "data": []}, list(ports))


def test_healthy_pc_has_no_problems() -> None:
    findings = _run()
    assert not _ids(findings, "critical") and not _ids(findings, "warning")
    assert {"av_ok", "firewall_ok", "updates_ok"} <= _ids(findings, "ok")


def test_third_party_antivirus_is_not_a_false_alarm() -> None:
    findings = _run({"antivirus_products": [{"name": "ESET Security", "state": 266240}],  # 0x041000
                     "defender": {"antivirus_enabled": False, "realtime_enabled": False}})
    assert "av_off" not in _ids(findings)
    assert "av_ok" in _ids(findings, "ok")


def test_no_antivirus_is_critical() -> None:
    findings = _run({"antivirus_products": [{"name": "Windows Defender", "state": 393472}],  # 0x060100: off
                     "defender": {"antivirus_enabled": False, "realtime_enabled": False}})
    assert "av_off" in _ids(findings, "critical")


def test_dangerous_settings_are_flagged() -> None:
    findings = _run({"uac_enabled": 0, "rdp_enabled": True, "rdp_nla": False, "smb1_server": True,
                     "autologon_enabled": True, "autologon_password_stored": True, "last_update_days": 200})
    assert {"uac_off", "rdp_no_nla", "smb1_on", "autologon_password", "updates_old"} <= _ids(findings, "critical")


def test_public_firewall_off_is_critical() -> None:
    firewall = {"status": "passed", "data": [{"Name": "Public", "Enabled": False}, {"Name": "Private", "Enabled": True}]}
    assert "firewall_off" in _ids(_run(firewall=firewall), "critical")


def test_unencrypted_laptop_warns_but_desktop_only_informs() -> None:
    laptop = _run({"bitlocker": {"protection_on": False}, "is_laptop": True})
    desktop = _run({"bitlocker": {"protection_on": False}, "is_laptop": False})
    assert "disk_not_encrypted" in _ids(laptop, "warning")
    assert "disk_not_encrypted" in _ids(desktop, "info")


def test_limited_privileges_is_info_not_a_security_problem() -> None:
    findings = _run(admin=False)
    assert "partial_scan" in _ids(findings, "info")
    assert not _ids(findings, "warning")


def test_loopback_only_ports_are_not_exposed() -> None:
    local = _run(ports=[{"ip": "127.0.0.1", "port": 445, "is_common_exposed_port": True}])
    lan = _run(ports=[{"ip": "0.0.0.0", "port": 445, "is_common_exposed_port": True}])
    assert "ports_exposed" not in _ids(local)
    assert "ports_exposed" in _ids(lan)


def test_av_state_decoding() -> None:
    assert _av_state(397568) == (True, True)    # 0x061100
    assert _av_state(397584) == (True, False)   # 0x061110: definitions out of date
    assert _av_state(393472) == (False, True)   # 0x060100: off


def test_every_windows_finding_has_spanish_and_english_advice() -> None:
    findings = _run({"uac_enabled": 0, "guest_enabled": True, "rdp_enabled": True, "smb1_server": True,
                     "secure_boot": 0, "smartscreen": "Off", "reboot_pending": True,
                     "bitlocker": {"protection_on": False}, "is_laptop": True,
                     "defender": {"antivirus_enabled": True, "realtime_enabled": True, "tamper_protected": False,
                                  "signature_age_days": 30}},
                    admin=False, ports=[{"ip": "0.0.0.0", "port": 3389, "is_common_exposed_port": True}])
    for finding in findings:
        if finding["id"] == "many_admins":
            continue
        assert finding["id"] in ADVICE, finding["id"]
        for language in ("en", "es"):
            text = advice_for(finding, language)
            assert text["title"] and text["why"]
            if finding["severity"] in ("critical", "warning"):
                assert text["fix"], (finding["id"], language)
