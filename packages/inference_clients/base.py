from __future__ import annotations

from enum import StrEnum
from typing import Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class InferenceStatus(StrEnum):
    SUCCESS = "success"
    PROVIDER_ERROR = "provider_error"


class ProviderErrorCode(StrEnum):
    MODEL_LOADING = "model_loading"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    TIMEOUT = "timeout"
    CONFIGURATION_ERROR = "configuration_error"
    UNEXPECTED_RESPONSE = "unexpected_response"


class EmbeddingRequest(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)

    @field_validator("text")
    @classmethod
    def reject_suspicious_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Embedding text cannot be blank.")
        return normalized


class EmbeddingResponse(BaseModel):
    trace_id: str
    provider: str
    model: str
    dense_dimensions: int = Field(..., ge=1)
    output_types: list[str]
    status: Literal[InferenceStatus.SUCCESS] = InferenceStatus.SUCCESS


class InferenceProviderError(BaseModel):
    """Typed error envelope for provider-boundary failures.

    This object is safe to pass across the application boundary because it avoids
    raw exception strings that may contain URLs, headers, payload fragments, or
    other sensitive implementation details.
    """

    trace_id: str
    provider: str
    model: str
    code: ProviderErrorCode
    message: str
    retryable: bool
    error_type: str | None = None
    status: Literal[InferenceStatus.PROVIDER_ERROR] = InferenceStatus.PROVIDER_ERROR


EmbeddingCallResult = EmbeddingResponse | InferenceProviderError


class InferenceClient(Protocol):
    def encode_text(self, request: EmbeddingRequest) -> EmbeddingCallResult:
        """Encode text into a typed success or provider-error result."""
