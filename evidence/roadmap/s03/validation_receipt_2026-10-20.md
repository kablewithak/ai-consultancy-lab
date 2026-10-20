# S03 — Local acceptance evidence (2026-10-20)

**Sprint:** P1 / S03 — Credit-Independent Provider Execution
**Base:** S02 merge `2ea327de7aac75822be0375688a3979f88052e41`
**Working branch:** `feat/s03-credit-independent-provider`
**Evidence source:** User-provided terminal output in the 2026-10-20 implementation session, not independent execution by the reviewer.

## Outcome record

| Check | Evidence provided | Disposition |
| --- | --- | --- |
| Existing environment: Ruff lint/changed-file formatting, default test suite, SDK mock-contract tests and whitespace | User reported all checks passed before clean-core test | PASS (user-reported) |
| Fresh core environment: optional SDK absent | Printed `NO-SDK CHECK: PASS` | PASS |
| Fresh core environment: default unit tests | Initial run: 1 failure, 30 passed; failed because adapter imported absent `httpx` before optional `sie_sdk` | Defect found |
| No-SDK regression correction | Factory checks optional SDK availability before importing adapter; replacement tests added | Implemented; tests rerun |
| Clean-core and provider mock-contract regression after correction | Printed `S03 CLEAN CORE AND PROVIDER CONTRACTS: PASS` | PASS (user-reported) |
| SDK static compatibility | `sie-sdk 0.6.4`, all six required exception classes present, `encode` supports `output_types` and `is_query` | PASS for inspected static surface |
| Local SIE document encoding | `success`, requested model `sentence-transformers/all-MiniLM-L6-v2`, vector length 384 | PASS |
| Local SIE query encoding | `success`, same requested model, vector length 384 | PASS |
| Final live smoke | Printed `local_sie: PASS` and `S03 REAL BACKEND: PASS` | PASS |

## Live smoke summary

- The SIE server ran in Docker and was accessed over loopback at `http://127.0.0.1:8081`.
- Both `document` and `query` calls returned usable, validated 384-dimensional dense embeddings.
- `provider=superlinked` and `model=sentence-transformers/all-MiniLM-L6-v2` are the adapter/request identifiers; the SDK returned `reported_model=null` for both calls. **Independent provider-reported model identity was not established.**
- No raw vectors, input text, credentials, or model payloads are retained in this receipt.
- The smoke result demonstrates local inference without hosted Superlinked inference credits; it does not establish general zero operating cost (local compute and downloads still have costs).

## Acceptance boundary and remaining work

**S03 technical acceptance: PASS on supplied local evidence.** The code must still undergo exact staged-diff inspection and git/PR merge before the sprint is considered repository-integrated. G1 is **NOT PASSED**: S04 must qualify reproducible environment, static checks, CI and remaining regression conditions. Historical S02 final-check output was not independently supplied; S03 smoke and regression evidence only overlaps some of those checks.

The evidence does not establish service uptime, benchmarked throughput, offline model-download availability, provider-independent semantic equivalence, production readiness, retrieval quality, or protection for actual client data.
