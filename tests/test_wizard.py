import argparse

from pcbench.wizard import _apply_profile_choice, _parse_reports, _preset_from_choice


def test_parse_reports_filters_unknown_values() -> None:
    assert _parse_reports("json, html, bad, supabase, json") == ["json", "html", "supabase"]


def test_apply_profile_choice_sets_flags() -> None:
    args = argparse.Namespace(quick=False, full=False)
    _apply_profile_choice(args, "full")
    assert args.quick is False
    assert args.full is True


def test_preset_from_choice_maps_numbered_menu() -> None:
    assert _preset_from_choice("1") == "quick"
    assert _preset_from_choice("4") == "custom"
