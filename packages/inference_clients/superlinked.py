from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import ValidationError
from sie_sdk import SIEClient
from sie_sdk.client.errors import (
    ModelLoadingError,
    ProvisioningError,
    RequestError,
    SIEConnectionError,
    SIEError,
    ServerError,
)
from sie_sdk.types import Item

from packages.config.settings import SuperlinkedSettings
from packages.inference_clients.base import (
    EmbeddingCallResult,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingTask,
    InferenceProviderError,
    ProviderErrorCode,
    normalize_dense_vector,
)


class SuperlinkedInferenceClient:
    """Single-call SDK adapter; retry orchestration belongs outside this boundary.

    The SDK itself may retry selected errors. There is no second adapter retry loop.
    """

    provider_name = "superlinked"

    def __init__(self, settings: SuperlinkedSettings, sdk_client: Any | None = None) -> None:
        self._settings = settings
        self._client = sdk_client if sdk_client is not None else SIEClient(
            settings.sie_base_url,
            timeout_s=settings.sie_timeout_s,
            api_key=settings.api_key_value,
        )

    def encode_text(self, request: EmbeddingRequest) -> EmbeddingCallResult:
        options: dict[str, Any] = {"output_types": ["dense"]}
        if request.task == EmbeddingTask.QUERY:
            options["is_query"] = True

        try:
            result = self._client.encode(request.model, Item(text=request.text), **options)
        except ModelLoadingError as exc:
            return self._build_error(request, ProviderErrorCode.MODEL_LOADING, True, exc)
        except ProvisioningError as exc:
            return self._build_error(request, ProviderErrorCode.PROVIDER_UNAVAILABLE, True, exc)
        except SIEConnectionError as exc:
            return self._build_error(request, ProviderErrorCode.PROVIDER_UNAVAILABLE, True, exc)
        except RequestError as exc:
            return self._map_http_error(request, exc)
        except ServerError as exc:
            return self._map_http_error(request, exc)
        except httpx.TimeoutException as exc:
            return self._build_error(request, ProviderErrorCode.TIMEOUT, True, exc)
        except httpx.TransportError as exc:
            return self._build_error(request, ProviderErrorCode.PROVIDER_UNAVAILABLE, True, exc)
        except TimeoutError as exc:
            return self._build_error(request, ProviderErrorCode.TIMEOUT, True, exc)
        except SIEError as exc:
            # Unrecognized vendor exceptions are terminal until classified.
            return self._build_error(request, ProviderErrorCode.INTERNAL_ERROR, False, exc)

        # SDK/shape validation is separate from transport exceptions. Programming
        # errors outside these explicit shapes are intentionally not swallowed.
        try:
            if not isinstance(result, Mapping):
                raise ValueError("Expected a single result mapping.")
            vector = normalize_dense_vector(result["dense"])
            model_from_provider = result.get("model")
            if model_from_provider is not None:
                if not isinstance(model_from_provider, str) or not model_from_provider.strip():
                    raise ValueError("Provider supplied invalid model identity.")
                model_from_provider = model_from_provider.strip()

            return EmbeddingResponse(
                trace_id=request.trace_id,
                provider=self.provider_name,
                model=request.model,
                reported_model=model_from_provider,
                task=request.task,
                dense_vector=vector,
                dense_dimensions=len(vector),
                output_types=["dense"],
            )
        except (KeyError, ValueError, ValidationError, TypeError) as exc:
            return self._build_error(request, ProviderErrorCode.UNEXPECTED_RESPONSE, False, exc)

    def _map_http_error(
        self, request: EmbeddingRequest, exc: RequestError | ServerError
    ) -> InferenceProviderError:
        status = getattr(exc, "status_code", None)
        code = getattr(exc, "code", None)
        code_key = code.upper() if isinstance(code, str) else ""

        if status in (401, 403):
            return self._build_error(request, ProviderErrorCode.AUTHENTICATION_ERROR, False, exc)
        exhausted_codes = {"QUOTA_EXCEEDED", "INSUFFICIENT_CREDITS", "OUT_OF_CREDITS"}
        if status == 402 or code_key in exhausted_codes:
            return self._build_error(request, ProviderErrorCode.QUOTA_EXHAUSTED, False, exc)
        if status == 429 or code_key == "RATE_LIMIT":
            return self._build_error(request, ProviderErrorCode.RATE_LIMITED, True, exc)
        if code_key == "MODEL_LOADING":
            return self._build_error(request, ProviderErrorCode.MODEL_LOADING, True, exc)
        if code_key == "MODEL_LOAD_FAILED":
            return self._build_error(request, ProviderErrorCode.MODEL_LOAD_FAILED, False, exc)
        if code_key == "RESOURCE_EXHAUSTED":
            return self._build_error(request, ProviderErrorCode.RESOURCE_EXHAUSTED, False, exc)
        if status in (408, 504):
            return self._build_error(request, ProviderErrorCode.TIMEOUT, True, exc)
        if isinstance(status, int) and 400 <= status < 500:
            return self._build_error(request, ProviderErrorCode.INVALID_REQUEST, False, exc)
        if isinstance(status, int) and 500 <= status < 600:
            return self._build_error(request, ProviderErrorCode.PROVIDER_UNAVAILABLE, True, exc)
        # SDK error without interpretable status/code: fail closed, no guesses.
        return self._build_error(request, ProviderErrorCode.INTERNAL_ERROR, False, exc)

    def _build_error(
        self,
        request: EmbeddingRequest,
        code: ProviderErrorCode,
        retryable: bool,
        exc: Exception,
    ) -> InferenceProviderError:
        return InferenceProviderError(
            trace_id=request.trace_id,
            provider=self.provider_name,
            model=request.model,
            code=code,
            message=_ERROR_MESSAGES[code],
            retryable=retryable,
            error_type=type(exc).__name__,
        )


_ERROR_MESSAGES: dict[ProviderErrorCode, str] = {
    ProviderErrorCode.MODEL_LOADING: "The model is loading and is not yet available.",
    ProviderErrorCode.MODEL_LOAD_FAILED: "The model failed to load.",
    ProviderErrorCode.PROVIDER_UNAVAILABLE: "The inference provider is unavailable.",
    ProviderErrorCode.RESOURCE_EXHAUSTED: "The provider exhausted runtime resources.",
    ProviderErrorCode.TIMEOUT: "The inference request timed out.",
    ProviderErrorCode.CONFIGURATION_ERROR: "Inference configuration is invalid.",
    ProviderErrorCode.AUTHENTICATION_ERROR: "Provider authentication or permission failed.",
    ProviderErrorCode.QUOTA_EXHAUSTED: "Provider credits or quota are exhausted.",
    ProviderErrorCode.RATE_LIMITED: "The provider rejected the request due to rate limiting.",
    ProviderErrorCode.INVALID_REQUEST: "The provider rejected the inference request.",
    ProviderErrorCode.UNEXPECTED_RESPONSE: "The provider returned an invalid embedding result.",
    ProviderErrorCode.INTERNAL_ERROR: "An unclassified provider error occurred.",
}


def dense_dimensions(dense: Any) -> int:
    """Legacy helper preserved, now requires usable values rather than dims metadata."""

    return len(normalize_dense_vector(dense))
