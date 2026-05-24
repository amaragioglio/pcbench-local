from __future__ import annotations

import argparse

from rich.console import Console
from rich.prompt import Confirm, Prompt


REPORT_CHOICES = {"json", "html", "docx", "md", "supabase"}
PRESETS = {
    "quick": {
        "label": "Recon rapido",
        "profile": "quick",
        "scope": "core",
        "reports": ["json", "html", "md"],
        "speedtest": False,
    },
    "full": {
        "label": "Diagnostico completo",
        "profile": "full",
        "scope": "all",
        "reports": ["json", "html", "docx", "md"],
        "speedtest": False,
    },
    "supabase": {
        "label": "Pipeline Supabase",
        "profile": "quick",
        "scope": "core",
        "reports": ["json", "supabase"],
        "speedtest": False,
    },
    "custom": {
        "label": "Configuracion manual",
        "profile": None,
        "scope": None,
        "reports": None,
        "speedtest": None,
    },
}


def configure_interactive(args: argparse.Namespace, console: Console) -> argparse.Namespace:
    console.print()
    console.print("[accent]PCBENCH WIZARD[/accent] [muted]// configuracion interactiva[/muted]")
    console.print("[muted]Presets disponibles:[/muted]")
    console.print("  [label]quick[/label]    Recon rapido: CPU/RAM/DISCO + reportes ligeros")
    console.print("  [label]full[/label]     Diagnostico completo: todos los modulos")
    console.print("  [label]supabase[/label] Pipeline Supabase: core + JSON plano")
    console.print("  [label]custom[/label]   Configuracion manual")

    preset_name = Prompt.ask("Preset", choices=list(PRESETS), default="quick", console=console)
    preset = PRESETS[preset_name]

    if preset_name == "custom":
        profile = Prompt.ask("Perfil", choices=["quick", "normal", "full"], default="quick", console=console)
        scope = Prompt.ask("Modulos", choices=["all", "core", "custom"], default="all", console=console)
        reports = _parse_reports(Prompt.ask("Reportes", default="json,html,docx,md", console=console))
        speedtest = Confirm.ask("Incluir speedtest? puede tardar mas", default=False, console=console)
    else:
        profile = preset["profile"]
        scope = preset["scope"]
        reports = list(preset["reports"])
        speedtest = bool(preset["speedtest"])

        if Confirm.ask("Ajustar este preset?", default=False, console=console):
            profile = Prompt.ask("Perfil", choices=["quick", "normal", "full"], default=str(profile), console=console)
            scope = Prompt.ask("Modulos", choices=["all", "core", "custom"], default=str(scope), console=console)
            reports = _parse_reports(Prompt.ask("Reportes", default=",".join(reports), console=console))
            speedtest = Confirm.ask("Incluir speedtest? puede tardar mas", default=speedtest, console=console)

    _apply_profile_choice(args, str(profile))
    _apply_scope_choice(args, str(scope), console)
    args.reports = ",".join(reports)
    args.no_save = False if reports else True
    args.speedtest = speedtest

    _print_execution_plan(console, preset["label"], str(profile), str(scope), reports, args)
    if not Confirm.ask("Ejecutar ahora?", default=True, console=console):
        raise SystemExit("Ejecucion cancelada por el usuario.")

    return args


def _apply_profile_choice(args: argparse.Namespace, profile: str) -> None:
    args.quick = profile == "quick"
    args.full = profile == "full"


def _apply_scope_choice(args: argparse.Namespace, scope: str, console: Console) -> None:
    args.skip_ram = False
    args.skip_cpu = False
    args.skip_disk = False
    args.skip_network = False
    args.skip_gpu = False
    args.skip_security = False

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


def _print_execution_plan(
    console: Console,
    preset_label: str,
    profile: str,
    scope: str,
    reports: list[str],
    args: argparse.Namespace,
) -> None:
    modules = []
    for label, skipped in [
        ("RAM", args.skip_ram),
        ("CPU", args.skip_cpu),
        ("DISK", args.skip_disk),
        ("NET", args.skip_network),
        ("GPU", args.skip_gpu),
        ("SEC", args.skip_security),
    ]:
        if not skipped:
            modules.append(label)

    console.print()
    console.print("[accent]PLAN DE EJECUCION[/accent]")
    console.print(f"[label]Preset[/label]   :: {preset_label}")
    console.print(f"[label]Perfil[/label]   :: {profile}")
    console.print(f"[label]Scope[/label]    :: {scope}")
    console.print(f"[label]Modulos[/label]  :: {', '.join(modules)}")
    console.print(f"[label]Reportes[/label] :: {', '.join(reports) if reports else 'sin reportes'}")
    console.print(f"[label]Speedtest[/label]:: {'si' if args.speedtest else 'no'}")


def _parse_reports(value: str) -> list[str]:
    selected = []
    for item in value.split(","):
        item = item.strip().lower()
        if item in REPORT_CHOICES and item not in selected:
            selected.append(item)
    return selected
