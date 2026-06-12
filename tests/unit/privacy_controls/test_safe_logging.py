from __future__ import annotations

from packages.privacy_controls.safe_logging import redact_mapping
from packages.trace_logging.logger import build_trace_event


def test_redact_mapping_redacts_sensitive_fields() -> None:
    result = redact_mapping(
        {
            "sie_api_key": "super-secret-key",
            "nested": {"authorization": "Bearer abc123"},
            "safe": "visible",
        }
    )

    assert result["sie_api_key"] != "super-secret-key"
    assert result["nested"]["authorization"] != "Bearer abc123"
    assert result["safe"] == "visible"


def test_trace_event_does_not_expose_secret_payload() -> None:
    event = build_trace_event(
        trace_id="trace-123",
        event_name="test",
        provider="superlinked",
        payload={"api_key": "secret-value", "model": "BAAI/bge-m3"},
    )

    assert "secret-value" not in event
    assert "BAAI/bge-m3" in event
    assert "trace-123" in event
