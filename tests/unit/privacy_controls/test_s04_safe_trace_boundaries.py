"""S04 security regressions across structured failure and trace boundaries."""

from __future__ import annotations

import json

from packages.inference_clients.base import (
    EmbeddingRequest,
    InferenceProviderError,
    ProviderErrorCode,
)
from packages.inference_clients.factory import DisabledInferenceClient
from packages.privacy_controls.safe_logging import redact_value
from packages.trace_logging.logger import build_trace_event


def test_disabled_inference_error_does_not_include_request_text() -> None:
    private_text = "private-content-should-never-be-logged"
    request = EmbeddingRequest(trace_id="s04-private-trace", text=private_text, model="test")
    failure = DisabledInferenceClient().encode_text(request)
    assert isinstance(failure, InferenceProviderError)
    assert failure.code == ProviderErrorCode.CONFIGURATION_ERROR
    assert failure.retryable is False
    assert private_text not in failure.model_dump_json()


def test_secret_redaction_never_reveals_partial_credentials() -> None:
    assert redact_value("prefix-DONT-LEAK-suffix") == "***"
    assert redact_value(None) == ""


def test_trace_event_hides_nested_credentials_on_failure() -> None:
    secret = "private-test-token-S04-123456789"
    event = build_trace_event(
        trace_id="s04-trace",
        event_name="inference_failed",
        provider="disabled",
        payload={
            "api_key": secret,
            "nested": {"authorization": f"Bearer {secret}"},
            "status": "provider_error",
        },
    )
    parsed = json.loads(event)
    assert secret not in event
    assert parsed["payload"]["status"] == "provider_error"
    assert parsed["payload"]["api_key"] == "***"
    assert parsed["payload"]["nested"]["authorization"] == "***"


def test_trace_event_success_metadata_does_not_need_embedding_values() -> None:
    event = build_trace_event(
        trace_id="s04-success",
        event_name="inference_succeeded",
        provider="superlinked",
        payload={"model": "test-model", "dense_dimensions": 384},
    )
    parsed = json.loads(event)
    assert parsed["payload"] == {"model": "test-model", "dense_dimensions": 384}
    assert "dense_vector" not in event
