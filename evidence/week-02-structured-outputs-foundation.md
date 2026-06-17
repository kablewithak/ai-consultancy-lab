# Week 02 Evidence: Structured Outputs Foundation

## Summary

This evidence note records the Week 2 structured-output foundation for `ai-consultancy-lab`.

The goal is to create deterministic model-output contracts before building RAG, eval, and agent capstones.

```text
Probabilistic model output must become a validated software contract before downstream code can trust it.
```

## What Was Added

```text
packages/structured_outputs/
  __init__.py
  contracts.py

tests/unit/structured_outputs/
  test_contracts.py
```

## Core Contracts

The package adds:

```text
StrictOutputModel
BaseResult
StructuredOutputStatus
StructuredOutputErrorCode
ValidationIssue
ValidationErrorEnvelope
Refusal
UnsupportedAnswer
OutputParseResult
RetryDecision
parse_model_output
retry_decision_for_failure
```

## Design Decisions

### Extra fields are forbidden

`StrictOutputModel` uses Pydantic v2 with `extra="forbid"`.

This prevents model outputs from quietly smuggling unsupported fields across deterministic boundaries.

### Raw output is not stored in validation envelopes

`ValidationErrorEnvelope` stores validation issues and the raw output type, not the raw output payload.

Reason:

```text
Raw model output may contain prompts, documents, customer data, secrets, or other sensitive payload fragments.
```

### Refusal and unsupported answers are explicit states

The system distinguishes:

```text
refusal
unsupported_answer
validation_error
success
```

This prevents downstream code from treating all failures as generic exceptions.

### Retry decisions are bounded

`retry_decision_for_failure` retries only when the failure is retryable and retry budget remains.

When the retry limit is reached, the decision escalates rather than looping.

## Validation

Run targeted tests:

```powershell
python -m pytest tests\unit\structured_outputs\test_contracts.py -q
```

Run the full suite:

```powershell
python -m pytest
```

Expected coverage:

- valid model output becomes a typed success result
- extra fields fail safely
- invalid confidence values fail safely
- validation envelopes do not store raw secret-like values
- refusal is explicit and non-retryable
- unsupported answers can record missing evidence
- unsupported-answer error codes are constrained
- parse-result invariants are enforced
- retryable validation errors retry while budget remains
- retry limit escalates instead of looping
- refusals are not retried

## What This Proves

This proves:

```text
The repo has a reusable structured-output boundary.
Invalid model-shaped data can fail safely.
Failures are machine-readable.
Refusal and unsupported-answer states are first-class.
Retry/escalation decisions are bounded.
Validation errors avoid storing raw model outputs.
```

## What This Does Not Prove

This does not prove:

```text
RAG reliability
retrieval improvement
agent reliability
customer-data readiness
production readiness
LLM provider output quality
```

## Commercial Translation

This strengthens the AI System Evaluation Audit because it provides a concrete way to inspect whether an AI product has deterministic output contracts.

It strengthens the RAG Reliability Improvement Sprint because future grounded answers can use explicit answer/refusal/unsupported states.

It strengthens the Agent Harness Hardening Sprint because future tool calls and agent actions can use the same validation and retry/escalation discipline.

## Maturity Label

```text
production-shaped structured-output contract layer,
locally unit-tested,
not RAG-ready,
not customer-data tested,
not production-ready
```
