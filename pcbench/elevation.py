from __future__ import annotations

import ctypes
import platform
import subprocess
import sys


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_windows_admin() -> bool:
    if not is_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def relaunch_elevated(argv: list[str] | None = None) -> bool:
    if not is_windows():
        return False

    args = argv if argv is not None else sys.argv
    parameters = subprocess.list2cmdline(args)
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, parameters, None, 1)
    return result > 32
