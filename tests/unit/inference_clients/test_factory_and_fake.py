from __future__ import annotations

import socket

import pytest

from packages.inference_clients.base import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingTask,
    InferenceClient,
    InferenceProviderError,
    ProviderErrorCode,
)
from packages.inference_clients.factory import (
    BackendUnavailableError,
    DisabledInferenceClient,
    InferenceBackend,
    create_embedding_client,
)
from tests.fakes.embedding import ScriptedEmbeddingClient


def test_disabled_mode_needs_no_credentials_or_provider_sdk() -> None:
    client = create_embedding_client(backend=InferenceBackend.DISABLED)
    assert isinstance(client, DisabledInferenceClient)
    result = client.encode_text(EmbeddingRequest(text="example", model="m", trace_id="t"))
    assert isinstance(result, InferenceProviderError)
    assert result.code == ProviderErrorCode.CONFIGURATION_ERROR
    assert result.retryable is False
    assert result.trace_id == "t"


def test_disabled_mode_rejects_extra_provider_configuration() -> None:
    with pytest.raises(ValueError, match="disabled"):
        create_embedding_client(
            backend=InferenceBackend.DISABLED,
            settings=object(),  # type: ignore[arg-type]
        )


def test_unknown_backend_does_not_silently_use_fake_or_hosted() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        create_embedding_client(backend="unknown")  # type: ignore[arg-type]


def test_optional_vendor_import_is_lazy_and_missing_extra_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Block optional-provider import even if this developer environment has the SDK.
    import builtins

    real_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name.startswith("sie_sdk"):
            raise ModuleNotFoundError("No module named 'sie_sdk'", name="sie_sdk")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    client = create_embedding_client(backend=InferenceBackend.DISABLED)
    assert isinstance(client, DisabledInferenceClient)
    with pytest.raises(BackendUnavailableError, match="optional extra"):
        create_embedding_client(backend=InferenceBackend.SUPERLINKED)


def test_missing_sdk_is_detected_before_importing_transitive_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Simulate a truly minimal core environment, regardless of host packages.
    import builtins
    import importlib.util

    original_find_spec = importlib.util.find_spec
    original_import = builtins.__import__

    def find_spec_without_sdk(name: str, *args: object, **kwargs: object) -> object:
        if name == "sie_sdk":
            return None
        return original_find_spec(name, *args, **kwargs)

    def block_httpx(name: str, *args: object, **kwargs: object) -> object:
        if name == "httpx":
            raise AssertionError("Optional transitive dependency imported before SDK check")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "find_spec", find_spec_without_sdk)
    monkeypatch.setattr(builtins, "__import__", block_httpx)

    with pytest.raises(BackendUnavailableError, match="optional extra"):
        create_embedding_client(backend=InferenceBackend.SUPERLINKED)


def test_fake_is_provided_via_application_protocol_injection() -> None:
    fake: InferenceClient = ScriptedEmbeddingClient(
        outcomes={"doc": (0.1, 0.2), "blocked": ProviderErrorCode.QUOTA_EXHAUSTED}
    )
    result = fake.encode_text(
        EmbeddingRequest(trace_id="fixed", text="doc", model="m", task=EmbeddingTask.QUERY)
    )
    assert isinstance(result, EmbeddingResponse)
    assert result.dense_vector == (0.1, 0.2)
    assert result.task == EmbeddingTask.QUERY
    failure = fake.encode_text(EmbeddingRequest(text="blocked", model="m"))
    assert isinstance(failure, InferenceProviderError)
    assert failure.code == ProviderErrorCode.QUOTA_EXHAUSTED
    missing = fake.encode_text(EmbeddingRequest(text="not scripted", model="m"))
    assert isinstance(missing, InferenceProviderError)
    assert missing.code == ProviderErrorCode.INVALID_REQUEST


def test_unit_suite_rejects_socket_connections() -> None:
    with socket.socket() as sock:
        with pytest.raises(AssertionError, match="must not open network"):
            sock.connect(("127.0.0.1", 9))
