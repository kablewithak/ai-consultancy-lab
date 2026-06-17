from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any, Generic, Literal, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class StrictOutputModel(BaseModel):
    """Base model for deterministic output-boundary contracts.

    Extra fields are forbidden so model output cannot quietly smuggle unsupported
    keys across a software boundary.
    """

    model_config = ConfigDict(extra="forbid")


class StructuredOutputStatus(StrEnum):
    SUCCESS = "success"
    REFUSAL = "refusal"
    UNSUPPORTED = "unsupported"
    VALIDATION_ERROR = "validation_error"


class StructuredOutputErrorCode(StrEnum):
    SCHEMA_ERROR = "schema_error"
    UNSUPPORTED_ANSWER = "unsupported_answer"
    MISSING_EVIDENCE = "missing_evidence"
    LOW_CONFIDENCE = "low_confidence"
    INVALID_TOOL_CALL = "invalid_tool_call"
    REFUSAL = "refusal"
    RETRY_LIMIT_EXCEEDED = "retry_limit_exceeded"


class RetryAction(StrEnum):
    RETRY = "retry"
    DO_NOT_RETRY = "do_not_retry"
    ESCALATE = "escalate"


class BaseResult(StrictOutputModel):
    """Common metadata for structured output-boundary results."""

    trace_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    schema_name: str = Field(..., min_length=1)
    status: StructuredOutputStatus


class ValidationIssue(StrictOutputModel):
    """A single machine-readable validation issue."""

    field_path: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    error_type: str = Field(..., min_length=1)


class ValidationErrorEnvelope(BaseResult):
    """Safe validation failure envelope for model-output parsing.

    The envelope intentionally stores schema/type metadata and validation issues,
    not the raw model output. Raw model outputs may contain prompts, documents,
    customer data, or other sensitive payloads.
    """

    status: Literal[StructuredOutputStatus.VALIDATION_ERROR] = (
        StructuredOutputStatus.VALIDATION_ERROR
    )
    error_code: Literal[StructuredOutputErrorCode.SCHEMA_ERROR] = (
        StructuredOutputErrorCode.SCHEMA_ERROR
    )
    issues: tuple[ValidationIssue, ...] = Field(..., min_length=1)
    raw_output_type: str = Field(..., min_length=1)
    retryable: bool = True


class Refusal(BaseResult):
    """Explicit refusal state from a model or policy boundary."""

    status: Literal[StructuredOutputStatus.REFUSAL] = StructuredOutputStatus.REFUSAL
    error_code: Literal[StructuredOutputErrorCode.REFUSAL] = StructuredOutputErrorCode.REFUSAL
    reason: str = Field(..., min_length=1)
    retryable: bool = False


class UnsupportedAnswer(BaseResult):
    """Explicit unsupported-answer state when evidence is insufficient."""

    status: Literal[StructuredOutputStatus.UNSUPPORTED] = StructuredOutputStatus.UNSUPPORTED
    error_code: StructuredOutputErrorCode = StructuredOutputErrorCode.UNSUPPORTED_ANSWER
    reason: str = Field(..., min_length=1)
    missing_evidence: tuple[str, ...] = Field(default_factory=tuple)
    retryable: bool = False

    @model_validator(mode="after")
    def require_supported_error_code(self) -> UnsupportedAnswer:
        allowed = {
            StructuredOutputErrorCode.UNSUPPORTED_ANSWER,
            StructuredOutputErrorCode.MISSING_EVIDENCE,
            StructuredOutputErrorCode.LOW_CONFIDENCE,
        }
        if self.error_code not in allowed:
            allowed_values = ", ".join(sorted(code.value for code in allowed))
            raise ValueError(f"UnsupportedAnswer error_code must be one of: {allowed_values}")
        return self


OutputT = TypeVar("OutputT", bound=BaseModel)
FailureResult = ValidationErrorEnvelope | Refusal | UnsupportedAnswer


