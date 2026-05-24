from pcbench.wizard import _parse_reports


def test_parse_reports_filters_unknown_values() -> None:
    assert _parse_reports("json, html, bad, supabase, json") == ["json", "html", "supabase"]
