from __future__ import annotations

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from packages.structured_outputs import (
    OutputParseResult,
    Refusal,
    RetryAction,
    StructuredOutputErrorCode,
    StructuredOutputStatus,
    UnsupportedAnswer,
    ValidationErrorEnvelope,
    parse_model_output,
    retry_decision_for_failure,
)


class DemoAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0, le=1)


def test_parse_model_output_returns_typed_success_result() -> None:
    result = parse_model_output(
        schema=DemoAnswer,
        raw_output={"answer": "Use a schema boundary.", "confidence": 0.91},
        trace_id="trace-success",
    )

    assert result.status == StructuredOutputStatus.SUCCESS
    assert isinstance(result.parsed, DemoAnswer)
    assert result.parsed.answer == "Use a schema boundary."
    assert result.failure is None


def test_parse_model_output_rejects_extra_fields_safely() -> None:
    result = parse_model_output(
        schema=DemoAnswer,
        raw_output={
            "answer": "Use a schema boundary.",
            "confidence": 0.91,
            "api_key": "secret-value-that-must-not-cross-the-boundary",
        },
        trace_id="trace-extra",
    )

    assert result.status == StructuredOutputStatus.VALIDATION_ERROR
    assert isinstance(result.failure, ValidationErrorEnvelope)
    assert result.failure.error_code == StructuredOutputErrorCode.SCHEMA_ERROR
    assert result.failure.raw_output_type == "dict"
    assert result.parsed is None
    assert "secret-value" not in result.failure.model_dump_json()
    assert any(issue.field_path == "api_key" for issue in result.failure.issues)


def test_parse_model_output_rejects_invalid_confidence() -> None:
    result = parse_model_output(
        schema=DemoAnswer,
        raw_output={"answer": "Too confident.", "confidence": 1.7},
        trace_id="trace-confidence",
    )

    assert result.status == StructuredOutputStatus.VALIDATION_ERROR
    assert isinstance(result.failure, ValidationErrorEnvelope)
    assert any(issue.field_path == "confidence" for issue in result.failure.issues)


def test_refusal_is_explicit_non_retryable_state() -> None:
    refusal = Refusal(
        trace_id="trace-refusal",
        schema_name="DemoAnswer",
        reason="The request violates the policy boundary.",
    )

    assert refusal.status == StructuredOutputStatus.REFUSAL
    assert refusal.error_code == StructuredOutputErrorCode.REFUSAL
    assert refusal.retryable is False


def test_unsupported_answer_captures_missing_evidence() -> None:
    unsupported = UnsupportedAnswer(
        trace_id="trace-unsupported",
        schema_name="DemoAnswer",
        reason="The retrieved context does not support an answer.",
        error_code=StructuredOutputErrorCode.MISSING_EVIDENCE,
        missing_evidence=("source citation", "freshness metadata"),
    )

    assert unsupported.status == StructuredOutputStatus.UNSUPPORTED
    assert unsupported.retryable is False
    assert unsupported.missing_evidence == ("source citation", "freshness metadata")


def test_unsupported_answer_rejects_wrong_error_code() -> None:
    with pytest.raises(ValidationError):
        UnsupportedAnswer(
            trace_id="trace-invalid-code",
            schema_name="DemoAnswer",
            reason="Unsupported answer.",
            error_code=StructuredOutputErrorCode.INVALID_TOOL_CALL,
        )


def test_output_parse_result_requires_success_to_have_parsed_output() -> None:
    with pytest.raises(ValidationError):
        OutputParseResult[DemoAnswer](
            trace_id="trace-bad-success",
            schema_name="DemoAnswer",
            status=StructuredOutputStatus.SUCCESS,
        )


def test_output_parse_result_requires_failure_status_to_match_failure() -> None:
    refusal = Refusal(
        trace_id="trace-refusal",
        schema_name="DemoAnswer",
        reason="Refused.",
    )

    with pytest.raises(ValidationError):
        OutputParseResult[DemoAnswer](
            trace_id="trace-mismatch",
            schema_name="DemoAnswer",
            status=StructuredOutputStatus.UNSUPPORTED,
            failure=refusal,
        )


def test_retry_decision_retries_retryable_validation_errors() -> None:
    result = parse_model_output(
        schema=DemoAnswer,
        raw_output={"answer": "Bad confidence", "confidence": 2.0},
        trace_id="trace-retry",
    )

    assert result.failure is not None
    decision = retry_decision_for_failure(result.failure, attempt_number=1, max_attempts=3)

    assert decision.action == RetryAction.RETRY
    assert decision.retryable is True


def test_retry_decision_escalates_when_retry_limit_is_reached() -> None:
    result = parse_model_output(
        schema=DemoAnswer,
        raw_output={"answer": "Bad confidence", "confidence": 2.0},
        trace_id="trace-escalate",
    )

    assert result.failure is not None
    decision = retry_decision_for_failure(result.failure, attempt_number=3, max_attempts=3)

    assert decision.action == RetryAction.ESCALATE
    assert decision.retryable is False


def test_retry_decision_does_not_retry_refusals() -> None:
    refusal = Refusal(
        trace_id="trace-refusal",
        schema_name="DemoAnswer",
        reason="Refused.",
    )

    decision = retry_decision_for_failure(refusal, attempt_number=1, max_attempts=3)

    assert decision.action == RetryAction.DO_NOT_RETRY
    assert decision.retryable is False
