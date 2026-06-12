from __future__ import annotations

import pytest

from packages.config.settings import SuperlinkedSettings
from packages.inference_clients.base import (
    EmbeddingRequest,
    EmbeddingResponse,
    InferenceProviderError,
    InferenceStatus,
    ProviderErrorCode,
)
from packages.inference_clients.superlinked import SuperlinkedInferenceClient, dense_dimensions


class FakeSuccessfulSIEClient:
    def encode(self, model: str, item: object, output_types: list[str]) -> dict[str, list[float]]:
        return {"dense": [0.1, 0.2, 0.3]}


class FakeModelLoadingSIEClient:
    def encode(self, model: str, item: object, output_types: list[str]) -> dict[str, object]:
        raise RuntimeError("503 Service Unavailable")


class FakeTimeoutSIEClient:
    def encode(self, model: str, item: object, output_types: list[str]) -> dict[str, object]:
        raise TimeoutError("timed out")


class FakeUnexpectedShapeSIEClient:
    def encode(self, model: str, item: object, output_types: list[str]) -> dict[str, object]:
        return {"unexpected": [0.1, 0.2]}


def test_embedding_request_rejects_blank_text() -> None:
    with pytest.raises(ValueError):
        EmbeddingRequest(text="   ", model="BAAI/bge-m3")


def test_embedding_response_contract() -> None:
    response = EmbeddingResponse(
        trace_id="trace-123",
        provider="superlinked",
        model="BAAI/bge-m3",
        dense_dimensions=1024,
        output_types=["dense"],
    )

    assert response.status == InferenceStatus.SUCCESS
    assert response.dense_dimensions == 1024


def test_inference_provider_error_contract() -> None:
    error = InferenceProviderError(
        trace_id="trace-123",
        provider="superlinked",
        model="sentence-transformers/all-MiniLM-L6-v2",
        code=ProviderErrorCode.MODEL_LOADING,
        message="Model is loading.",
        retryable=True,
        error_type="RuntimeError",
    )

    assert error.status == InferenceStatus.PROVIDER_ERROR
    assert error.retryable is True
    assert error.code == ProviderErrorCode.MODEL_LOADING


def test_superlinked_adapter_returns_success_result_from_fake_client() -> None:
    settings = SuperlinkedSettings(sie_base_url="http://localhost:8081")
    client = SuperlinkedInferenceClient(settings, sdk_client=FakeSuccessfulSIEClient())

    result = client.encode_text(
        EmbeddingRequest(
            trace_id="trace-success",
            text="hello world",
            model="sentence-transformers/all-MiniLM-L6-v2",
        )
    )

    assert isinstance(result, EmbeddingResponse)
    assert result.status == InferenceStatus.SUCCESS
    assert result.provider == "superlinked"
    assert result.dense_dimensions == 3


def test_superlinked_adapter_maps_503_to_model_loading_error() -> None:
    settings = SuperlinkedSettings(sie_base_url="http://localhost:8081")
    client = SuperlinkedInferenceClient(settings, sdk_client=FakeModelLoadingSIEClient())

    result = client.encode_text(
        EmbeddingRequest(
            trace_id="trace-loading",
            text="hello world",
            model="sentence-transformers/all-MiniLM-L6-v2",
        )
    )

    assert isinstance(result, InferenceProviderError)
    assert result.status == InferenceStatus.PROVIDER_ERROR
    assert result.code == ProviderErrorCode.MODEL_LOADING
    assert result.retryable is True
    assert result.trace_id == "trace-loading"


def test_superlinked_adapter_maps_timeout_to_retryable_error() -> None:
    settings = SuperlinkedSettings(sie_base_url="http://localhost:8081")
    client = SuperlinkedInferenceClient(settings, sdk_client=FakeTimeoutSIEClient())

    result = client.encode_text(
        EmbeddingRequest(
            trace_id="trace-timeout",
            text="hello world",
            model="sentence-transformers/all-MiniLM-L6-v2",
        )
    )

    assert isinstance(result, InferenceProviderError)
    assert result.code == ProviderErrorCode.TIMEOUT
    assert result.retryable is True


def test_superlinked_adapter_maps_unexpected_shape_to_non_retryable_error() -> None:
    settings = SuperlinkedSettings(sie_base_url="http://localhost:8081")
    client = SuperlinkedInferenceClient(settings, sdk_client=FakeUnexpectedShapeSIEClient())

    result = client.encode_text(
        EmbeddingRequest(
            trace_id="trace-shape",
            text="hello world",
            model="sentence-transformers/all-MiniLM-L6-v2",
        )
    )

    assert isinstance(result, InferenceProviderError)
    assert result.code == ProviderErrorCode.UNEXPECTED_RESPONSE
    assert result.retryable is False


def test_dense_dimensions_from_list() -> None:
    assert dense_dimensions([0.1, 0.2, 0.3]) == 3


def test_dense_dimensions_from_dict_values() -> None:
    assert dense_dimensions({"values": [0.1, 0.2]}) == 2
