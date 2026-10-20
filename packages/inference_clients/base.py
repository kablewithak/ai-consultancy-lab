from __future__ import annotations

import math
from collections.abc import Mapping
from enum import StrEnum
from numbers import Real
from typing import Any, Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InferenceStatus(StrEnum):
    SUCCESS = "success"
    PROVIDER_ERROR = "provider_error"


class EmbeddingTask(StrEnum):
    DOCUMENT = "document"
    QUERY = "query"


class ProviderErrorCode(StrEnum):
    MODEL_LOADING = "model_loading"
    MODEL_LOAD_FAILED = "model_load_failed"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    TIMEOUT = "timeout"
    CONFIGURATION_ERROR = "configuration_error"
    AUTHENTICATION_ERROR = "authentication_error"
    QUOTA_EXHAUSTED = "quota_exhausted"
    RATE_LIMITED = "rate_limited"
    INVALID_REQUEST = "invalid_request"
    UNEXPECTED_RESPONSE = "unexpected_response"
    INTERNAL_ERROR = "internal_error"


class EmbeddingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    text: str = Field(..., min_length=1, repr=False)
    model: str = Field(..., min_length=1)
    task: EmbeddingTask = EmbeddingTask.DOCUMENT

    @field_validator("text", "model")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Embedding text and model must not be blank.")
        return normalized


class EmbeddingResponse(BaseModel):
    """Validated application vector; never serialize it into operational logs."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)  # Requested model identity.
    reported_model: str | None = None  # Explicit None if the SDK did not supply identity.
    task: EmbeddingTask = EmbeddingTask.DOCUMENT
    dense_vector: tuple[float, ...] = Field(..., min_length=1, repr=False)
    dense_dimensions: int = Field(..., ge=1)
    output_types: list[str]
    status: Literal[InferenceStatus.SUCCESS] = InferenceStatus.SUCCESS

    @field_validator("dense_vector", mode="before")
    @classmethod
    def validate_vector(cls, value: Any) -> tuple[float, ...]:
        return normalize_dense_vector(value)

    @model_validator(mode="after")
    def check_vector_identity(self) -> EmbeddingResponse:
        if len(self.dense_vector) != self.dense_dimensions:
            raise ValueError("Embedding dimensions do not match vector length.")
        if self.reported_model is not None and self.reported_model != self.model:
            raise ValueError("Provider-reported model differs from requested model.")
        if self.output_types != ["dense"]:
            raise ValueError("Only a single dense embedding output is supported.")
        return self


class InferenceProviderError(BaseModel):
    """Metadata-only error envelope. Never copy provider exception text into message."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., min_length=1)
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
        """Encode text into an application vector or a typed provider error."""


def normalize_dense_vector(value: Any) -> tuple[float, ...]:
    """Normalize one flat numeric vector; never flatten or coerce text/bools."""

    declared_dimensions: int | None = None
    if isinstance(value, Mapping):
        if "values" not in value:
            raise ValueError("Dense embedding has no vector values.")
        if "dims" in value:
            dims = value["dims"]
            if isinstance(dims, bool) or not isinstance(dims, int) or dims < 1:
                raise ValueError("Declared embedding dimension is invalid.")
            declared_dimensions = dims
        value = value["values"]

    # The SIE SDK returns numpy.ndarray; this avoids a numpy core dependency.
    if not isinstance(value, (list, tuple)):
        tolist = getattr(value, "tolist", None)
        if callable(tolist):
            value = tolist()

    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError("Dense embedding must be a nonempty one-dimensional vector.")

    values: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, Real):
            raise ValueError("Dense embedding must contain only numeric scalar values.")
        try:
            numeric = float(item)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError("Dense embedding scalar cannot be represented as a float.") from exc
        if not math.isfinite(numeric):
            raise ValueError("Dense embedding contains a non-finite value.")
        values.append(numeric)
    if declared_dimensions is not None and declared_dimensions != len(values):
        raise ValueError("Declared embedding dimension differs from vector length.")
    return tuple(values)


def inference_retry_allowed(
    error: InferenceProviderError,
    *,
    attempt_number: int,
    max_attempts: int,
    remaining_seconds: float,
) -> bool:
    """Pure policy check; this function never calls or retries a provider."""

    if attempt_number < 1 or max_attempts < 1 or attempt_number > max_attempts:
        raise ValueError("Attempt budget must be positive and consistent.")
    if not math.isfinite(remaining_seconds) or remaining_seconds < 0:
        raise ValueError("Remaining deadline must be finite and nonnegative.")
    return error.retryable and attempt_number < max_attempts and remaining_seconds > 0
