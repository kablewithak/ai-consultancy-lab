from __future__ import annotations

import pytest

from packages.inference_clients.base import EmbeddingRequest, EmbeddingResponse, InferenceStatus
from packages.inference_clients.superlinked import dense_dimensions


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


def test_dense_dimensions_from_list() -> None:
    assert dense_dimensions([0.1, 0.2, 0.3]) == 3


def test_dense_dimensions_from_dict_values() -> None:
    assert dense_dimensions({"values": [0.1, 0.2]}) == 2
