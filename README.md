# AI Consultancy Lab

Production-shaped AI reliability lab for evaluated, privacy-aware, harness-driven RAG and agent systems.

## Current Slice

Week 2 adds the structured-output foundation for deterministic model-output boundaries.

Week 1 added the first provider-backed inference boundary using Superlinked.

Superlinked is used as the first external inference provider, but the architecture remains provider-neutral.

```text
Superlinked is the first provider adapter.
Superlinked is not the architecture.
```

## Maturity Label

production-shaped provider integration and structured-output scaffold, locally unit-tested, not RAG-ready, not customer-data tested, not production-ready

## Setup

Run from the repo root:

```powershell
Set-Location "C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\ai-consultancy-lab"
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
notepad .env
```

Fill in the `.env` file:

```text
SIE_BASE_URL=https://replace-with-your-superlinked-sie-endpoint
SIE_API_KEY=replace-with-your-real-api-key
SIE_EMBEDDING_MODEL=BAAI/bge-m3
SIE_TIMEOUT_S=60
```

For local Docker SIE validation, `SIE_API_KEY` may be blank if the local SIE server does not require a key.

Run tests:

```powershell
python -m pytest
```

Run the Superlinked smoke test:

```powershell
python scripts\smoke_superlinked.py
```

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
