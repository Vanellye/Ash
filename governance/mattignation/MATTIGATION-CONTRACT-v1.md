# Mattignation Governance Contract v1

Mattignation combines information **maturation** and **mitigation** into one evidence-preserving lifecycle. This contract adopts the ERIA human-authority principles already present in this repository; it supplements, and does not replace, existing ethics or red-write-only policies.

## Relationship to existing controls

- Existing default-deny behavior remains authoritative.
- Existing create-only scope remains authoritative.
- No secret access, overwrite, deletion, shell execution, external dispatch, deployment, fund transfer, or hardware actuation is granted.
- Validation and eligibility are not authorization.
- Human approval must be explicit, attributable, scoped, time-bounded, revocable, and bound to the exact operation digest.
- Independent review remains independent; requester self-approval cannot satisfy it.

## Maturation controls

Information progresses through RECEIVED, NORMALIZED, CLASSIFIED, ENRICHED, CORROBORATED, VALIDATED, and PUBLISHED. Each transition records actor, timestamp, source digest, schema/policy version, method, and decision.

The engine distinguishes OBSERVED, REPRODUCED, CORROBORATED, INFERRED, HYPOTHESIS, SIMULATED, and UNKNOWN. In particular, simulated output is never described as physical measurement.

## Mitigation controls

The engine identifies and records:
- missing or unverifiable provenance;
- conflicting claims and evidence dependence;
- stale or context-expired information;
- unsupported certainty and unstated assumptions;
- privacy/security exposure;
- unsafe use outside declared purpose;
- schema or model drift.

Mitigation actions are non-destructive by default: flag, quarantine, redact a derived view, restrict eligibility, or propose a correction. Corrections append a new linked record and preserve previous records.

## Decision and audit model

Decision states are distinct: PROPOSED → VALIDATED → ELIGIBLE → HUMAN_APPROVED → EXECUTED → AUDITED. Any material change to target, payload, scope, operation, or risk invalidates approval and requires new review. Denial, timeout, missing evidence, ambiguity, or verification failure means BLOCKED.

Audit records are append-only and must identify event ID, time, actor, operation, target, decision, reason, source revision/digest, policy version, and authorization reference. Do not record secret values or secret fingerprints.

## Cross-repository exchange

Lumi is the canonical general-purpose information schema and lifecycle definition. Ash consumes compatible records and adds governance checkpoints. Exchange is read-only by default. Every exchange includes repository identity, commit, schema version, content digest, and purpose. No automatic reciprocal repository write is permitted.

## Rollout gate

A production adoption claim requires:
1. implemented validators and deterministic tests;
2. synthetic fixture coverage for all states and failure modes;
3. audit integrity and lineage verification;
4. privacy and authorization review;
5. human sign-off for the specific deployment.

This file defines governance requirements; it does not certify that runtime components or production integrations are active.
