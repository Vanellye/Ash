# ERIA Red Write-Only Ethical Tools

**Status:** Draft security implementation; defensive, synthetic-fixture-only.

## Meaning of “write-only”

The toolkit may create new, narrowly scoped security reports, evidence manifests, and remediation proposals. It must not silently read secrets, modify existing source files, overwrite or delete records, execute generated content, or dispatch network/hardware/biological actions.

## Allowed output roots

- `reports/` — findings and test summaries
- `evidence-manifests/` — hashes and provenance metadata for non-secret evidence
- `proposals/` — human-reviewable remediation plans

Create-new only. Existing files are never overwritten or deleted.

## Upstream freshness and Log & Fix

- `tools/upstream_index.py` resolves the configured upstream ref live, compares it with an independently supplied pinned SHA, checks ancestry, and appends every outcome to a hash-chained JSONL rolling index.
- Every failed check is recorded as `DENY` with `next_action: LOG_AND_FIX`, a reason, and actionable remediation guidance. The raised `UpstreamVerificationError` carries the durable index record and remediation text to the caller.
- A successful freshness check is `ALLOW_CHECK_ONLY`; it is not human approval and does not authorize a mutation.
- Remediation is proposed, not silently applied. After repair, rerun verification. Any subsequent mutation still requires separate, valid human authorization.
- If the index cannot be appended or its chain is corrupt, the gate fails closed. It must not claim a durable log record where none was written.

## Shared execution boundary and storage enforcement

- `tools/validate_policy.py` is the pure path/operation policy validator.
- `tools/execution_boundary_guard.py` requires a scoped, time-bounded, non-revoked human grant, a trusted grant verifier, and a live upstream verifier on every authorization attempt.
- `tools/storage_adapter.py` is the filesystem mutation boundary. It creates new files only beneath approved output roots, uses no-follow directory traversal and exclusive creation, and denies overwrites, symlinks, and out-of-scope paths.
- `tests/test_storage_adapter.py` and `tests/test_upstream_index.py` exercise the boundaries using synthetic fixtures.
- `.github/workflows/eria-write-only-boundary.yml` runs the isolated test suite in CI.

### Production requirements

Wire the live verifier with a pinned SHA from a separately trusted event, not from the mutable checkout being checked. Independently anchor rolling-index head hashes in a separately administered append-only store or transparency service. The local hash chain alone is not independently tamper-proof. Configure the trusted human-grant verifier and revocation source before production use.

## Explicitly denied

Secret extraction, credential harvesting, shell execution, dynamic evaluation, exploit payloads, source-tree mutation, overwrite/delete, network/webhook dispatch, hidden execution, hardware activation, and biological intervention.

The write-only component emits inert artifacts; it does not execute them. A separate read/scan component would need its own authorization and data-minimization controls.

## Evidence discipline

Preserve original artifacts and append corrections. Findings are hypotheses until verified. Never treat a glyph, test pass, or freshness check as human authorization.
