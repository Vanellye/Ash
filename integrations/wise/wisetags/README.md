# WiseTags — ERIA Authorization Adapter

**Status:** Design/specification only; no Wise credentials, API calls, transfers, or live account access are configured.
**Policy:** ERIA Ethics Attachment 1.0.0
**Default mode:** `PREPARE_ONLY` / deny by default

WiseTags are Vanellye/Ash authorization labels for requests that may interact with a Wise account. They are not represented as native Wise features. A tag is a requested capability, not proof of approval and not an execution command.

## Capability tags

| Tag | Scope | Result |
|---|---|---|
| `WISE.READ` | Read-only account/balance data | Read request; separate Wise API permission still required |
| `WISE.BENEFICIARY.VERIFY` | Verify beneficiary details | Verification result; never changes beneficiary |
| `WISE.TRANSFER.PREPARE` | Build a transfer draft/quote | Draft only; no submission |
| `WISE.TRANSFER.REVIEW` | Submit an exact request for review | Review record |
| `WISE.TRANSFER.APPROVE` | Approve exact immutable request digest | Approval grant only |
| `WISE.TRANSFER.SUBMIT` | Submit one previously approved exact transfer | Disabled until a separately reviewed live adapter is implemented |
| `WISE.RECONCILE` | Read transfer status and reconcile evidence | Read-only reconciliation |
| `WISE.LIMIT.CONFIGURE` | Propose a limit change | Proposal only; applying limits requires a separate provider capability and approval |

## Centralized decision path

All Wise actions must enter one policy decision point. Do not create parallel tag-specific authorization implementations.

1. Parse and validate the request and capability tag.
2. Resolve actor, Wise account identifier, beneficiary, currency, amount, fee/quote, and immutable request digest.
3. Check policy version, least-privilege scope, expiry, revocation, replay protection, and independent approval requirements.
4. Emit an append-only ALLOW/DENY audit event with no secrets or credentials.
5. For this initial release, allow only read/prepare/review operations in a future explicitly configured adapter. No live provider calls are enabled by this specification.
6. Treat approval as bound to the exact digest, account, beneficiary, amount, currency, operation, and expiry. Any change invalidates it.

## Transfer submission gate

`WISE.TRANSFER.SUBMIT` is deliberately disabled. It must remain disabled until all of the following are independently implemented and verified:

- authentic Wise API integration and documented provider scopes;
- trusted human-approval issuer and signature/revocation verification;
- independent reviewer identity and separation from requester;
- exact-digest approval, one-time nonce/idempotency, expiry, and replay rejection;
- beneficiary verification and amount/currency/fee/limit checks;
- provider-side status reconciliation and failure handling;
- isolated tests and a reviewed threat model.

Even after implementation, no autonomous, scheduled, webhook, retry, or background process may create its own approval. A user must explicitly confirm the exact transfer at the final execution boundary.

## Safeguard consolidation / purge policy

This change centralizes Wise-specific authorization semantics; it does **not** delete the repository's existing ERIA safeguards. Existing controls are retained until a path-by-path review proves a control is redundant, identifies its replacement, and passes regression tests. No broad deletion or weakening is authorized by this specification.

## Current implementation boundary

- No Wise credentials or tokens stored here.
- No account discovery or personal financial data access.
- No transfer creation, submission, cancellation, or beneficiary mutation.
- No production adapter or webhook.
- `policy.json` is a declarative policy contract, not an enforcement engine.
- The existing `security/red-write-only/tools/execution_boundary_guard.py` remains the shared provider-neutral gate for its documented create-only storage boundary; it is not claimed to authorize Wise API calls.

## Required tests before live integration

Test missing/invalid/expired/revoked approvals; requester self-approval; wrong reviewer; altered amount, currency, beneficiary, account, or quote; duplicate/replayed request; expired quote; over-limit amount; provider timeout; partial/unknown provider result; and audit-sink failure. All ambiguous or unverifiable outcomes must HOLD/DENY and require reconciliation before retry.
