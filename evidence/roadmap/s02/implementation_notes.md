# S02 — Embedding vector contract and Superlinked error boundary

**Date:** 2026-10-20  
**Roadmap:** P1/S02 → contributes to G1  
**Base commit:** `3631ab01feabb6fc0246e95a364b5a9c64f292c8`  
**Disposition:** IMPLEMENTATION CANDIDATE — **NOT VALIDATED ON THE USER'S SDK OR LOCAL CHECKOUT**.

## Scope and intent

This change preserves the existing `InferenceClient.encode_text(request)` protocol while returning an actual, validated dense vector. The response includes the requested model, optionally the provider-reported model, and the request's `document`/`query` task. Missing provider model metadata stays `None`; the Lab does **not** pretend that requested identity was independently verified. A reported model mismatch is rejected. The vector is application data and must not be logged.

`EmbeddingResponse` validates a nonempty one-dimensional numeric vector, finite values, exact length/dimension agreement, and the supported dense output type. The adapter consumes the SDK's NumPy-style dense result without exposing SDK/NumPy objects at the application boundary. It also supports a `{"values": [...]}` mapping when supplied, while rejecting metadata-only `{"dims": N}`.

The Superlinked adapter uses SDK exception classes and structured `status_code`/`code` attributes, never text-searches exception messages. Generic `503` is **unavailable**, not assumed model loading. `MODEL_LOADING` requires a known typed exception or exact structured code. Authentication, quota, rate limiting, malformed requests, server failure, resource exhaustion, timeout and unclassified vendor errors receive distinct safe outcomes. Unexpected non-SDK programming errors are not mislabeled as transient provider failures.

One `encode_text` invocation calls the SDK once. The Lab introduces no automatic retry loop. `inference_retry_allowed` is only a pure decision helper for downstream orchestration. SDK-internal retries, if any, must be measured and bounded during the subsequent live-backend qualification; the Lab cannot certify total wall-clock limits from fake-based tests.

## API and migration note

- `InferenceClient.encode_text` keeps the same method signature and union return type.
- `EmbeddingResponse` now **requires** `dense_vector` and still exposes `dense_dimensions`; callers constructing success results must provide the vector. This intentional schema extension is incompatible with callers constructing metadata-only success objects.
- `EmbeddingRequest` adds `task` with a backwards-compatible default of `document`. Query calls set `is_query=True` on the SDK; document calls retain the prior SDK invocation shape.
- `ProviderErrorCode` adds categories and corrects generic HTTP `503` semantics. Tests assuming all 503s indicate model loading are intentionally replaced.
- No provider installation strategy, retrieval code, hosted credentials, dependency declarations, historical evidence or formatting in unrelated files is changed. Those remain scheduled for S03/S04 or later.

## SDK compatibility boundary

The user captured `sie-sdk==0.6.4` as installed at G0. Public Python SDK documentation describes `SIEClient.encode`, `is_query`, `RequestError`, `ServerError`, `ModelLoadingError`, `ProvisioningError`, `SIEConnectionError`, and their structured fields. Documentation may describe a newer SDK version. Therefore **the package includes a read-only local preflight that must pass before copying files**; this checks the exact installed distribution version, required exception symbols and encode signature, but does not itself prove live exception semantics.

If preflight fails, stop and share its safe textual output; do not force installation or guess imports. The focused contract tests simulate SDK exception subclasses, not a real SIE server. A future real-provider S03 smoke and error-integration investigation remain mandatory to qualify G1.

## Deterministic acceptance cases

- Valid numeric vector, NumPy array, optional model identity, task metadata and trace ID.
- Empty, 2D, boolean/string/non-numeric, infinite, NaN, declared-dimension mismatch, model mismatch, missing dense values, batched shape mistaken for single result.
- Generic `503` versus confirmed loading, `401`, `403`, `402`/quota, `429`, `502` load failed, resource exhaustion, timeout, connection and unknown SDK failures.
- Secret-bearing provider exception text never enters typed error envelopes.
- No hidden application retry loop; retry decision requires positive attempt budget and remaining deadline.
- Existing structured-output, logging and settings tests remain required regressions.

## Known open risks / nonclaims

1. No SIE `0.6.4` local inspection output has yet been provided in this implementation session. Exact error-class availability and response shape remain user-machine preflight questions.
2. Offline fake tests are **not** proof of actual provider error semantics, server response formats, backend performance, no-network core independence, or real embedding utility.
3. SDK-internal retries and total elapsed-time behavior remain to be qualified with real backend evidence in S03/G1.
4. `sie-sdk` remains a core dependency until S03; mypy and the two historical Ruff-format differences remain S04 work.
5. Application vector representations and identity fingerprints are not yet retrieval-index qualifications (G3).

## Validation record

- Assistant sandbox: **46 focused tests passed** against deliberately simplified **simulated** SDK classes and a mocked config module; this is an implementation sanity check only. No installed `sie-sdk==0.6.4` was available in the assistant sandbox.
- User machine: no S02 preflight, Ruff, mypy or pytest run has been supplied for this candidate.
- `S02` state: **NOT ASSESSED** pending installation on a dedicated branch, local test outputs, diff inspection and accepted documentation. G1 remains open.

## Commercial proof fragment

A validated provider/model boundary with safe error evidence is reusable in an AI System Evaluation Audit. It does **not** justify marketing a qualified RAG system, real-provider portability or production readiness.
