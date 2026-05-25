from __future__ import annotations

import argparse
from pathlib import Path

from pcbench import __version__
from pcbench.elevation import is_windows_admin, relaunch_elevated
from pcbench.reports.compare import compare_latest_reports, compare_reports
from pcbench.runner import run_benchmarks
from pcbench.terminal_ui import build_console, print_comparison, print_header
from pcbench.wizard import configure_interactive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pcbench",
        description="Terminal-first local PC benchmark and diagnostic tool.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pcbench {__version__}",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("run", "compare", "wizard"),
        default="run",
        help="Command to run. Default: run.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick profile: reduces test duration and sizes.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full profile: increases test duration and sizes.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Runs the scan without saving report artifacts.",
    )
    parser.add_argument(
        "--reports",
        default="json,html,docx,md",
        help="Comma-separated report formats: json,html,docx,md,supabase.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where reports and logs are saved.",
    )
    parser.add_argument(
        "--keep-last",
        type=int,
        default=None,
        help="Keep only the latest N report artifacts in the output directory.",
    )
    parser.add_argument(
        "--sanitize",
        action="store_true",
        help="Sanitize hostnames, IPs, users and commands before saving reports.",
    )
    parser.add_argument(
        "--skip-ram",
        action="store_true",
        help="Skip the RAM benchmark.",
    )
    parser.add_argument(
        "--ram-mib",
        type=int,
        default=None,
        help="Maximum RAM in MiB for the test. Defaults to an automatic safe limit.",
    )
    parser.add_argument(
        "--skip-cpu",
        action="store_true",
        help="Skip the CPU benchmark.",
    )
    parser.add_argument(
        "--cpu-seconds",
        type=int,
        default=5,
        help="Duration of each CPU test in seconds. Allowed range: 1 to 60.",
    )
    parser.add_argument(
        "--skip-disk",
        action="store_true",
        help="Skip the disk benchmark.",
    )
    parser.add_argument(
        "--disk-mib",
        type=int,
        default=512,
        help="Disk test temporary file size in MiB. Allowed range: 64 to 4096.",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Skip the network benchmark.",
    )
    parser.add_argument(
        "--ping-host",
        default="1.1.1.1",
        help="Host used to measure ping latency.",
    )
    parser.add_argument(
        "--dns-host",
        default="google.com",
        help="Domain used to measure DNS resolution.",
    )
    parser.add_argument(
        "--speedtest",
        action="store_true",
        help="Include download/upload speedtest. It can take longer and requires internet.",
    )
    parser.add_argument(
        "--skip-gpu",
        action="store_true",
        help="Skip GPU detection and metrics.",
    )
    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Skip the local security audit.",
    )
    parser.add_argument(
        "--elevate",
        action="store_true",
        help="On Windows, relaunch through UAC before running.",
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=None,
        help="Base JSON report for compare.",
    )
    parser.add_argument(
        "--current",
        type=Path,
        default=None,
        help="Current JSON report for compare.",
    )
    parser.add_argument(
        "--profile",
        choices=("quick", "normal", "full"),
        default=None,
        help="Compare the two latest reports for the selected profile.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _apply_profile(args)
    console = build_console()

    if args.elevate and not is_windows_admin():
        if relaunch_elevated():
            return
        console.print("[warn]WARN[/warn] Could not request elevation. Continuing in the current session.")

    print_header(console, __version__)

    if args.command == "compare":
        if args.base and args.current:
            print_comparison(console, compare_reports(args.base, args.current))
        else:
            print_comparison(console, compare_latest_reports(args.profile, args.output_dir))
        return

    if args.command == "wizard":
        configured = configure_interactive(args, console)
        if configured is None:
            return
        args = configured
        _apply_profile(args)

    run_benchmarks(args, console)


def _apply_profile(args: argparse.Namespace) -> None:
    if args.quick:
        args.cpu_seconds = min(args.cpu_seconds, 2)
        args.disk_mib = min(args.disk_mib, 128)
        args.ram_mib = min(args.ram_mib or 256, 256)
    if args.full:
        args.cpu_seconds = max(args.cpu_seconds, 10)
        args.disk_mib = max(args.disk_mib, 1024)
        args.ram_mib = max(args.ram_mib or 2048, 2048)
