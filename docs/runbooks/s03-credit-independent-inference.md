# S03 — Credit-independent inference development

**Roadmap:** P1/S03 (contributes to G1)
**Dependency:** S02 merged in PR #6; fresh local S02 validation remains required
**Claim boundary:** Core tests can run without a provider SDK; only a separate real smoke receipt supports real-embedding availability.

## Provider selection

Application code depends on `InferenceClient`. `create_embedding_client(backend=InferenceBackend.DISABLED)` is a safe, explicit non-network mode that returns `CONFIGURATION_ERROR` (not fake semantic output). `create_embedding_client(backend=InferenceBackend.SUPERLINKED)` lazily imports the Superlinked adapter and loads its settings only if selected. If `sie-sdk` is absent, the selected mode raises `BackendUnavailableError`, with no fallback.

`ScriptedEmbeddingClient` lives only under `tests/fakes`. Inject it directly via the `InferenceClient` protocol; never use it as evidence of real model quality. A fake result is not interchangeable with a real model.

## Dependencies and test separation

- `python -m pip install -e ".[dev]"` installs core and ordinary test tools, without installing `sie-sdk` as a direct Lab dependency.
- `python -m pytest -q` runs `tests/unit` by default, with a socket-level deny-network fixture. It does not collect provider-only tests.
- `python -m pip install -e ".[dev,superlinked]"` opts in to `sie-sdk==0.6.4` for a backend workstation.
- `python -m pytest -q tests/provider/superlinked` explicitly runs the SDK-dependent **mock-based** adapter contract tests. These tests do not contact the provider.
- `python scripts/preflight_s02_sdk.py` inspects the installed SDK's static symbols. It is not a live qualification.

**Required clean-core proof:** Use a fresh venv, install only `.[dev]`, verify that `importlib.util.find_spec("sie_sdk")` returns `None`, run the default pytest suite, instantiate the disabled backend and confirm a typed nonretryable configuration error. A preexisting developer venv with the SDK already installed does not demonstrate SDK independence.

`tests/provider` is excluded from default collection by the explicit `testpaths` setting. A skipped required test is not a passing test. Run the provider suite explicitly when the provider extra is selected, and keep its result separately from core tests.

## Local-only SIE smoke (opt in)

This step requires user-confirmed Docker availability and explicitly starts an inference server. Historical evidence records a CPU server exposed at `127.0.0.1:8081` with `sentence-transformers/all-MiniLM-L6-v2`. It is a candidate, not a current guarantee. The first launch may download model files and take additional time.

For an already running and healthy local SIE instance:

```powershell
python scripts/preflight_s02_sdk.py
python scripts/smoke_s03_local.py --base-url http://127.0.0.1:8081 --model sentence-transformers/all-MiniLM-L6-v2
```

The smoke script **rejects non-loopback destinations** and explicitly supplies no API key. It evaluates both document and query embedding tasks, validates vectors through S02 contracts, and reports only metadata (trace ID, model identity, task, dimensions and status). It does not log raw text, vectors, `.env` values or secrets.

If the local server returns a temporary model-loading failure, observe readiness and retry manually within the chosen budget. Do not add hidden automatic retries or treat an arbitrary `503` as known loading. Do not substitute a hosted endpoint in this local-only script.

If local SIE is unavailable, record S03's real-backend criterion **BLOCKED** and investigate an actually accessible alternative through a separate approved adapter decision. Offline fake tests alone cannot award G1.

## S03 evidence and decision

Record exact HEAD SHA, interpreter version, installed extras, no-SDK clean-core proof, default pytest outcome, provider-only test outcome, local SIE status and model, safe error examples, `git diff --check` and open risks. Keep host credentials and vector payloads out of version control. Do not award S03 based on a successful merge alone.

S04 owns mypy, Python/Ruff target consistency, CI, dependency resolution and verified fresh-environment reproducibility across supported runtime versions.
