# -*- mode: python ; coding: utf-8 -*-
# Builds two executables from one analysis:
#   PCBench.exe - desktop window for everyone (no console)
#   pcbench-cli.exe - terminal CLI for technicians (distinct name: Windows paths ignore case)

from pathlib import Path


ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "pcbench" / "security" / "windows_posture.ps1"), "pcbench/security"),
        (str(ROOT / "pcbench" / "gui" / "web"), "pcbench/gui/web"),
    ],
    hiddenimports=["wmi", "pynvml", "webview", "pcbench.gui.app"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)


def build(name, console):
    return EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,  # UPX-packed binaries trigger more antivirus false positives
        upx_exclude=[],
        runtime_tmpdir=None,
        console=console,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )


app = build("PCBench", console=False)
cli = build("pcbench-cli", console=True)
