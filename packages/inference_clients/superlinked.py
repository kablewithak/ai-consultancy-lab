from __future__ import annotations

from typing import Any

from sie_sdk import SIEClient
from sie_sdk.types import Item

from packages.config.settings import SuperlinkedSettings
from packages.inference_clients.base import (
    EmbeddingCallResult,
    EmbeddingRequest,
    EmbeddingResponse,
    InferenceProviderError,
    ProviderErrorCode,
)


class SuperlinkedInferenceClient:
    """Superlinked-backed implementation of the provider-neutral inference client.

    This adapter is allowed to know about Superlinked.
    Core packages should depend on the provider-neutral interface instead.
    """

    provider_name = "superlinked"

    def __init__(self, settings: SuperlinkedSettings, sdk_client: Any | None = None) -> None:
        self._settings = settings
        self._client = sdk_client or SIEClient(
            settings.sie_base_url,
            timeout_s=settings.sie_timeout_s,
            api_key=settings.api_key_value,
        )

    def encode_text(self, request: EmbeddingRequest) -> EmbeddingCallResult:
        try:
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
        except KeyError as exc:
            return self._build_error(
                request=request,
                code=ProviderErrorCode.UNEXPECTED_RESPONSE,
                message="Superlinked returned an unexpected response shape.",
                retryable=False,
                error_type=exc.__class__.__name__,
            )
        except ValueError as exc:
            return self._build_error(
                request=request,
                code=ProviderErrorCode.UNEXPECTED_RESPONSE,
                message="Superlinked returned an embedding that could not be validated.",
                retryable=False,
                error_type=exc.__class__.__name__,
            )
        except TimeoutError as exc:
            return self._build_error(
                request=request,
                code=ProviderErrorCode.TIMEOUT,
                message="Superlinked inference timed out.",
                retryable=True,
                error_type=exc.__class__.__name__,
            )
        except Exception as exc:  # noqa: BLE001 - provider boundary converts unknown SDK failures.
            return self._provider_exception_to_error(request=request, exc=exc)

    def _provider_exception_to_error(
        self,
        *,
        request: EmbeddingRequest,
        exc: Exception,
    ) -> InferenceProviderError:
        exception_text = str(exc).lower()
        exception_type = exc.__class__.__name__

        if "503" in exception_text or "service unavailable" in exception_text:
            return self._build_error(
                request=request,
                code=ProviderErrorCode.MODEL_LOADING,
                message=(
                    "Superlinked model is temporarily unavailable, likely because "
                    "it is still downloading, loading, or warming up."
                ),
                retryable=True,
                error_type=exception_type,
            )

        if "timeout" in exception_text or "timed out" in exception_text:
            return self._build_error(
                request=request,
                code=ProviderErrorCode.TIMEOUT,
                message="Superlinked inference timed out.",
                retryable=True,
                error_type=exception_type,
            )

        if any(
            marker in exception_text
            for marker in (
                "connection refused",
                "failed to establish",
                "connection error",
                "connecterror",
                "network is unreachable",
                "name or service not known",
            )
        ):
            return self._build_error(
                request=request,
                code=ProviderErrorCode.PROVIDER_UNAVAILABLE,
                message="Superlinked provider is unavailable at the configured base URL.",
                retryable=True,
                error_type=exception_type,
            )

        return self._build_error(
            request=request,
            code=ProviderErrorCode.PROVIDER_UNAVAILABLE,
            message="Superlinked provider returned an SDK error.",
            retryable=True,
            error_type=exception_type,
        )

    def _build_error(
        self,
        *,
        request: EmbeddingRequest,
        code: ProviderErrorCode,
        message: str,
        retryable: bool,
        error_type: str | None,
    ) -> InferenceProviderError:
        return InferenceProviderError(
            trace_id=request.trace_id,
            provider=self.provider_name,
            model=request.model,
            code=code,
            message=message,
            retryable=retryable,
            error_type=error_type,
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
