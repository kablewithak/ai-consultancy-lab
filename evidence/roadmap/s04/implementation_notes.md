# S04 — Reproducible foundation verification candidate

**Date:** 2026-10-20
**Phase:** P1 / S04 (G1 exit)
**Upstream:** S03 PR #7 merged at `7dd7a0eba81409ac791af810a98cf4cf4f3b850a`
**State:** IMPLEMENTATION CANDIDATE — no S04 local verifier or GitHub CI results yet.

## Factual incoming state

- S01 observed Python 3.12.10, Ruff 0.15.17, pytest 9.0.3, Pydantic 2.13.4, pydantic-settings 2.14.1; mypy was absent.
- S01 Ruff check passed; whole-tree formatting reported `packages/config/settings.py` and `packages/privacy_controls/safe_logging.py`.
- S02 PR #6 merged a validated numeric embedding boundary with typed provider errors; its standalone final local check receipt was not supplied.
- S03 PR #7 merged SDK-independent core and local-only SIE smoke; user supplied no-SDK/core/provider test pass and two real 384-dimensional document/query embeddings.
- GitHub had no automated CI workflow run for S03.

## Implementation scope

1. Align declared Python support and Ruff target on CPython 3.12.
2. Add pinned direct verification tools and a **named, explicit mypy scope**; no global type-ignore.
3. Add a no-credentials, no-SDK, default-offline GitHub Actions job.
4. Close the existing partial-secret redaction leak (prefix/suffix leakage) and add privacy regressions for success/error metadata.
5. Document supported installs, validation order, known limitations and G1 decision rules.

## Pending verification / exclusions

- Ruff full-tree format needs the two known formatting fixes performed by the user with pinned Ruff; preserve a file-level diff.
- Mypy has not been executed in a supported Python 3.12 environment; diagnostics may require a follow-up targeted patch.
- CI has not run; a configuration file does not prove automated verification.
- Direct tool versions are pinned, but a complete transitive or hash-locked dependency resolution is not yet recorded. A fresh Windows clean-core and CI Linux resolution record is required.
- No provider code, SDK retry policy, agent, RAG, hosted deployment or production claim changes in this sprint.
- G1 is OPEN until **all** required proof has been assessed and the decision is recorded.
