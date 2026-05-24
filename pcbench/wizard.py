from __future__ import annotations

import argparse

from rich.console import Console
from rich.prompt import Confirm, Prompt


REPORT_CHOICES = {"json", "html", "docx", "md", "supabase"}


def configure_interactive(args: argparse.Namespace, console: Console) -> argparse.Namespace:
    console.print()
    console.print("[accent]PCBENCH WIZARD[/accent] [muted]// configuracion interactiva[/muted]")

    profile = Prompt.ask("Perfil", choices=["quick", "normal", "full"], default="quick", console=console)
    args.quick = profile == "quick"
    args.full = profile == "full"

    scope = Prompt.ask("Modulos", choices=["all", "core", "custom"], default="all", console=console)
    if scope == "core":
        args.skip_network = True
        args.skip_gpu = True
        args.skip_security = True
    elif scope == "custom":
        args.skip_ram = not Confirm.ask("Incluir RAM?", default=True, console=console)
        args.skip_cpu = not Confirm.ask("Incluir CPU?", default=True, console=console)
        args.skip_disk = not Confirm.ask("Incluir disco?", default=True, console=console)
        args.skip_network = not Confirm.ask("Incluir red?", default=True, console=console)
        args.skip_gpu = not Confirm.ask("Incluir GPU?", default=True, console=console)
        args.skip_security = not Confirm.ask("Incluir seguridad local?", default=False, console=console)

    reports = Prompt.ask(
        "Reportes",
        default="json,html,docx,md",
        console=console,
    )
    selected = _parse_reports(reports)
    args.reports = ",".join(selected)
    args.no_save = False if selected else True

    if "supabase" not in selected and Confirm.ask("Generar JSON optimizado para Supabase?", default=False, console=console):
        selected.append("supabase")
        args.reports = ",".join(selected)

    if Confirm.ask("Incluir speedtest? puede tardar mas", default=False, console=console):
        args.speedtest = True

    return args


def _parse_reports(value: str) -> list[str]:
    selected = []
    for item in value.split(","):
        item = item.strip().lower()
        if item in REPORT_CHOICES and item not in selected:
            selected.append(item)
    return selected
