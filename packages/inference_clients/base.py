from __future__ import annotations

from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class InferenceStatus(StrEnum):
    SUCCESS = "success"
    PROVIDER_ERROR = "provider_error"


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
    status: InferenceStatus = InferenceStatus.SUCCESS


class InferenceClient(Protocol):
    def encode_text(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Encode text into an embedding response."""
