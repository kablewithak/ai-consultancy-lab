# G1 — Provider-neutral foundation acceptance review

**Date:** 2026-10-20
**Repository:** `kablewithak/ai-consultancy-lab`
**Phase:** P1 — Provider-neutral foundation
**Gate:** G1 — Foundation qualification
**Reviewed revision:** `main` merge commit `2cc0e28ac660d6e974f81226765760db37ce6f33` (PR #8)
**Owner:** Repository owner / technical decision-maker
**Review source:** GitHub repository and CI observations, plus user-supplied local CLI evidence
**Decision:** **PASS — G1 technical foundation qualified within the explicitly declared CPython 3.12 scope.**

## 1. Claim being assessed

For the **declared CPython 3.12, single-process, locally exercised foundation**, Lab-owned embedding and structured-output contracts can be tested without an installed provider SDK or hosted credentials, while an explicitly selected local Superlinked SIE backend can return validated dense document/query vectors. Fresh Windows and Linux test environments run the core verification checks. This is **not** RAG reliability, model quality, production, customer-data, or multi-provider portability certification.

G1's governing exit evidence in the north-star plan is: usable vector/result contracts, no-credit core tests, real-backend smoke/integration proof, typed failures, and reproducible checks. S04's runbook also requires the SDK-enabled provider contract regression on the final S04 candidate. The user-supplied final run on merged `main` now satisfies that requirement. This acceptance is limited to the observed and recorded operating surfaces.

## 2. Evidence register

| Requirement | Evidence and revision | Decision |
| --- | --- | --- |
| G0 factual baseline | S01/G0 closeout: clean baseline commit `3631ab01feabb6fc0246e95a364b5a9c64f292c8`; Python 3.12, 34 initial unit tests, historical format/mypy gaps documented | PASS, baseline scope only |
| Typed usable dense vector | S02 PR #6, merge `2ea327de7aac75822be0375688a3979f88052e41`; `EmbeddingResponse` and SDK adapter expose validated numeric vectors, dimensions, task metadata and explicit optional provider-reported model identity | PASS for implemented contract and tests; historical S02 standalone final-run output not supplied |
| Typed error/fail-closed policy | S02 unit contract cases distinguish generic unavailable vs confirmed loading, auth, quota, rate limits, malformed response and non-retryable outcomes; no application-level automatic retry loop | PASS for covered cases; real error taxonomy not exhaustively fault-injected |
| SDK-independent core | S03 PR #7, merge `7dd7a0eba81409ac791af810a98cf4cf4f3b850a`; clean Windows venv printed `NO-SDK CHECK: PASS`; corrected missing-`httpx` trap; reported `S03 CLEAN CORE AND PROVIDER CONTRACTS: PASS` | PASS on supplied local evidence |
| Real backend | S03 local Docker SIE; `sie-sdk==0.6.4` static-symbol preflight PASS; local document and query `sentence-transformers/all-MiniLM-L6-v2` calls both SUCCESS with 384-dimensional vectors, `local_sie: PASS`, `S03 REAL BACKEND: PASS` | PASS for current local backend procedure, not for all deployment modes |
| Reproducible clean Windows run | S04 Windows receipt: clean `.[dev]` install, no SDK, `pip check`, Ruff check/format, mypy seven-source-file scope, **36 passed in 1.32s** | PASS for recorded Windows dependency resolution |
| CI independent Linux run | S04 PR #8, head `63dbb4b91a762060d23f033b0be213575a4f02fa`; GitHub Actions run **39429635540**, job `offline-core`, **success**, including no-SDK assertion, Ruff, mypy, pytest | PASS for that PR head; exact main merge commit is `2cc0e28ac660d6e974f81226765760db37ce6f33` |
| Safe telemetry/privacy boundary | S04 masking of secret field values and four new privacy-focused tests; default network-deny pytest fixture | PASS for tested controls; not a comprehensive privacy audit |
| Final SDK-enabled regression on S04 | On clean merged `main` at `2cc0e28ac660d6e974f81226765760db37ce6f33`, user-supplied output: `sie-sdk version: 0.6.4`; all six SDK error types and both encode options present; `S02 SDK compatibility: static surface PASS`; `pytest -q tests/provider/superlinked`: **46 passed in 1.60s**; `G1 FINAL PROVIDER VERIFICATION: PASS`. | **PASS** for SDK static surface and provider mock-contract tests; no claim of exhaustive live exception semantics |

**Links:** [PR #6](https://github.com/kablewithak/ai-consultancy-lab/pull/6), [PR #7](https://github.com/kablewithak/ai-consultancy-lab/pull/7), [PR #8](https://github.com/kablewithak/ai-consultancy-lab/pull/8), [successful S04 CI run](https://github.com/kablewithak/ai-consultancy-lab/actions/runs/39429635540).

## 3. Final provider-regression closure (2026-10-20)

**Evidence provenance:** User-pasted PowerShell console output. The reviewer verified the referenced merged GitHub commit and the successful PR-triggered Linux CI separately; the local Windows CLI execution was not independently observed by the reviewer. The local run was performed on clean `main` synced to the exact S04 merge SHA:

```text
## main...origin/main
2cc0e28 (HEAD -> main, origin/main, origin/HEAD) Merge pull request #8 from kablewithak/feat/s04-reproducible-verification
sie-sdk version: 0.6.4
SDK errors present: ModelLoadingError, ProvisioningError, RequestError, ServerError, SIEConnectionError, SIEError
encode options present: output_types, is_query
missing error classes: none
missing encode options: none
S02 SDK compatibility: static surface PASS; runtime exception semantics need tests.
46 passed in 1.60s
G1 FINAL PROVIDER VERIFICATION: PASS
```

**Interpretation:** The SDK import/static API surface meets the pinned interface requirements, and all 46 provider-only mock-contract tests pass on the merged S04 revision. Provider exception mapping is exercised by contract tests; this is not proof that every real deployment failure mode has been induced and observed live. S03 separately recorded a successful local real SIE document/query smoke; repeating Docker would not provide a missing G1 evidence category because no functional provider behavior changed in S04.

**Gate reconciliation:** S01/G0 baseline, S02 typed-vector and failure contracts, S03 SDK-independent development and local real inference, S04 clean Windows/no-SDK regression and Linux CI, and the final SDK-enabled regression are all accepted at their declared scopes. No mandatory G1 check remains blocked. The G1 decision may be recorded **PASS** in the repository; S05 is eligible after this record is merged. No later capability may infer production, semantic quality, data rights or customer acceptance from G1.

## 4. Residual risk register and acceptance decisions

1. **Dependency determinism — accepted limitation within the G1 scope.** Core ranges and transitive packages are not hash-locked. Fresh Windows and Linux installations succeeded; direct verifier dependencies are pinned. This proves *tested current resolutions*, not bit-for-bit rebuilds. A fully locked requirements workflow must be decided before a stronger reproducibility or release claim.
2. **Type checking — accepted bounded scope.** Mypy passes for seven declared application source files, not the complete repository or SDK adapter. Additional boundaries require expansion as they become depended upon.
3. **Provider/model metadata — accepted limited scope.** Local SIE returned `reported_model=null`; requested model and returned vector shape were validated but independently reported provider model revision was not confirmed. Fingerprint model and preprocessing/index assumptions when retrieval is introduced.
4. **S02 standalone evidence — traceability caveat.** The historic S02 final local log is absent. Subsequent S03 contract regression and live local smoke cover relevant behavior, but are not retroactively represented as the missing run.
5. **No customer authorization or operational guarantee.** Synthetic tests only. There is no customer-data approval, hosted provider budget, SLA, production deployment, load/cost claim, retrieval score or calibrated semantic quality proof.
6. **Actual schedule effort — not recorded.** The owner-confirmed 35 h/week capacity and 26 h planned + 9 h reserve are planning assumptions, not measured hours. Do not manufacture an S05 calendar forecast; capture actual S01–S04 effort when available.

Items 1–6 do not invalidate this narrowly scoped technical foundation now that the final SDK-enabled test has passed. They remain explicit limitations and requalification triggers.

## 5. Requalification triggers

- Change to SDK version, transport, adapter error taxonomy or provider connection semantics: rerun typed provider contracts and live integration where affected.
- Change to embedding model, preprocessing or document/query mode: rerun embedding boundary checks; later index compatibility and retrieval metrics under G3/G4.
- Change to core dependency resolver or Python minor version: fresh no-SDK install plus Ruff/mypy/default tests; inspect dependency diff.
- Change to safe logging/privacy envelope: rerun trace and privacy negative cases.
- Change to required CI conditions: verify a new successful CI run on the exact proposed revision.

## 6. Next eligible work

**S05 — Corpus and evaluation-data contracts (P2/G2)** is eligible **after this PASS record is committed and merged**. It must not be confused with G2 acceptance.

S05's *first* scoped job is selecting a small permitted, versioned dirty-document corpus for the first retrieval capstone, defining source and document/chunk manifests, data rights, freshness, sensitive-data exclusions and reviewed diagnostic questions. Include representative, challenge and transfer slices. No retrieval tuning, hosted provider spend or fabricated LLM-generated ground truth. S06 then builds scorers, run manifests and protected evaluation splits; G2 is not passed until those controls are tested.

## 7. Decision authority

This record is an evidence-based technical gate review prepared by the assistant using inspected GitHub state/CI plus explicitly identified user-supplied Windows verification. **Technical G1 decision: PASS for the stated foundation scope.** The repository owner remains the acceptance authority and can ratify this decision by reviewing and merging the documentation-only closeout PR. Acceptance does not authorize production or sensitive client-data use.
