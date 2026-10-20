# AI Consultancy Lab

Production-shaped AI reliability lab for evaluated, privacy-aware, harness-driven RAG and agent systems.

## Current Slice

S03 introduces explicit provider selection, an SDK-optional core installation,
provider-independent deterministic tests, and an opt-in local SIE smoke route.

S02 added validated numerical embedding vectors and more precise provider errors.
Earlier work established the structured-output foundation and the first Superlinked adapter.

```text
Superlinked is the first provider adapter.
Superlinked is not the architecture.
```

## Maturity Label

Production-shaped inference and structured-output contracts, with provider-neutral
core development. Local S03 and real-backend qualification must be assessed from
fresh evidence. Not RAG-ready, customer-data qualified, or production-ready.

## Setup

Run from the repository root in PowerShell. Ordinary core tests require neither `sie-sdk` nor a provider endpoint, credentials or hosted credits.

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

The application selects `InferenceBackend.DISABLED` or `InferenceBackend.SUPERLINKED` explicitly; tests inject a scripted fake at the `InferenceClient` protocol. The disabled mode returns a configuration error rather than fake output.

To install and test the **optional** Superlinked provider adapter:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,superlinked]"
.\.venv\Scripts\python.exe -m pytest -q tests/provider/superlinked
.\.venv\Scripts\python.exe scripts/preflight_s02_sdk.py
```

For an already running local SIE service, run the **loopback-only/no-key** S03 probe explicitly:

```powershell
.\.venv\Scripts\python.exe scripts/smoke_s03_local.py --base-url http://127.0.0.1:8081 --model sentence-transformers/all-MiniLM-L6-v2
```

The historical `scripts/smoke_superlinked.py` uses `SIE_BASE_URL`, `SIE_API_KEY`, `SIE_EMBEDDING_MODEL` and `SIE_TIMEOUT_S` from `.env`; it is not an offline test. Never put secrets in Git. See `docs/runbooks/s03-credit-independent-inference.md` for the clean-core and live qualification procedures.

## Security Rules

- Do not commit `.env`.
- Do not paste API keys into code, logs, screenshots, GitHub, or ChatGPT.
- Do not log raw prompts, raw customer data, secrets, or sensitive payloads.
- Use trace IDs and metadata-safe logs only.
- Do not store raw model output inside validation error envelopes.

## Week 1 Acceptance Criteria

- Repo initializes cleanly.
- Virtual environment works.
- Superlinked API key is loaded only from `.env` when a hosted SIE endpoint needs it.
- `.env` is ignored by git.
- Superlinked adapter performs one smoke call.
- Smoke call returns a validated response object.
- Logs include `trace_id` and provider name.
- Logs do not include API key, raw secret, or sensitive payload.
- `pytest` passes.
- ADR-0001 documents Superlinked as first provider adapter, not the architecture.

## Week 2 Acceptance Criteria

- `packages/structured_outputs` exists as a reusable contract layer.
- Pydantic v2 models reject extra fields at the output boundary.
- Validation errors become machine-readable envelopes.
- Refusal and unsupported-answer states are explicit.
- Retry/escalation decisions are bounded and typed.
- Tests prove valid output, invalid output, extra-field rejection, refusal, unsupported answers, and retry decisions.
- Validation envelopes do not persist raw model output payloads.

## Week 1 Non-Claims

This does not prove:

- production readiness
- customer-data readiness
- RAG reliability
- retrieval improvement
- scale behavior
- provider superiority

## Week 2 Non-Claims

This does not prove:

- RAG reliability
- retrieval improvement
- agent reliability
- customer-data readiness
- production readiness
- LLM provider output quality

Allowed maturity label:

```text
production-shaped provider integration and structured-output scaffold,
locally unit-tested,
not RAG-ready,
not customer-data tested,
not production-ready
```
