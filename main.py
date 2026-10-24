import multiprocessing as mp

from pcbench.cli import main


if __name__ == "__main__":
    mp.freeze_support()
    # The packaged PCBench.exe opens the desktop window when double-clicked;
    # pcbench-cli.exe keeps the terminal behaviour.
    import sys
    from pathlib import Path

    is_app_exe = getattr(sys, "frozen", False) and "cli" not in Path(sys.executable).stem.lower()
    if is_app_exe and len(sys.argv) == 1:
        sys.argv.append("app")
    main()
