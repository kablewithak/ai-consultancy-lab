"""Scripted inference fake with zero transport dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.inference_clients.base import (
    EmbeddingCallResult,
    EmbeddingRequest,
    EmbeddingResponse,
    InferenceProviderError,
    ProviderErrorCode,
)


@dataclass
class ScriptedEmbeddingClient:
    """Caller-specified test outputs; never qualifies a semantic model."""

    outcomes: dict[str, tuple[float, ...] | ProviderErrorCode]
    calls: list[EmbeddingRequest] = field(default_factory=list)

    def encode_text(self, request: EmbeddingRequest) -> EmbeddingCallResult:
        self.calls.append(request)
        outcome = self.outcomes.get(request.text)
        if outcome is None:
            return InferenceProviderError(
                trace_id=request.trace_id,
                provider="test_fake",
                model=request.model,
                code=ProviderErrorCode.INVALID_REQUEST,
                message="No scripted outcome for test request.",
                retryable=False,
            )
        if isinstance(outcome, ProviderErrorCode):
            return InferenceProviderError(
                trace_id=request.trace_id,
                provider="test_fake",
                model=request.model,
                code=outcome,
                message="Scripted test failure.",
                retryable=False,
            )
        return EmbeddingResponse(
            trace_id=request.trace_id,
            provider="test_fake",
            model=request.model,
            task=request.task,
            dense_vector=outcome,
            dense_dimensions=len(outcome),
            output_types=["dense"],
        )
