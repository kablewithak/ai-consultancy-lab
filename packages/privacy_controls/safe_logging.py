from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "token",
        "secret",
        "password",
        "sie_api_key",
    }
)


def is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(sensitive in normalized for sensitive in SENSITIVE_KEYS)


def redact_value(value: Any) -> str:
    """Never preserve any prefix or suffix of a credential in operational logs."""

    if value is None:
        return ""
    return "***"


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of a mapping with sensitive values fully redacted.

    This intentionally does not mutate the original input. Callers must not
    add arbitrary raw texts, prompts or vectors as values under safe-looking keys.
    """

    redacted: dict[str, Any] = {}

    for key, value in data.items():
        if is_sensitive_key(key):
            redacted[key] = redact_value(value)
        elif isinstance(value, Mapping):
            redacted[key] = redact_mapping(value)
        else:
            redacted[key] = value

    return redacted
