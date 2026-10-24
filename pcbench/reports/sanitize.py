from __future__ import annotations

import copy
import hashlib
import hmac
import re
import secrets
from typing import Any

# Random key generated once per run. Tokens stay consistent inside a report
# (the same IP always maps to the same token, so readers can still correlate),
# but cannot be reversed by hashing candidate values. A plain SHA-256 of a
# private IPv4 address can be brute-forced in milliseconds.
_RUN_KEY = secrets.token_bytes(32)


SENSITIVE_KEYS = {
    "hostname": "host",
    "local_ip": "ip",
    "ip": "ip",
    "local": "endpoint",
    "remote": "endpoint",
    "user": "user",
    "users": "user",
    "command": "command",
    "test_path": "path",
}

PATH_SENSITIVE_KEYS = {
    ("security_audit", "local_admins", "data", "Name"): "principal",
    ("security_audit", "startup_items", "data", "User"): "user",
    ("security_audit", "startup_items", "data", "Command"): "command",
    ("security_audit", "sudo_users", "users"): "user",
}


def sanitize_report(report: dict[str, Any]) -> dict[str, Any]:
    sanitized = _sanitize_value(copy.deepcopy(report), ())
    if isinstance(sanitized, dict):
        sanitized["sanitized"] = True
    return sanitized


_USER_PATH = re.compile(r"(?i)((?:[a-z]:)?[\\/](?:users|home)[\\/])([^\\/\s\"']+)")
_MAC = re.compile(r"\b(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\b")


def sanitize_text(text: str) -> str:
    text = _USER_PATH.sub(lambda match: match.group(1) + _token("user", match.group(2)), text)
    text = _MAC.sub(lambda match: _token("mac", match.group(0).lower()), text)
    text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", lambda match: _token("ip", match.group(0)), text)
    text = re.sub(
        r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b",
        lambda match: _token("host", match.group(0)),
        text,
    )
    return text


def _sanitize_value(value: Any, path: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_value(item, (*path, str(key))) for key, item in value.items()}

    if isinstance(value, list):
        return [_sanitize_value(item, path) for item in value]

    label = _label_for_path(path)
    if label and value not in (None, ""):
        if isinstance(value, list):
            return [_token(label, item) for item in value]
        return _token(label, value)

    if isinstance(value, str):
        return sanitize_text(value)

    return value


def _label_for_path(path: tuple[str, ...]) -> str | None:
    normalized_path = tuple(part for part in path if not part.isdigit())
    for suffix, label in PATH_SENSITIVE_KEYS.items():
        if normalized_path[-len(suffix) :] == suffix:
            return label

    key = path[-1].lower() if path else ""
    return SENSITIVE_KEYS.get(key)


def _token(label: str, value: Any) -> str:
    digest = hmac.new(_RUN_KEY, str(value).encode("utf-8"), hashlib.sha256).hexdigest()[:12]
    return f"{label}_{digest}"
