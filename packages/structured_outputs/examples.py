from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import Field

from packages.structured_outputs.contracts import (
    OutputParseResult,
    StrictOutputModel,
    StructuredOutputErrorCode,
    StructuredOutputStatus,
    UnsupportedAnswer,
    parse_model_output,
)


class ReliabilityRequestRoute(StrEnum):
    """Small route taxonomy for AI reliability request classification demos."""

    RAG_RELIABILITY = "rag_reliability"
    AGENT_HARNESS = "agent_harness"
    EVAL_HARNESS = "eval_harness"
    PRIVACY_SECURITY = "privacy_security"
    STRUCTURED_OUTPUTS = "structured_outputs"
    HUMAN_REVIEW = "human_review"


class RequestClassification(StrictOutputModel):
    """Structured output for routing an AI reliability request."""

    route: ReliabilityRequestRoute
    confidence: float = Field(..., ge=0, le=1)
    rationale: str = Field(..., min_length=1)
    missing_information: tuple[str, ...] = Field(default_factory=tuple)
    requires_human_review: bool = False


def parse_classification_model_output(
    *,
    raw_output: Mapping[str, Any],
    trace_id: str,
    min_confidence: float = 0.70,
) -> OutputParseResult[RequestClassification]:
    """Validate classifier-like model output and fail safely when confidence is low.

    This is intentionally small: it demonstrates how a future LLM classifier,
    router, RAG answerer, or agent tool planner should cross the software
    boundary. The raw output is validated into a strict Pydantic contract, and
    low-confidence outputs become explicit unsupported states instead of quiet
    guesses.
    """

    if min_confidence < 0 or min_confidence > 1:
        raise ValueError("min_confidence must be between 0 and 1")

    result = parse_model_output(
        schema=RequestClassification,
        raw_output=raw_output,
        trace_id=trace_id,
        schema_name="RequestClassification",
    )

    if result.status != StructuredOutputStatus.SUCCESS:
        return result

    classification = result.parsed
    if classification is None:
        raise RuntimeError("success parse result unexpectedly had no parsed classification")

    if classification.confidence < min_confidence:
        return OutputParseResult[RequestClassification](
            trace_id=trace_id,
            schema_name="RequestClassification",
            status=StructuredOutputStatus.UNSUPPORTED,
            failure=UnsupportedAnswer(
                trace_id=trace_id,
                schema_name="RequestClassification",
                error_code=StructuredOutputErrorCode.LOW_CONFIDENCE,
                reason=(
                    f"Classification confidence {classification.confidence:.2f} is below "
                    f"the required threshold {min_confidence:.2f}."
                ),
                missing_evidence=("clearer request text", "stronger route evidence"),
            ),
        )

    return result


def classify_request_with_rules(
    *,
    request_text: str,
    trace_id: str,
    min_confidence: float = 0.70,
) -> OutputParseResult[RequestClassification]:
    """Deterministic local classifier demo using the same output boundary.

    This is not claiming to be a good production classifier. It exists to prove
    the structured-output contract can be used by an applied component and that
    ambiguous requests escalate instead of receiving unsupported certainty.
    """

    raw_output = _rule_based_raw_classification(request_text)
    return parse_classification_model_output(
        raw_output=raw_output,
        trace_id=trace_id,
        min_confidence=min_confidence,
    )


def _rule_based_raw_classification(request_text: str) -> dict[str, Any]:
    text = request_text.strip().lower()

    if not text:
        return {
            "route": ReliabilityRequestRoute.HUMAN_REVIEW.value,
            "confidence": 0.0,
            "rationale": "No request text was provided.",
            "missing_information": ("request_text",),
            "requires_human_review": True,
        }

    route_keywords: tuple[tuple[ReliabilityRequestRoute, float, tuple[str, ...]], ...] = (
        (
            ReliabilityRequestRoute.RAG_RELIABILITY,
            0.86,
            ("rag", "retrieval", "chunk", "citation", "grounding", "document"),
        ),
        (
            ReliabilityRequestRoute.AGENT_HARNESS,
            0.84,
            ("agent", "tool call", "loop", "action", "trajectory", "escalation"),
        ),
        (
            ReliabilityRequestRoute.EVAL_HARNESS,
            0.83,
            ("eval", "evaluation", "baseline", "score", "failure taxonomy", "test case"),
        ),
        (
            ReliabilityRequestRoute.PRIVACY_SECURITY,
            0.82,
            ("privacy", "pii", "gdpr", "popia", "redact", "secret", "logs"),
        ),
        (
            ReliabilityRequestRoute.STRUCTURED_OUTPUTS,
            0.82,
            ("schema", "pydantic", "structured", "json", "validation"),
        ),
    )

    for route, confidence, keywords in route_keywords:
        if any(keyword in text for keyword in keywords):
            return {
                "route": route.value,
                "confidence": confidence,
                "rationale": f"Request contains terms associated with {route.value}.",
                "missing_information": (),
                "requires_human_review": False,
            }

    return {
        "route": ReliabilityRequestRoute.HUMAN_REVIEW.value,
        "confidence": 0.45,
        "rationale": "No reliable route-specific signals were detected.",
        "missing_information": ("clearer problem statement", "affected AI system boundary"),
        "requires_human_review": True,
    }
