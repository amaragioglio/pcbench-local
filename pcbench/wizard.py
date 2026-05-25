from __future__ import annotations

import argparse

from rich.console import Console
from rich.prompt import Confirm, Prompt


REPORT_CHOICES = {"json", "html", "docx", "md", "supabase"}
PRESETS = {
    "quick": {
        "label": "Quick scan",
        "profile": "quick",
        "scope": "core",
        "reports": ["json", "html", "md"],
        "speedtest": False,
    },
    "full": {
        "label": "Full diagnostic",
        "profile": "full",
        "scope": "all",
        "reports": ["json", "html", "docx", "md"],
        "speedtest": False,
    },
    "supabase": {
        "label": "Supabase pipeline",
        "profile": "quick",
        "scope": "core",
        "reports": ["json", "supabase"],
        "speedtest": False,
    },
    "custom": {
        "label": "Manual configuration",
        "profile": None,
        "scope": None,
        "reports": None,
        "speedtest": None,
    },
}


def configure_interactive(args: argparse.Namespace, console: Console) -> argparse.Namespace | None:
    console.print()
    console.print("[accent]PCBENCH WIZARD[/accent] [muted]// interactive configuration[/muted]")
    console.print("[muted]Available presets:[/muted]")
    console.print("  [label]quick[/label]    Quick scan: CPU/RAM/DISK + lightweight reports")
    console.print("  [label]full[/label]     Full diagnostic: every module")
    console.print("  [label]supabase[/label] Supabase pipeline: core + flat JSON")
    console.print("  [label]custom[/label]   Manual configuration")

    preset_name = Prompt.ask("Preset", choices=list(PRESETS), default="quick", console=console)
    preset = PRESETS[preset_name]

    if preset_name == "custom":
        profile = Prompt.ask("Profile", choices=["quick", "normal", "full"], default="quick", console=console)
        scope = Prompt.ask("Modules", choices=["all", "core", "custom"], default="all", console=console)
        reports = _parse_reports(Prompt.ask("Reports", default="json,html,docx,md", console=console))
        sanitize = Confirm.ask("Sanitize reports for sharing?", default=True, console=console)
        speedtest = Confirm.ask("Include speedtest? It can take longer", default=False, console=console)
    else:
        profile = preset["profile"]
        scope = preset["scope"]
        reports = list(preset["reports"])
        sanitize = preset_name == "supabase"
        speedtest = bool(preset["speedtest"])

        if Confirm.ask("Adjust this preset?", default=False, console=console):
            profile = Prompt.ask("Profile", choices=["quick", "normal", "full"], default=str(profile), console=console)
            scope = Prompt.ask("Modules", choices=["all", "core", "custom"], default=str(scope), console=console)
            reports = _parse_reports(Prompt.ask("Reports", default=",".join(reports), console=console))
            sanitize = Confirm.ask("Sanitize reports for sharing?", default=sanitize, console=console)
            speedtest = Confirm.ask("Include speedtest? It can take longer", default=speedtest, console=console)

    _apply_profile_choice(args, str(profile))
    _apply_scope_choice(args, str(scope), console)
    args.reports = ",".join(reports)
    args.no_save = False if reports else True
    args.sanitize = sanitize
    args.speedtest = speedtest

    _print_execution_plan(console, preset["label"], str(profile), str(scope), reports, args)
    if not Confirm.ask("Run now?", default=True, console=console):
        console.print("[muted]Execution cancelled by user.[/muted]")
        return None

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
        args.skip_ram = not Confirm.ask("Include RAM?", default=True, console=console)
        args.skip_cpu = not Confirm.ask("Include CPU?", default=True, console=console)
        args.skip_disk = not Confirm.ask("Include disk?", default=True, console=console)
        args.skip_network = not Confirm.ask("Include network?", default=True, console=console)
        args.skip_gpu = not Confirm.ask("Include GPU?", default=True, console=console)
        args.skip_security = not Confirm.ask("Include local security?", default=False, console=console)


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
    console.print("[accent]EXECUTION PLAN[/accent]")
    console.print(f"[label]Preset[/label]   :: {preset_label}")
    console.print(f"[label]Profile[/label]  :: {profile}")
    console.print(f"[label]Scope[/label]    :: {scope}")
    console.print(f"[label]Modules[/label]  :: {', '.join(modules)}")
    console.print(f"[label]Reports[/label]  :: {', '.join(reports) if reports else 'no reports'}")
    console.print(f"[label]Sanitize[/label] :: {'yes' if getattr(args, 'sanitize', False) else 'no'}")
    console.print(f"[label]Speedtest[/label]:: {'yes' if args.speedtest else 'no'}")


def _parse_reports(value: str) -> list[str]:
    selected = []
    for item in value.split(","):
        item = item.strip().lower()
        if item in REPORT_CHOICES and item not in selected:
            selected.append(item)
    return selected
