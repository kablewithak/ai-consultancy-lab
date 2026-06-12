# ADR-0001: AI Reliability Lab Architecture and Superlinked Provider Boundary

## Status

Accepted

## Context

The `ai-consultancy-lab` exists to build production-shaped AI reliability proof assets:

- typed inference boundaries
- eval harnesses
- trace-safe logging
- privacy controls
- retrieval systems
- agent harnesses
- buyer-facing evidence assets

Superlinked credits are available and should be used from Week 1 as a visible, real inference provider integration.

The risk is turning the roadmap into a provider-specific demo instead of a durable AI reliability lab.

## Decision

Use Superlinked as the first external inference provider, behind a provider-neutral adapter.

```text
Superlinked is the first provider adapter.
Superlinked is not the architecture.
```

The dependency direction is:

```text
script / app
  -> provider-neutral inference interface
  -> Superlinked adapter
  -> validated response object
  -> trace-safe output
```

Core packages must not import Superlinked directly. They should depend on provider-neutral interfaces.

## Design Rules

### Provider Boundary

The Superlinked SDK may only be imported inside the Superlinked adapter module.

Allowed:

```text
packages/inference_clients/superlinked.py imports sie_sdk
```

Avoid:

```text
retrieval_core imports sie_sdk directly
eval_harness imports sie_sdk directly
agent_harness imports sie_sdk directly
```

### Configuration

Secrets must be provided through environment variables or `.env`.

Required settings:

```text
SIE_BASE_URL
SIE_API_KEY
SIE_EMBEDDING_MODEL
SIE_TIMEOUT_S
```

`.env` must never be committed.

### Logging

Logs may include:

- `trace_id`
- provider name
- model name
- dense vector dimension
- success/failure status
- timing metadata later

Logs must not include:

- API keys
- raw secrets
- authorization headers
- raw customer documents
- raw prompts
- sensitive payloads

## Consequences

### Positive

- Superlinked is visible from Week 1.
- Real provider integration is tested early.
- API keys remain outside source control.
- Logs are metadata-safe.
- Later retrieval and RAG evals can use the same provider boundary.
- The lab remains portable if another provider is added later.

### Negative

- Slightly more upfront structure than a one-file smoke test.
- Requires discipline to avoid leaking provider-specific code into core packages.
- Requires a valid SIE base URL in addition to the API key.

## Verification

Week 1 verification requires:

```text
pytest
python scripts\smoke_superlinked.py
```

The smoke test must show:

- a successful Superlinked encode call
- a validated response object
- a dense vector dimension
- a trace-safe log event
- no leaked API key

## Week 1 Non-Claims

This does not prove:

- production readiness
- customer-data readiness
- RAG reliability
- retrieval improvement
- scale behavior
- provider superiority

## Current Maturity Label

```text
production-shaped provider integration scaffold,
locally validated,
not RAG-ready,
not customer-data tested,
not production-ready
```

## Commercial Translation

This integration supports the consultancy positioning because it proves:

- a real inference provider can be integrated safely
- the provider boundary is typed and replaceable
- credentials are handled through environment config
- logs are traceable without exposing secrets
- future retrieval and RAG evals can compare provider-backed behavior
- the work strengthens an inspectable AI reliability lab, not a throwaway demo

## Final Judgment

Use Superlinked from Week 1, but keep it behind a narrow adapter.

The correct first slice is:

```text
settings
+ provider-neutral inference interface
+ Superlinked adapter
+ smoke script
+ trace-safe logs
+ no-secret tests
+ ADR note
```

Then expand naturally into:

```text
Week 3 retrieval mechanics
Week 4 RAG baseline
Weeks 5-8 Dirty Data RAG capstone
Week 13 API Integration Deflection Agent
```
