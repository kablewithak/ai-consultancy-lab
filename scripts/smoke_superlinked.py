from __future__ import annotations

from packages.config.settings import SuperlinkedSettings
from packages.inference_clients.base import EmbeddingRequest, InferenceProviderError
from packages.inference_clients.superlinked import SuperlinkedInferenceClient
from packages.trace_logging.logger import build_trace_event


def main() -> int:
    settings = SuperlinkedSettings()

    request = EmbeddingRequest(
        text="Superlinked Week 1 smoke test for ai-consultancy-lab.",
        model=settings.sie_embedding_model,
    )

    client = SuperlinkedInferenceClient(settings)
    response = client.encode_text(request)

    if isinstance(response, InferenceProviderError):
        print(
            build_trace_event(
                trace_id=response.trace_id,
                event_name="superlinked_encode_smoke_test_failed",
                provider=response.provider,
                payload={
                    "model": response.model,
                    "status": response.status,
                    "code": response.code,
                    "message": response.message,
                    "retryable": response.retryable,
                    "error_type": response.error_type,
                },
            )
        )
        return 2 if response.retryable else 1

    print(
        build_trace_event(
            trace_id=response.trace_id,
            event_name="superlinked_encode_smoke_test_passed",
            provider=response.provider,
            payload={
                "model": response.model,
                "status": response.status,
                "dense_dimensions": response.dense_dimensions,
                "output_types": response.output_types,
            },
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
