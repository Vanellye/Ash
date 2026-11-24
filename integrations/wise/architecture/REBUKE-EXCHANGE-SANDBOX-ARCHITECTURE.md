# REBUKE EXCHANGE — Wise dual-scope sandbox architecture

Status: design specification; not a live integration.

## Objective

Support two distinct Wise relationship scopes without mixing ownership, credentials, consent, or authority:

1. **Customer-connected scope** — each customer authorizes REBUKE EXCHANGE through the Wise-approved partner onboarding and OAuth model. Every customer authorization is bound to that customer's Wise identity/profile and the scopes approved for the integration.
2. **Exchange operating scope** — the exchange's own legal business uses a separately onboarded Wise business/partner relationship for its own treasury and operating payments. It is never represented as a customer account.

Wise must confirm the correct partner integration model (Enterprise, Correspondent, or Embedded) and permitted use cases during onboarding. Do not assume that customer linking, custody, pooled funds, marketplace payouts, or exchange treasury activity is approved merely because an API endpoint exists.

## Environment boundary

- Sandbox API base URL: https://api.wise-sandbox.com
- Sandbox mTLS API base URL, if provisioned: https://api-mtls.wise-sandbox.com
- Production API base URL: https://api.wise.com
- Production mTLS API base URL, if provisioned: https://api-mtls.transferwise.com

Sandbox and production credentials, tokens, certificates, callback URLs, webhook secrets, data stores, and deployment variables must be separate. Sandbox accepts test data only; it is not a load/performance test environment and does not move real money.

## Logical components

- **Wise API Gateway** — server-side adapter; environment selected from an allowlisted configuration, never a user-supplied URL.
- **Customer Authorization Service** — OAuth state/nonce/PKCE handling as required by Wise's approved flow; maps Wise subject/profile identifiers to a local customer and records consent, scopes, issued-at, expiry, and revocation.
- **Operating Account Service** — separate principal and credential namespace for the exchange's own approved Wise profile.
- **WiseTags Policy Engine** — default deny; evaluates principal, action, environment, resource owner, amount/currency limits, purpose, expiry, and approval evidence.
- **Transfer Preparation Service** — validates quote, recipient, requirements, and draft transfer data; cannot fund or submit.
- **Webhook Intake** — verifies authenticity/signatures as specified by Wise, deduplicates events, stores event provenance, and processes asynchronously.
- **Audit Ledger** — append-only event records for authorization, policy decisions, quote/recipient/transfer preparation, webhook receipt, reconciliation, and human approvals.
- **Reconciliation Worker** — compares locally recorded prepared/status data with Wise API and webhook observations; produces discrepancy reports, never initiates corrective money movement.

## Identity and credential separation

Use two namespaces at minimum:

- `WISE_CUSTOMER_<internal_customer_id>`
- `WISE_OPERATING_ENTITY`

Never share refresh tokens, access tokens, client secrets, private keys, or mTLS certificates across these namespaces. Partner client credentials identify the integration; customer authorization tokens identify the customer context where the selected Wise model requires them. The exchange operating profile must be explicitly provisioned and authorized by Wise.

All secrets remain server-side in a managed secret store. Never put credentials in browser/mobile bundles, Git, logs, URLs, issue comments, or chat. Encrypt refresh tokens at rest, redact authorization headers, rotate credentials, and support revocation.

## Initial sandbox capability matrix

| Capability | Customer scope | Operating scope | Initial state |
|---|---|---|---|
| OAuth connect/disconnect | Yes, after Wise partner approval | Not applicable unless Wise requires it | Sandbox only |
| Profile/account discovery | Only authorized profile data | Only approved operating profile | Read-only |
| Unauthenticated indicative quote | Yes | Yes | Sandbox |
| Authenticated quote | If approved by model/scopes | If approved by model/scopes | Prepare only |
| Recipient requirements/validation | Customer-authorized context | Operating context | Prepare only |
| Recipient creation | Only after policy and test approval | Only after policy and test approval | Sandbox gated |
| Draft transfer creation | Only after explicit sandbox test approval | Only after explicit sandbox test approval | Sandbox gated |
| Fund/submit transfer | No | No | Disabled |
| Status/webhook tracking | Authorized records only | Operating records only | Sandbox |
| Reconciliation | Per-customer partition | Separate operating partition | Report only |

## WiseTags actions

- `WISE.READ`
- `WISE.CUSTOMER.CONNECT`
- `WISE.BENEFICIARY.VERIFY`
- `WISE.QUOTE.PREPARE`
- `WISE.TRANSFER.PREPARE`
- `WISE.TRANSFER.REVIEW`
- `WISE.TRANSFER.APPROVE`
- `WISE.TRANSFER.SUBMIT` — disabled and unavailable in this phase
- `WISE.RECONCILE`
- `WISE.AUTH.REVOKE`

A policy grant is not a Wise credential and must not be accepted as a substitute for Wise authentication. Approval is bound to an immutable transfer-intent digest (principal, source profile, recipient, amount, currency, quote, fees, purpose, expiry, idempotency/customer transaction ID). Any material change invalidates the approval.

## Mandatory invariants

1. Default deny; unknown action, principal, profile, currency, or environment is denied.
2. Customer data and operating-entity data are tenant-isolated in storage, logs, queues, caches, and reconciliation.
3. No cross-customer token use or profile substitution.
4. No browser/mobile exposure of Wise secrets.
5. No live endpoint can be selected in sandbox builds; production configuration is absent until separately approved.
6. Transfer funding/submission code paths are not implemented or callable in this phase.
7. Idempotency keys and duplicate-event handling are required for create operations and webhooks.
8. Every decision has a correlation ID, policy version, actor, timestamp, and evidence reference.
9. Revocation blocks future API use and marks existing sessions/tokens for invalidation according to Wise's token lifecycle.
10. Sandbox data is synthetic only.

## Deployment shape

Client app -> REBUKE API -> Wise API Gateway -> Wise Sandbox V2.

The client never calls Wise with a partner secret. OAuth redirects terminate at a server callback. Background workers use a queue with tenant-scoped messages. Database row-level controls or equivalent service-layer enforcement isolate customer and operating principals.

## Out of scope

Production enablement, real customer onboarding, custody, pooled balances, exchange settlement, real transfers, funding, automatic FX conversion, and performance/load testing. Each requires separate Wise confirmation, legal/compliance review, security review, and explicit release authorization.
