from __future__ import annotations

from typing import Any

from sie_sdk import SIEClient
from sie_sdk.types import Item

from packages.config.settings import SuperlinkedSettings
from packages.inference_clients.base import EmbeddingRequest, EmbeddingResponse


class SuperlinkedInferenceClient:
    """Superlinked-backed implementation of the provider-neutral inference client.

    This adapter is allowed to know about Superlinked.
    Core packages should depend on the provider-neutral interface instead.
    """

    provider_name = "superlinked"

    def __init__(self, settings: SuperlinkedSettings) -> None:
        self._settings = settings
        self._client = SIEClient(
            settings.sie_base_url,
            timeout_s=settings.sie_timeout_s,
            api_key=settings.api_key_value,
        )

    def encode_text(self, request: EmbeddingRequest) -> EmbeddingResponse:
        result = self._client.encode(
            request.model,
            Item(text=request.text),
            output_types=["dense"],
        )

        dense = result["dense"]
        dimensions = dense_dimensions(dense)

        return EmbeddingResponse(
            trace_id=request.trace_id,
            provider=self.provider_name,
            model=request.model,
            dense_dimensions=dimensions,
            output_types=["dense"],
        )


def dense_dimensions(dense: Any) -> int:
    """Infer embedding dimensionality from common SDK/vector return shapes."""

    if hasattr(dense, "shape"):
        shape = dense.shape
        if shape:
            return int(shape[0])

    if isinstance(dense, dict):
        if "values" in dense and hasattr(dense["values"], "__len__"):
            return len(dense["values"])
        if "dims" in dense:
            return int(dense["dims"])

    if hasattr(dense, "__len__"):
        return len(dense)

    raise ValueError(f"Could not determine dense vector dimensions from {type(dense)!r}")
