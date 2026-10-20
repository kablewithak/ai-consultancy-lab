from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
from pydantic import ValidationError
from sie_sdk.client.errors import (
    ModelLoadingError,
    ProvisioningError,
    RequestError,
    SIEConnectionError,
    SIEError,
    ServerError,
)

from packages.config.settings import SuperlinkedSettings
from packages.inference_clients.base import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingTask,
    InferenceProviderError,
    InferenceStatus,
    ProviderErrorCode,
    inference_retry_allowed,
    normalize_dense_vector,
)
from packages.inference_clients.superlinked import SuperlinkedInferenceClient, dense_dimensions


class FakeSIEClient:
    def __init__(self, *, result: Any = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def encode(self, model: str, item: object, **options: Any) -> Any:
        self.calls.append((model, options))
        if self.error is not None:
            raise self.error
        return self.result


class FakeSDKRequestError(RequestError):
    def __init__(self, status: int, code: str):
        Exception.__init__(self, "sensitive.example token=do-not-log")
        self.status_code = status
        self.code = code


class FakeSDKServerError(ServerError):
    def __init__(self, status: int, code: str):
        Exception.__init__(self, "https://sensitive.example?api_key=secret")
        self.status_code = status
        self.code = code


class FakeSDKLoadingError(ModelLoadingError):
    def __init__(self):
        Exception.__init__(self, "sensitive model error")


class FakeSDKConnectionError(SIEConnectionError):
    def __init__(self):
        Exception.__init__(self, "sensitive connection error")


class FakeSDKProvisioningError(ProvisioningError):
    def __init__(self):
        Exception.__init__(self, "sensitive provisioning error")


class FakeUnknownSDKError(SIEError):
    def __init__(self):
        Exception.__init__(self, "unknown sensitive provider condition")


def build_client(*, result: Any = None, error: Exception | None = None):
    sdk = FakeSIEClient(result=result, error=error)
    settings = SuperlinkedSettings(sie_base_url="http://localhost:8081")
    return SuperlinkedInferenceClient(settings, sdk_client=sdk), sdk


def request(task: EmbeddingTask = EmbeddingTask.DOCUMENT) -> EmbeddingRequest:
    return EmbeddingRequest(trace_id="trace-s02", text="hello world", model="test/model", task=task)


def test_request_trims_text_and_rejects_blank_text() -> None:
    assert EmbeddingRequest(text=" hello ", model=" x ").text == "hello"
    with pytest.raises(ValidationError):
        EmbeddingRequest(text="  ", model="test/model")
    with pytest.raises(ValidationError):
        EmbeddingRequest(text="valid", model=" ")


def test_embedding_contract_contains_numeric_vector_and_matching_dimensions() -> None:
    response = EmbeddingResponse(
        trace_id="trace",
        provider="superlinked",
        model="test/model",
        task=EmbeddingTask.DOCUMENT,
        dense_vector=(0.1, 0.2),
        dense_dimensions=2,
        output_types=["dense"],
    )
    assert response.status == InferenceStatus.SUCCESS
    assert response.dense_vector == (0.1, 0.2)
    assert response.reported_model is None


def test_response_rejects_dimension_mismatch() -> None:
    with pytest.raises(ValidationError):
        EmbeddingResponse(
            trace_id="trace",
            provider="superlinked",
            model="test/model",
            dense_vector=(1.0, 2.0),
            dense_dimensions=3,
            output_types=["dense"],
        )


@pytest.mark.parametrize(
    "value",
    [
        [],
        [[1.0, 2.0]],
        [[1.0], [2.0]],
        [True, 0.1],
        ["1.2", 0.1],
        [None, 0.1],
        [math.nan],
        [math.inf],
        [-math.inf],
        3,
        {"dims": 3},
        {"values": []},
        {"dims": 3, "values": [0.1, 0.2]},
        {"dims": True, "values": [0.1]},
        [10**1000],
    ],
)
def test_vector_rejects_invalid_values(value: Any) -> None:
    with pytest.raises(ValueError):
        normalize_dense_vector(value)


def test_vector_accepts_numpy_dense_values_without_leaking_numpy_types() -> None:
    vector = normalize_dense_vector(np.array([0.25, -0.5], dtype=np.float32))
    assert isinstance(vector, tuple)
    assert all(isinstance(x, float) for x in vector)
    assert vector == (0.25, -0.5)
    assert dense_dimensions({"values": [0.1, 0.2]}) == 2
    assert dense_dimensions({"dims": 2, "values": [0.1, 0.2]}) == 2


def test_success_preserves_identity_vector_trace_and_single_sdk_call() -> None:
    client, sdk = build_client(result={"dense": np.array([0.1, 0.2]), "model": "test/model"})
    response = client.encode_text(request())
    assert isinstance(response, EmbeddingResponse)
    assert response.dense_vector == pytest.approx((0.1, 0.2))
    assert response.dense_dimensions == 2
    assert response.reported_model == "test/model"
    assert response.task == EmbeddingTask.DOCUMENT
    assert response.trace_id == "trace-s02"
    assert sdk.calls == [("test/model", {"output_types": ["dense"]})]


def test_query_passes_explicit_sdk_task_flag_once() -> None:
    client, sdk = build_client(result={"dense": [0.1]})
    response = client.encode_text(request(EmbeddingTask.QUERY))
    assert isinstance(response, EmbeddingResponse)
    assert response.task == EmbeddingTask.QUERY
    assert sdk.calls == [("test/model", {"output_types": ["dense"], "is_query": True})]


@pytest.mark.parametrize(
    "result",
    [
        {},
        {"dense": [0.5], "model": "wrong/model"},
        {"dense": [0.5], "model": 1},
        {"dense": [[0.1, 0.2]]},
        {"dense": [float("nan")]},
        {"dense": {"dims": 384}},
        [{"dense": [0.5]}],
    ],
)
def test_invalid_sdk_results_become_non_retryable_errors(result: Any) -> None:
    client, sdk = build_client(result=result)
    response = client.encode_text(request())
    assert isinstance(response, InferenceProviderError)
    assert response.code == ProviderErrorCode.UNEXPECTED_RESPONSE
    assert response.retryable is False
    assert len(sdk.calls) == 1


@pytest.mark.parametrize(
    ("error", "expected_code", "expected_retry"),
    [
        (FakeSDKRequestError(400, "BAD_INPUT"), ProviderErrorCode.INVALID_REQUEST, False),
        (FakeSDKRequestError(401, "UNAUTHORIZED"), ProviderErrorCode.AUTHENTICATION_ERROR, False),
        (FakeSDKRequestError(403, "FORBIDDEN"), ProviderErrorCode.AUTHENTICATION_ERROR, False),
        (
            FakeSDKRequestError(402, "INSUFFICIENT_CREDITS"),
            ProviderErrorCode.QUOTA_EXHAUSTED,
            False,
        ),
        (FakeSDKRequestError(429, "RATE_LIMIT"), ProviderErrorCode.RATE_LIMITED, True),
        (FakeSDKServerError(503, "OTHER"), ProviderErrorCode.PROVIDER_UNAVAILABLE, True),
        (FakeSDKServerError(503, "MODEL_LOADING"), ProviderErrorCode.MODEL_LOADING, True),
        (FakeSDKServerError(502, "MODEL_LOAD_FAILED"), ProviderErrorCode.MODEL_LOAD_FAILED, False),
        (
            FakeSDKServerError(503, "RESOURCE_EXHAUSTED"),
            ProviderErrorCode.RESOURCE_EXHAUSTED,
            False,
        ),
        (FakeSDKServerError(504, "GATEWAY_TIMEOUT"), ProviderErrorCode.TIMEOUT, True),
        (FakeSDKLoadingError(), ProviderErrorCode.MODEL_LOADING, True),
        (FakeSDKConnectionError(), ProviderErrorCode.PROVIDER_UNAVAILABLE, True),
        (FakeSDKProvisioningError(), ProviderErrorCode.PROVIDER_UNAVAILABLE, True),
        (FakeUnknownSDKError(), ProviderErrorCode.INTERNAL_ERROR, False),
        (TimeoutError("timed out"), ProviderErrorCode.TIMEOUT, True),
    ],
)
def test_structured_error_mapping_and_redaction(
    error: Exception, expected_code: ProviderErrorCode, expected_retry: bool
) -> None:
    client, sdk = build_client(error=error)
    outcome = client.encode_text(request())
    assert isinstance(outcome, InferenceProviderError)
    assert outcome.code == expected_code
    assert outcome.retryable is expected_retry
    assert outcome.trace_id == "trace-s02"
    assert len(sdk.calls) == 1
    assert "sensitive" not in outcome.model_dump_json()
    assert "secret" not in outcome.model_dump_json()
    assert "api_key" not in outcome.model_dump_json()


def test_unexpected_programming_error_is_not_misclassified_as_outage() -> None:
    client, _ = build_client(error=RuntimeError("programming bug"))
    with pytest.raises(RuntimeError, match="programming bug"):
        client.encode_text(request())


def test_retry_decision_uses_caller_budget_not_hidden_attempts() -> None:
    client, _ = build_client(error=FakeSDKRequestError(429, "RATE_LIMIT"))
    error = client.encode_text(request())
    assert isinstance(error, InferenceProviderError)
    assert inference_retry_allowed(error, attempt_number=1, max_attempts=2, remaining_seconds=5)
    assert not inference_retry_allowed(error, attempt_number=2, max_attempts=2, remaining_seconds=5)
    assert not inference_retry_allowed(error, attempt_number=1, max_attempts=2, remaining_seconds=0)
    with pytest.raises(ValueError):
        inference_retry_allowed(error, attempt_number=0, max_attempts=2, remaining_seconds=5)
    with pytest.raises(ValueError):
        inference_retry_allowed(
            error, attempt_number=1, max_attempts=2, remaining_seconds=float("inf")
        )


def test_non_retryable_auth_failure_ignores_generous_budget() -> None:
    client, _ = build_client(error=FakeSDKRequestError(401, "AUTH"))
    error = client.encode_text(request())
    assert isinstance(error, InferenceProviderError)
    assert not inference_retry_allowed(
        error, attempt_number=1, max_attempts=100, remaining_seconds=1000
    )
