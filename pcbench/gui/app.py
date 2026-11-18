"""PCBench desktop window.

A local HTML page rendered by the operating system's webview (Edge WebView2 on
Windows). The page talks to Python through pywebview's JS bridge: there is no
web server and no open port.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from pcbench import __version__
from pcbench.elevation import is_windows, is_windows_admin, relaunch_elevated
from pcbench.gui.i18n import STRINGS, detect_language, t
from pcbench.gui.view_model import build_view
from pcbench.history import save_run_to_history
from pcbench.reports.json_report import save_json_report
from pcbench.reports.paths import ensure_reports_dir
from pcbench.scan import latest_saved_report, plan_steps, run_scan, save_scan

WEB_DIR = Path(__file__).with_name("web")


class Api:
    """Methods callable from JavaScript as window.pywebview.api.<name>()."""

    def __init__(self) -> None:
        self.language = detect_language()
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {"phase": "idle", "step": 0, "total": len(plan_steps()), "name": ""}
        self._report: dict[str, Any] | None = None
        self._previous: dict[str, Any] | None = latest_saved_report()
        self._saved: dict[str, str] = {}

    # ---------- setup ----------
    def init(self) -> dict[str, Any]:
        return {
            "version": __version__,
            "language": self.language,
            "strings": STRINGS,
            "is_admin": is_windows_admin(),
            "can_elevate": is_windows(),
            "steps": plan_steps(),
        }

    def set_language(self, language: str) -> dict[str, Any]:
        if language in STRINGS:
            self.language = language
        return self.status()

    # ---------- scan ----------
    def start_scan(self) -> dict[str, Any]:
        with self._lock:
            if self._state["phase"] == "running":
                return self.status()
            self._previous = latest_saved_report() or self._previous
            self._state = {"phase": "running", "step": 0, "total": len(plan_steps()), "name": "system"}
            self._saved = {}
        threading.Thread(target=self._scan, daemon=True).start()
        return self.status()

    def _scan(self) -> None:
        def progress(step: int, total: int, name: str) -> None:
            with self._lock:
                self._state.update(step=step, total=total, name=name)

        report = run_scan(progress)
        with self._lock:
            self._report = report
            self._state = {**self._state, "phase": "done"}
        # Keep a private local copy (history + JSON) to show what was fixed next time.
        try:
            save_run_to_history(report)
            save_json_report(report)
        except OSError:
            pass

    def status(self) -> dict[str, Any]:
        with self._lock:
            state = dict(self._state)
            report = self._report
        view = build_view(report, self._previous, self.language) if state["phase"] == "done" else {"state": state["phase"]}
        if state["phase"] == "running":
            state["label"] = t(self.language, "step_of", i=state["step"], n=state["total"],
                               name=t(self.language, f"step_{state['name']}"))
        return {"progress": state, "view": view, "saved": self._saved}

    # ---------- reports ----------
    def save_report(self, hide_personal: bool = True) -> dict[str, Any]:
        if not self._report:
            return {"ok": False}
        paths = save_scan(self._report, sanitize=bool(hide_personal))
        self._saved = {key: str(value) for key, value in paths.items()}
        _open_path(paths["html"])
        return {"ok": True, "paths": self._saved}

    def open_reports_folder(self) -> None:
        _open_path(ensure_reports_dir())

    def restart_as_admin(self) -> bool:
        # Frozen .exe: relaunch itself. From source: relaunch "python main.py app".
        argv = [] if getattr(sys, "frozen", False) else [str(Path(sys.argv[0]).resolve()), "app"]
        started = relaunch_elevated(argv)
        if started:
            os._exit(0)  # the elevated copy takes over
        return started


def _open_path(path: Path | str) -> None:
    path = str(path)
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606 - opens our own report/folder with the default app
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def main() -> None:
    try:
        import webview
    except ImportError:
        print("The desktop window needs pywebview: pip install pywebview")
        raise SystemExit(1)
    api = Api()
    webview.create_window(
        "PCBench Local",
        url=str(WEB_DIR / "index.html"),
        js_api=api,
        width=1120,
        height=780,
        min_size=(760, 560),
        background_color="#F1F4F7",
    )
    webview.start(private_mode=True)
