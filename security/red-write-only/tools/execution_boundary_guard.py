"""Shared, provider-neutral authorization boundary for ERIA output creation."""
from dataclasses import dataclass
import time
from typing import Callable, Optional

from .validate_policy import ALLOWED_PREFIXES, authorize_output


@dataclass(frozen=True)
class AuthorizationGrant:
    """Claims supplied by a trusted human-approval authority.

    The signature is opaque here. The injected verifier MUST validate its
    authenticity and current revocation state; this module does not mint grants.
    """
    actor: str
    approval_ref: str
    operation: str
    output_prefix: str
    expires_at: int
    source_revision: str
    human_approved: bool
    revoked: bool
    signature: str


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    reason: str


class ExecutionBoundaryGuard:
    """Deny-by-default gate; upstream freshness is checked on every authorize call."""

    def __init__(
        self,
        grant_verifier: Callable[[AuthorizationGrant], bool],
        upstream_verifier: Callable[[], object],
    ):
        if not callable(grant_verifier):
            raise TypeError("a trusted grant_verifier is required")
        if not callable(upstream_verifier):
            raise TypeError("a live upstream_verifier is required")
        self._verify = grant_verifier
        self._verify_upstream = upstream_verifier

    def authorize(self, operation: str, path: str,
                  grant: Optional[AuthorizationGrant], now: Optional[int] = None) -> GuardDecision:
        allowed, reason = authorize_output(operation, path)
        if not allowed:
            return GuardDecision(False, reason)
        if grant is None:
            return GuardDecision(False, "human_authorization_required")
        if not grant.human_approved:
            return GuardDecision(False, "human_approval_missing")
        if grant.revoked:
            return GuardDecision(False, "authorization_revoked")
        if not grant.actor or not grant.approval_ref or not grant.source_revision:
            return GuardDecision(False, "authorization_audit_fields_missing")
        if grant.operation != operation:
            return GuardDecision(False, "authorization_operation_mismatch")
        if grant.output_prefix not in ALLOWED_PREFIXES or not path.startswith(grant.output_prefix):
            return GuardDecision(False, "authorization_scope_mismatch")
        if grant.expires_at <= (int(time.time()) if now is None else now):
            return GuardDecision(False, "authorization_expired")
        try:
            if not self._verify(grant):
                return GuardDecision(False, "authorization_verification_failed")
        except Exception:
            return GuardDecision(False, "authorization_verification_failed")
        # Resolve upstream immediately before returning permission to the storage boundary.
        try:
            upstream_result = self._verify_upstream()
            if upstream_result is False:
                return GuardDecision(False, "upstream_verification_failed")
            if isinstance(upstream_result, dict) and upstream_result.get("decision") != "ALLOW_CHECK_ONLY":
                return GuardDecision(False, "upstream_verification_failed")
        except Exception:
            return GuardDecision(False, "upstream_verification_failed")
        return GuardDecision(True, "authorized_create_only_upstream_verified")
