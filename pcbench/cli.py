from __future__ import annotations

import argparse

from pcbench import __version__
from pcbench.reports.compare import compare_latest_reports
from pcbench.runner import run_benchmarks
from pcbench.terminal_ui import build_console, print_comparison, print_header


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pcbench",
        description="Benchmark y diagnostico local de PC desde la terminal.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("run", "compare"),
        default="run",
        help="Comando a ejecutar. Por defecto: run.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Perfil rapido: reduce duracion y tamanos de prueba.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Perfil completo: aumenta duracion y tamanos de prueba.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Ejecuta el analisis inicial sin guardar reporte JSON.",
    )
    parser.add_argument(
        "--skip-ram",
        action="store_true",
        help="Omite el benchmark de RAM.",
    )
    parser.add_argument(
        "--ram-mib",
        type=int,
        default=None,
        help="Cantidad maxima de RAM en MiB para la prueba. Por defecto usa un limite seguro automatico.",
    )
    parser.add_argument(
        "--skip-cpu",
        action="store_true",
        help="Omite el benchmark de CPU.",
    )
    parser.add_argument(
        "--cpu-seconds",
        type=int,
        default=5,
        help="Duracion de cada prueba CPU en segundos. Rango permitido: 1 a 60.",
    )
    parser.add_argument(
        "--skip-disk",
        action="store_true",
        help="Omite el benchmark de disco.",
    )
    parser.add_argument(
        "--disk-mib",
        type=int,
        default=512,
        help="Tamano del archivo temporal de prueba de disco en MiB. Rango permitido: 64 a 4096.",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Omite el benchmark de red.",
    )
    parser.add_argument(
        "--ping-host",
        default="1.1.1.1",
        help="Host usado para medir latencia con ping.",
    )
    parser.add_argument(
        "--dns-host",
        default="google.com",
        help="Dominio usado para medir resolucion DNS.",
    )
    parser.add_argument(
        "--speedtest",
        action="store_true",
        help="Incluye prueba de descarga/subida. Puede tardar mas y requiere internet.",
    )
    parser.add_argument(
        "--skip-gpu",
        action="store_true",
        help="Omite deteccion y metricas de GPU.",
    )
    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Omite auditoria local de seguridad.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _apply_profile(args)
    console = build_console()

    print_header(console, __version__)

    if args.command == "compare":
        print_comparison(console, compare_latest_reports())
        return

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
