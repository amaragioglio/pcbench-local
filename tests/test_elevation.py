from pcbench import elevation


def test_is_windows_admin_false_on_non_windows(monkeypatch) -> None:
    monkeypatch.setattr(elevation.platform, "system", lambda: "Linux")

    assert elevation.is_windows_admin() is False


def test_relaunch_elevated_skips_non_windows(monkeypatch) -> None:
    monkeypatch.setattr(elevation.platform, "system", lambda: "Linux")

    assert elevation.relaunch_elevated(["main.py", "run"]) is False
