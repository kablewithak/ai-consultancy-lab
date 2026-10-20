# S04 — Windows clean-core validation receipt (2026-10-20)

**Roadmap:** P1 / S04 — Reproducible Engineering Verification; contributes to G1.
**Base:** S03 PR #7 merge `7dd7a0eba81409ac791af810a98cf4cf4f3b850a`.
**Feature branch:** `feat/s04-reproducible-verification`.
**Evidence source:** User-pasted PowerShell output from an isolated Windows virtual environment on 2026-10-20. Reviewer did not execute these tests on the user's workstation.
**Disposition:** Clean-core local qualification **PASS**; complete S04/G1 qualification **PENDING CI and final change review**.

## Observed clean-core gates

| Check | Evidence | Disposition |
| --- | --- | --- |
| Clean development install | `pip install -e '.[dev]'` reported successfully installed `ai-consultancy-lab==0.1.0` and verifier dependencies | PASS |
| Optional SDK isolation | Printed `NO-SDK CHECK: PASS`; `sie_sdk` absent from fresh environment | PASS |
| Dependency integrity | `pip check`: `No broken requirements found.` | PASS |
| Ruff lint | `All checks passed!` | PASS |
| Whole-tree Ruff formatting | `28 files already formatted` | PASS |
| Focused mypy | `Success: no issues found in 7 source files` | PASS within explicit scope |
| Offline pytest regression | `36 passed in 1.32s` | PASS |
| Clean environment checkpoint | Printed `S04 FRESH ENVIRONMENT: PASS` | PASS |

The clean environment used CPython 3.12-compatible Windows packages (wheel tag `cp312-win_amd64`); this receipt does not independently establish the exact interpreter patch version. The initial S04 mypy `SuperlinkedSettings()` diagnostic was resolved by enabling `pydantic.mypy`; the later clean-core mypy invocation passed. Historical Ruff formatting differences were addressed locally before this clean-environment run.

## Resolved clean-core package versions

```text
ai-consultancy-lab==0.1.0
annotated-types==0.8.0
colorama==0.4.6
iniconfig==2.3.1
mypy==1.18.2
mypy_extensions==1.1.0
packaging==26.3
pathspec==1.1.1
pip==25.0.1
pluggy==1.7.0
pydantic==2.14.1
pydantic_core==2.50.1
pydantic-settings==2.16.1
Pygments==2.21.0
pytest==9.0.3
python-dotenv==1.2.4
ruff==0.15.17
typing_extensions==4.16.0
typing-inspection==0.4.4
```

## Earlier evidence incorporated by reference

S03's acceptance receipt documents separate SDK-enabled adapter contract tests and a live local SIE smoke: both document and query embeddings succeeded, each with 384 dimensions, with `reported_model=null`. S04's clean-core suite does not rerun live SIE. SDK-enabled provider regression must be checked after S04's final candidate changes are staged.

## Pending before G1 decision

1. Final S04 scoped diff review and staged whitespace check; record the final feature commit SHA.
2. Current S04 provider-enabled adapter regression run and SDK static preflight (if the provider environment is available).
3. GitHub PR-triggered **Core verification (offline)** workflow must execute and pass; capture PR and run links/IDs, Linux Python and package resolution.
4. Review the cross-environment dependency inventory and record the limitation: core dependencies remain range-constrained and transitive dependencies are not hash-locked. A fresh successful install is evidence for this resolution, not a bit-for-bit reproduction guarantee.
5. Final written G1 decision, including precisely scoped mypy coverage, provider-model identity limit, known S02 historical check gap, and nonclaims.

**Not established:** Production readiness, customer-data qualification, RAG/evaluation quality, hosted-credit availability, model identity verified by provider metadata, full repository static typing, or complete transitive dependency locking.
