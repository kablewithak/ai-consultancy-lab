# S04 — Reproducible foundation verification

**Phase / gate:** P1 / G1; entry: S03 merged in PR #7. **State:** candidate, requires local and GitHub evidence.

## Supported runtime and declared scope

- Supported for G1: **CPython 3.12 only**; the former `>=3.12` declaration and `py311` Ruff target were inconsistent. Python 3.13 support is intentionally not asserted.
- Runtime core: Pydantic, Pydantic Settings, python-dotenv. No required provider SDK or secrets.
- Direct verifier tools: pytest 9.0.3, Ruff 0.15.17 (observed S01), mypy 1.18.2. This exact mypy version is a proposed G1 tool pin, not an observed local installation.
- Optional provider: `sie-sdk==0.6.4`, selected through the `superlinked` extra. No default CI credential or live provider step.
- **Resolution limitation:** Direct developer tools and provider SDK are pinned, but core dependency ranges and transitive packages are **not fully locked**. Capture actual resolved versions from fresh Windows and GitHub Linux environments; decide whether hashes/lock files are needed before awarding G1. Do not call this bit-for-bit reproducibility.

## Install-and-verify order (Windows PowerShell)

1. Confirm clean `main` following S03 merge `7dd7a0eba81409ac791af810a98cf4cf4f3b850a`; create feature branch `feat/s04-reproducible-verification`.
2. Apply S04 ZIP only after verifying the starting branch and commit. Inspect repository changes.
3. Install the verifier tools in existing `.venv`: `python -m pip install -e ".[dev]"`; do not install the optional provider in a clean-core environment.
4. Run Ruff and inspect `ruff format --check .`. Previously observed formatting debt was `packages/config/settings.py` and `packages/privacy_controls/safe_logging.py`; the latter is also changed in S04 to eliminate partial secret exposure. Format these two files, inspect their diff, and re-run the whole-tree check. Do not reformat unrelated sources to hide regressions.
5. Run `python -m mypy` and fix real type errors in the explicitly enumerated files. A selected focused scope is not repository-wide typing.
6. Run `python -m pytest -q` (offline default) and `python -m pip check`.
7. Check SDK independence in a new, fresh Python 3.12 virtual environment: `python -m pip install -e ".[dev]"`, `importlib.util.find_spec('sie_sdk') is None`, Ruff, mypy, pytest.
8. On the provider-enabled machine, run `python -m pytest -q tests/provider/superlinked` and `python scripts/preflight_s02_sdk.py`. Opt-in local-only smoke was already observed in S03 with both 384-dimensional document/query embeddings; repeat only if changes affect the runtime boundary or qualification requires a fresh final candidate.
9. Push the PR and inspect the actual GitHub Actions **Core verification (offline)** job result. Merely adding YAML does not qualify CI. Preserve the PR run link and evidence metadata.
10. Record exact commit SHA, Python/platform, installed versions, test counts and failures, and reviewer decision in `evidence/roadmap/s04/` and the G1 decision record before merge/closeout.

### Command block (repository root)

```powershell
$python = '.\.venv\Scripts\python.exe'
& $python -m pip check
& $python -m ruff check .
& $python -m ruff format --check .
& $python -m mypy
& $python -m pytest -q
& git diff --check
```

### CI failure taxonomy

| Failure | Meaning | Recovery |
| --- | --- | --- |
| Install fails | Tool/runtime/dependency resolution incompatibility | Inspect package and interpreter versions, correct only demonstrated conflict |
| SDK installed in CI | Core isolation regression | Remove implicit extra; never bypass SDK-free assertion |
| Ruff failure | Lint/style debt | Inspect file-specific diff, smallest correction |
| Mypy failure | Contract/type defect or unsupported typing dependency | Investigate diagnostic; no global ignore/silent fallback |
| Pytest failure | Regression or accidental network use | Reproduce locally; preserve traceback and test case |
| CI missing or skipped | Automated gate not executed | Treat as BLOCKED, not passed |

## G1 decision requirements

Evidence must connect: S02 usable vector and typed errors, S03 no-SDK core plus real SIE, fresh S04 supported environment, passing offline CI/local verification, safe metadata logging, stated type-check scope, dependency resolution and version record. A missing mandatory check or unreviewed regression blocks G1. S04 is not production, RAG, cost, security compliance or model-quality certification.
