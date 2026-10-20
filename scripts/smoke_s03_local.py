"""Explicit local-only real SIE smoke check; no credentials or embedding values logged."""

from __future__ import annotations

import argparse
import json
from urllib.parse import urlsplit

from packages.config.settings import SuperlinkedSettings
from packages.inference_clients.base import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingTask,
)
from packages.inference_clients.factory import InferenceBackend, create_embedding_client


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe only a local SIE HTTP endpoint.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = parser.parse_args()

    url = urlsplit(args.base_url)
    if (
        url.scheme != "http"
        or url.hostname not in {"127.0.0.1", "localhost"}
        or url.username is not None
        or url.password is not None
        or url.query
        or url.fragment
        or url.path not in {"", "/"}
    ):
        parser.error("S03 smoke check accepts only a plain loopback HTTP endpoint.")

    # Explicit constructor arguments supersede any .env values. Also disable .env reads.
    settings = SuperlinkedSettings(
        sie_base_url=args.base_url,
        sie_api_key=None,
        sie_embedding_model=args.model,
        _env_file=None,
    )
    client = create_embedding_client(backend=InferenceBackend.SUPERLINKED, settings=settings)
    results: list[dict[str, object]] = []
    for task in (EmbeddingTask.DOCUMENT, EmbeddingTask.QUERY):
        response = client.encode_text(
            EmbeddingRequest(
                text="AI Consultancy Lab S03 local integration check.",
                model=args.model,
                task=task,
            )
        )
        if isinstance(response, EmbeddingResponse):
            results.append(
                {
                    "task": task.value,
                    "status": response.status.value,
                    "provider": response.provider,
                    "model": response.model,
                    "reported_model": response.reported_model,
                    "dimensions": response.dense_dimensions,
                    "trace_id": response.trace_id,
                }
            )
        else:
            results.append(
                {
                    "task": task.value,
                    "status": response.status.value,
                    "code": response.code.value,
                    "retryable": response.retryable,
                    "trace_id": response.trace_id,
                }
            )
            print(json.dumps({"local_sie": "FAIL", "results": results}, indent=2))
            return 1

    print(json.dumps({"local_sie": "PASS", "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
