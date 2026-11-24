# Wise Platform onboarding checklist — REBUKE EXCHANGE

Status: preparation checklist; no Wise credentials or live account connection are present.

## 1. Confirm business model with Wise

Contact Wise Platform at api@wise.com or the assigned Wise implementation contact. Request written confirmation of:

- Whether REBUKE EXCHANGE is eligible for Wise Platform partnership.
- Which model applies: Enterprise, Correspondent, or Embedded.
- Whether customer-connected accounts and the exchange's own operating account can both be supported under the proposed arrangement.
- Permitted corridors, currencies, customer types, jurisdictions, and transfer purposes.
- Whether REBUKE EXCHANGE's exchange activity, custody model (if any), marketplace/payout activity, or third-party payment flows are permitted.
- Required licensing, compliance, KYC/AML, safeguarding, disclosures, and operational controls.
- Required OAuth scopes, account/profile access, recipient, quote, transfer, webhook, and reconciliation permissions.
- Required mTLS, JOSE/JWS/JWE, SCA/2FA, IP allowlisting, and webhook verification configuration.

Do not infer regulatory or product approval from sandbox access.

## 2. Request Sandbox V2 access

- Request Sandbox V2 client ID and client secret from Wise's integration team.
- Request access to the Sandbox Developer Hub: https://wise-sandbox.com/developer-hub
- Confirm the redirect URI(s), webhook URL(s), integration model, and granted scopes.
- If mTLS is required, provision and store sandbox certificates separately.
- Use only synthetic test identities and data.
- Sandbox API base URL: https://api.wise-sandbox.com
- Sandbox mTLS API base URL, if enabled: https://api-mtls.wise-sandbox.com

Wise's V1 sandbox was deprecated after June 30, 2026. Do not build new work against V1 endpoints or reuse V1-only credentials.

## 3. Customer-connected onboarding

- Implement Wise-approved OAuth flow on the server.
- Use one-time state and nonce values; validate callback state and exact redirect URI.
- Use PKCE if required or supported for the selected flow.
- Persist the Wise customer/profile mapping only after validated callback completion.
- Store refresh tokens encrypted and access tokens only as long as required.
- Track granted scopes, authorization time, token expiry, and revocation state.
- Provide disconnect/revoke handling and remove access on customer request.
- Enforce tenant isolation for every read, quote, recipient, transfer, webhook, and reconciliation operation.

Wise must confirm the precise token model. Embedded partner integrations may use a different token model than Enterprise/Correspondent integrations.

## 4. Exchange operating account onboarding

- Identify the exchange's legal operating entity and authorized Wise business profile.
- Obtain Wise's written approval for the intended operating-account use case.
- Provision a separate operating principal and secret namespace.
- Do not reuse customer OAuth tokens or customer profile IDs.
- Define dual control for any future operating-account payment approval.
- Keep funding/submission disabled until a separate production release review.

## 5. Sandbox test plan

- Credential isolation: customer principal cannot read operating data and vice versa.
- OAuth state mismatch, expired code, denied consent, reconnect, and revoke.
- Token expiry and refresh handling.
- Scope denial and profile ownership mismatch.
- Quote creation and expiry.
- Recipient requirements and invalid recipient data.
- Draft transfer preparation with no funding call.
- Duplicate request and idempotency behavior.
- Webhook signature/authenticity verification, replay, duplicate, delayed, and out-of-order events.
- Customer/operating reconciliation partitioning.
- Audit completeness and redaction of tokens and bank details.
- Explicit negative tests proving all submit/fund routes are disabled.
- Run Wise's partner-provided implementation test plan.

Do not use Sandbox for load or performance testing; Wise states it is not supported there.

## 6. Production gate — not authorized by this document

Production requires all of the following, separately evidenced:

- Written Wise approval and production credentials.
- Legal/compliance sign-off for the actual REBUKE EXCHANGE business model.
- Security review of OAuth, secrets, mTLS/JOSE where required, webhooks, storage, and incident response.
- Passing test suite and Wise implementation acceptance.
- Customer disclosures and support/revocation process.
- Approved limits, monitoring, reconciliation, and operational runbooks.
- Explicit human release authorization.

Even after production approval, `WISE.TRANSFER.SUBMIT` must remain separately gated by a fresh, exact-intent approval. This checklist does not authorize money movement.

## Official Wise references

- Getting started: https://docs.wise.com/guides/developer
- Authentication and security: https://docs.wise.com/guides/developer/auth-and-security
- Environments: https://docs.wise.com/guides/developer/environments
- Sandbox V2 migration: https://docs.wise.com/guides/developer/environments/sandbox-v2-migration
