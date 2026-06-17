from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.structured_outputs import (
    RetryAction,
    StructuredOutputErrorCode,
    StructuredOutputStatus,
    ValidationErrorEnvelope,
    retry_decision_for_failure,
)
from packages.structured_outputs.examples import (
    ReliabilityRequestRoute,
    RequestClassification,
    classify_request_with_rules,
    parse_classification_model_output,
)


def test_parse_classification_model_output_accepts_valid_route() -> None:
    result = parse_classification_model_output(
        raw_output={
            "route": "rag_reliability",
            "confidence": 0.91,
            "rationale": "The request asks about retrieval misses and citations.",
            "missing_information": (),
            "requires_human_review": False,
        },
        trace_id="trace-valid-route",
    )

    assert result.status == StructuredOutputStatus.SUCCESS
    assert isinstance(result.parsed, RequestClassification)
    assert result.parsed.route == ReliabilityRequestRoute.RAG_RELIABILITY
    assert result.parsed.confidence == 0.91
    assert result.failure is None


def test_parse_classification_model_output_rejects_unknown_label() -> None:
    result = parse_classification_model_output(
        raw_output={
            "route": "random_ai_magic",
            "confidence": 0.91,
            "rationale": "Unsupported label should fail.",
            "missing_information": (),
            "requires_human_review": False,
        },
        trace_id="trace-unknown-label",
    )

    assert result.status == StructuredOutputStatus.VALIDATION_ERROR
    assert isinstance(result.failure, ValidationErrorEnvelope)
    assert any(issue.field_path == "route" for issue in result.failure.issues)


def test_parse_classification_model_output_rejects_extra_sensitive_fields_safely() -> None:
    result = parse_classification_model_output(
        raw_output={
            "route": "privacy_security",
            "confidence": 0.88,
            "rationale": "The request mentions PII in logs.",
            "missing_information": (),
            "requires_human_review": False,
            "api_key": "secret-value-that-must-not-cross-boundary",
        },
        trace_id="trace-extra-sensitive",
    )

    assert result.status == StructuredOutputStatus.VALIDATION_ERROR
    assert isinstance(result.failure, ValidationErrorEnvelope)
    assert "secret-value" not in result.failure.model_dump_json()
    assert any(issue.field_path == "api_key" for issue in result.failure.issues)


def test_parse_classification_model_output_converts_low_confidence_to_unsupported() -> None:
    result = parse_classification_model_output(
        raw_output={
            "route": "human_review",
            "confidence": 0.41,
            "rationale": "Ambiguous request.",
            "missing_information": ("clearer problem statement",),
            "requires_human_review": True,
        },
        trace_id="trace-low-confidence",
    )

    assert result.status == StructuredOutputStatus.UNSUPPORTED
    assert result.parsed is None
    assert result.failure is not None
    assert result.failure.error_code == StructuredOutputErrorCode.LOW_CONFIDENCE
    assert result.failure.retryable is False


def test_classify_request_with_rules_routes_rag_request() -> None:
    result = classify_request_with_rules(
        request_text="Our RAG keeps missing citations and retrieving the wrong document chunks.",
        trace_id="trace-rule-rag",
    )

    assert result.status == StructuredOutputStatus.SUCCESS
    assert result.parsed is not None
    assert result.parsed.route == ReliabilityRequestRoute.RAG_RELIABILITY


def test_classify_request_with_rules_routes_agent_request() -> None:
    result = classify_request_with_rules(
        request_text="The agent repeats the same tool call and gets stuck in a loop.",
        trace_id="trace-rule-agent",
    )

    assert result.status == StructuredOutputStatus.SUCCESS
    assert result.parsed is not None
    assert result.parsed.route == ReliabilityRequestRoute.AGENT_HARNESS


def test_classify_request_with_rules_escalates_ambiguous_request() -> None:
    result = classify_request_with_rules(
        request_text="Can you look at our AI thing?",
        trace_id="trace-rule-ambiguous",
    )

    assert result.status == StructuredOutputStatus.UNSUPPORTED
    assert result.failure is not None
    assert result.failure.error_code == StructuredOutputErrorCode.LOW_CONFIDENCE
    assert "clearer request text" in result.failure.missing_evidence


def test_low_confidence_unsupported_result_does_not_retry() -> None:
    result = classify_request_with_rules(
        request_text="AI issue",
        trace_id="trace-no-retry-low-confidence",
    )

    assert result.failure is not None
    decision = retry_decision_for_failure(result.failure, attempt_number=1, max_attempts=3)

    assert decision.action == RetryAction.DO_NOT_RETRY
    assert decision.retryable is False


def test_invalid_confidence_threshold_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_classification_model_output(
            raw_output={
                "route": "rag_reliability",
                "confidence": 0.91,
                "rationale": "Valid output.",
            },
            trace_id="trace-invalid-threshold",
            min_confidence=1.5,
        )


def test_request_classification_rejects_extra_fields_directly() -> None:
    with pytest.raises(ValidationError):
        RequestClassification(
            route="rag_reliability",
            confidence=0.91,
            rationale="Valid route.",
            unexpected="not allowed",
        )