class OutputParseResult(StrictOutputModel, Generic[OutputT]):
    """Result of converting untrusted model output into a deterministic contract."""

    trace_id: str = Field(..., min_length=1)
    schema_name: str = Field(..., min_length=1)
    status: StructuredOutputStatus
    parsed: OutputT | None = None
    failure: FailureResult | None = None

    @model_validator(mode="after")
    def require_exactly_one_result_side(self) -> OutputParseResult[OutputT]:
        if self.status == StructuredOutputStatus.SUCCESS:
            if self.parsed is None or self.failure is not None:
                raise ValueError("success parse results require parsed output and no failure")
        else:
            if self.failure is None or self.parsed is not None:
                raise ValueError("failure parse results require failure and no parsed output")
            if self.failure.status != self.status:
                raise ValueError("parse result status must match failure status")
        return self


class RetryDecision(StrictOutputModel):
    """Machine-readable retry/escalation decision for output-boundary failures."""

    action: RetryAction
    reason: str = Field(..., min_length=1)
    attempt_number: int = Field(..., ge=1)
    max_attempts: int = Field(..., ge=1)
    retryable: bool

    @model_validator(mode="after")
    def validate_attempt_budget(self) -> RetryDecision:
        if self.attempt_number > self.max_attempts:
            raise ValueError("attempt_number cannot exceed max_attempts")
        return self


def parse_model_output(
    *,
    schema: type[OutputT],
    raw_output: Mapping[str, Any],
    trace_id: str,
    schema_name: str | None = None,
) -> OutputParseResult[OutputT]:
    """Validate raw model output into a Pydantic schema or safe error envelope."""

    resolved_schema_name = schema_name or schema.__name__

    try:
        parsed = schema.model_validate(raw_output)
    except ValidationError as exc:
        envelope = validation_error_to_envelope(
            exc,
            trace_id=trace_id,
            schema_name=resolved_schema_name,
            raw_output=raw_output,
        )
        return OutputParseResult[OutputT](
            trace_id=trace_id,
            schema_name=resolved_schema_name,
            status=StructuredOutputStatus.VALIDATION_ERROR,
            failure=envelope,
        )

    return OutputParseResult[OutputT](
        trace_id=trace_id,
        schema_name=resolved_schema_name,
        status=StructuredOutputStatus.SUCCESS,
        parsed=parsed,
    )


def validation_error_to_envelope(
    error: ValidationError,
    *,
    trace_id: str,
    schema_name: str,
    raw_output: Any,
) -> ValidationErrorEnvelope:
    """Convert a Pydantic validation error into a safe, machine-readable envelope."""

    issues = tuple(
        ValidationIssue(
            field_path=_format_location(issue.get("loc", ())),
            message=str(issue.get("msg", "validation error")),
            error_type=str(issue.get("type", "validation_error")),
        )
        for issue in error.errors()
    )

    return ValidationErrorEnvelope(
        trace_id=trace_id,
        schema_name=schema_name,
        issues=issues,
        raw_output_type=type(raw_output).__name__,
        retryable=True,
    )


def retry_decision_for_failure(
    failure: FailureResult,
    *,
    attempt_number: int,
    max_attempts: int,
) -> RetryDecision:
    """Return the next safe action for a structured-output boundary failure."""

    if attempt_number >= max_attempts:
        return RetryDecision(
            action=RetryAction.ESCALATE,
            reason="Retry limit reached; escalate instead of looping on invalid output.",
            attempt_number=attempt_number,
            max_attempts=max_attempts,
            retryable=False,
        )

    if failure.retryable:
        return RetryDecision(
            action=RetryAction.RETRY,
            reason="Failure is retryable and retry budget remains.",
            attempt_number=attempt_number,
            max_attempts=max_attempts,
            retryable=True,
        )

    return RetryDecision(
        action=RetryAction.DO_NOT_RETRY,
        reason="Failure is not retryable; escalate or return explicit unsupported/refusal state.",
        attempt_number=attempt_number,
        max_attempts=max_attempts,
        retryable=False,
    )


def _format_location(location: Sequence[Any]) -> str:
    if not location:
        return "root"
    return ".".join(str(part) for part in location)
