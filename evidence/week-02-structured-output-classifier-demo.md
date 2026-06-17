# Week 2 Evidence — Structured Output Classifier Demo

## Slice

`feat/structured-output-classifier-demo`

## Purpose

Prove the Week 2 structured-output contract layer can be used by an applied component, not only as abstract schemas.

The demo is intentionally small. It validates classifier-like model output and a deterministic rule-based classifier through the same strict boundary:

```text
raw output -> Pydantic contract -> success | validation_error | unsupported
```

## Files

```text
packages/structured_outputs/examples.py
tests/unit/structured_outputs/test_examples.py
evidence/week-02-structured-output-classifier-demo.md
```

`packages/structured_outputs/__init__.py` is updated to export the demo contract and helper functions.

## Behavior Proved

The demo proves:

- valid route labels parse into a typed `RequestClassification`
- unknown labels fail safely as `validation_error`
- extra fields are rejected at the schema boundary
- sensitive extra fields are not persisted inside validation envelopes
- low-confidence classifications become explicit `unsupported` states
- ambiguous requests are escalated instead of treated as known
- retry decisions do not loop on non-retryable low-confidence states

## Route Taxonomy

```text
rag_reliability
agent_harness
eval_harness
privacy_security
structured_outputs
human_review
```

The taxonomy is deliberately small and local to this demo. It is not yet the final Tech-Spec Router taxonomy.

## Validation Commands

Targeted structured-output suite:

```powershell
python -m pytest tests\unit\structured_outputs -q
```

Expected new total for this package-level suite after this slice:

```text
21 passed
```

Full repo suite:

```powershell
python -m pytest
```

Run this in the user's local `.venv`, where repo dependencies such as `sie-sdk` are installed.

## Privacy / Security Notes

- Raw classifier payloads are not stored in validation envelopes.
- Extra fields such as `api_key` are rejected.
- The test suite asserts that secret-like extra-field values do not appear in serialized validation envelopes.
- Low-confidence states are explicit and do not become silent guesses.

## Non-Claims

This slice does not prove:

- production classifier quality
- final routing taxonomy quality
- RAG reliability
- agent reliability
- customer-data readiness
- production readiness

## Commercial Translation

This strengthens the AI System Evaluation Audit and future router/agent capstones by proving a reusable pattern:

```text
model-like output must become a deterministic contract before software uses it.
```

This is the same pattern future buyer-facing systems need when classifying requests, scoring answers, routing support cases, producing audit findings, or validating agent tool plans.
