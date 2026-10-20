# S03 — Credit-independent inference execution candidate

**Date:** 2026-10-20
**Roadmap:** P1/S03 → contributes to G1
**Upstream:** PR #6 merged at `2ea327de7aac75822be0375688a3979f88052e41`
**State:** IMPLEMENTATION CANDIDATE; local acceptance and live-backend evidence remain open.

## Change rationale

The existing `pyproject.toml` made `sie-sdk` a core dependency, and the adapter tests lived under `tests/unit`. This prevented an ordinary no-SDK core installation and a default offline test run. No hosted credentials are required for core contracts or structured outputs.

## Decisions

1. Move `sie-sdk==0.6.4` to the explicit `superlinked` extra. Preserve the version already observed at G0 rather than assuming a newer SDK.
2. Keep the vendor adapter implementation unchanged. Add lazy backend selection; disabled means a typed nonretryable configuration error, not a synthetic success or an implicit hosted fallback.
3. Keep the reusable scripted fake in `tests/fakes`, injected at `InferenceClient` and excluded from production package discovery.
4. Move the existing S02 Superlinked mock-contract tests to `tests/provider/superlinked`, which must be invoked explicitly with the provider extra. Preserve all cases.
5. Default `pytest` discovery to `tests/unit`. In the unit collection, socket connection attempts fail explicitly rather than reaching a local or hosted service.
6. Add an explicit loopback-only live smoke command and a runbook. The smoke prints metadata only and never reads an API key from `.env`.

## Acceptance evidence still required

- Local S02 preflight/Ruff/pytest outcome at the merged revision (not previously supplied).
- Core install and default tests in a clean venv where `sie_sdk` is truly absent.
- Explicit provider mock suite with the selected SDK installed.
- Current local real-backend response with usable validated embeddings for document and query tasks; or an agreed alternative real implementation. No real evidence = S03 BLOCKED for the G1 path.
- Environment/version/trace-safe receipts; code diff, whitespace and final local validation.

## Exclusions and nonclaims

No semantic retrieval, interchangeable real-provider claim, RAG quality evidence, hosted credits, cloud deployment, mypy gate, CI or customer data. The historical local SIE receipt does not count as current real-backend qualification.
