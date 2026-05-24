import argparse

from pcbench.wizard import _apply_profile_choice, _parse_reports


def test_parse_reports_filters_unknown_values() -> None:
    assert _parse_reports("json, html, bad, supabase, json") == ["json", "html", "supabase"]


def test_apply_profile_choice_sets_flags() -> None:
    args = argparse.Namespace(quick=False, full=False)
    _apply_profile_choice(args, "full")
    assert args.quick is False
    assert args.full is True
