# AI Consultancy Lab

Production-shaped AI reliability lab for evaluated, privacy-aware, harness-driven RAG and agent systems.

## Current Slice

Week 1 adds the first provider-backed inference boundary using Superlinked.

Superlinked is used as the first external inference provider, but the architecture remains provider-neutral.

## Maturity Label

production-shaped provider integration scaffold, locally validated, not RAG-ready, not customer-data tested, not production-ready

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

Run tests:

```powershell
pytest
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

## Week 1 Acceptance Criteria

- Repo initializes cleanly.
- Virtual environment works.
- Superlinked API key is loaded only from `.env`.
- `.env` is ignored by git.
- Superlinked adapter performs one smoke call.
- Smoke call returns a validated response object.
- Logs include `trace_id` and provider name.
- Logs do not include API key, raw secret, or sensitive payload.
- `pytest` passes.
- ADR-0001 documents Superlinked as first provider adapter, not the architecture.

## Week 1 Non-Claims

This does not prove:

- production readiness
- customer-data readiness
- RAG reliability
- retrieval improvement
- scale behavior
- provider superiority

Allowed maturity label:

```text
production-shaped provider integration scaffold,
locally validated,
not RAG-ready,
not customer-data tested,
not production-ready
```
