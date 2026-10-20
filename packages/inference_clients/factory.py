"""Select a declared embedding backend without importing optional providers by default."""

from __future__ import annotations

import importlib.util
from enum import StrEnum
from typing import TYPE_CHECKING

from packages.inference_clients.base import (
    EmbeddingCallResult,
    EmbeddingRequest,
    InferenceClient,
    InferenceProviderError,
    ProviderErrorCode,
)

if TYPE_CHECKING:
    from packages.config.settings import SuperlinkedSettings


class InferenceBackend(StrEnum):
    DISABLED = "disabled"
    SUPERLINKED = "superlinked"


class BackendUnavailableError(RuntimeError):
    """The explicitly selected optional provider is not installed."""


class DisabledInferenceClient:
    """Fail closed: no implicit fake or hosted backend fallback."""

    def encode_text(self, request: EmbeddingRequest) -> EmbeddingCallResult:
        return InferenceProviderError(
            trace_id=request.trace_id,
            provider=InferenceBackend.DISABLED,
            model=request.model,
            code=ProviderErrorCode.CONFIGURATION_ERROR,
            message="No embedding backend has been enabled.",
            retryable=False,
        )


def create_embedding_client(
    *,
    backend: InferenceBackend,
    settings: SuperlinkedSettings | None = None,
) -> InferenceClient:
    """Construct only the named backend; never fall back silently.

    Ordinary imports and the disabled path do not require sie-sdk or a .env file.
    Test fakes are injected directly as InferenceClient instances, not selected here.
    """

    if backend == InferenceBackend.DISABLED:
        if settings is not None:
            raise ValueError("Provider settings cannot be supplied for a disabled backend.")
        return DisabledInferenceClient()

    if backend == InferenceBackend.SUPERLINKED:
        # Resolve optional-provider availability before importing its adapter.
        # Otherwise an absent transitive SDK dependency (e.g. httpx) could
        # mask the missing extra with an unrelated ModuleNotFoundError.
        if importlib.util.find_spec("sie_sdk") is None:
            raise BackendUnavailableError(
                "Superlinked backend requires optional extra: pip install -e '.[superlinked]'"
            )
        try:
            from packages.config.settings import SuperlinkedSettings
            from packages.inference_clients.superlinked import SuperlinkedInferenceClient
        except ModuleNotFoundError as exc:
            if exc.name == "sie_sdk" or (exc.name or "").startswith("sie_sdk."):
                raise BackendUnavailableError(
                    "Superlinked backend requires optional extra: pip install -e '.[superlinked]'"
                ) from None
            raise
        selected_settings = settings if settings is not None else SuperlinkedSettings()
        return SuperlinkedInferenceClient(selected_settings)

    raise ValueError(f"Unsupported embedding backend: {backend!r}")
