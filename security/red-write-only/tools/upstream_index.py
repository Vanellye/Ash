"""Fail-closed upstream freshness gate with a hash-chained rolling index.

Call verify_upstream_before_mutation immediately before each consequential
mutation. The upstream tip is resolved live; the expected SHA must come from
a separately trusted event/base reference. The index records decisions only:
it is not an approval token and does not authorize the mutation.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Callable

_SHA = re.compile(r"^[0-9a-f]{40,64}$")


class UpstreamVerificationError(RuntimeError):
    pass


def resolve_remote_ref(upstream_url: str, upstream_ref: str) -> str:
    """Resolve exactly one remote ref without invoking a shell."""
    if not upstream_url.startswith(("https://", "ssh://", "git@")):
        raise UpstreamVerificationError("upstream_url_scheme_denied")
    if not upstream_ref or upstream_ref.startswith("-") or any(c.isspace() for c in upstream_ref):
        raise UpstreamVerificationError("invalid_upstream_ref")
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--exit-code", upstream_url, upstream_ref],
            check=True, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise UpstreamVerificationError("upstream_resolution_failed") from exc
    rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != upstream_ref:
        raise UpstreamVerificationError("upstream_ref_missing_or_ambiguous")
    sha = rows[0][0].lower()
    if not _SHA.fullmatch(sha):
        raise UpstreamVerificationError("invalid_upstream_sha")
    return sha


def is_ancestor(base_sha: str, head_sha: str) -> bool:
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_sha, head_sha],
            check=True, capture_output=True, timeout=10,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except (OSError, subprocess.SubprocessError) as exc:
        raise UpstreamVerificationError("local_ancestry_check_failed") from exc


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _load_and_validate_index(stream) -> tuple[int, str]:
    stream.seek(0)
    previous = "GENESIS"
    sequence = 0
    for raw in stream:
        if not raw.endswith(b"\n"):
            raise UpstreamVerificationError("index_has_incomplete_tail")
        try:
            record = json.loads(raw)
            supplied = record.pop("record_sha256")
        except (ValueError, KeyError, TypeError) as exc:
            raise UpstreamVerificationError("index_record_invalid") from exc
        if record.get("sequence") != sequence + 1 or record.get("previous_record_sha256") != previous:
            raise UpstreamVerificationError("index_chain_discontinuity")
        calculated = hashlib.sha256(_canonical(record)).hexdigest()
        if supplied != calculated:
            raise UpstreamVerificationError("index_record_hash_mismatch")
        sequence += 1
        previous = supplied
    return sequence, previous


def _append_index(index_path: str, decision: dict) -> dict:
    """Append one tamper-evident record; fail closed if index cannot be updated."""
    path = Path(index_path)
    flags = os.O_RDWR | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "r+b", closefd=False) as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            stream.seek(0)
            data = stream.read()
            from io import BytesIO
            sequence, previous = _load_and_validate_index(BytesIO(data))
            record = {
                "sequence": sequence + 1,
                "previous_record_sha256": previous,
                **decision,
            }
            record["record_sha256"] = hashlib.sha256(_canonical(record)).hexdigest()
            stream.seek(0, os.SEEK_END)
            stream.write(_canonical(record) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
            return record
    finally:
        os.close(fd)


def verify_upstream_before_mutation(
    *,
    upstream_url: str,
    upstream_ref: str,
    expected_upstream_sha: str,
    current_head_sha: str,
    index_path: str,
    resolver: Callable[[str, str], str] = resolve_remote_ref,
    ancestry_check: Callable[[str, str], bool] = is_ancestor,
) -> dict:
    """Refresh upstream, compare pinned base, verify ancestry, and index outcome.

    Invoke immediately before mutation. Stop on any exception or DENY decision.
    The result is check-only and never constitutes human approval.
    """
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp_utc": int(time.time()),
        "upstream_url": upstream_url,
        "upstream_ref": upstream_ref,
        "expected_upstream_sha": expected_upstream_sha.lower(),
        "current_head_sha": current_head_sha.lower(),
    }
    decision, reason, observed = "DENY", "verification_not_completed", ""
    try:
        if not _SHA.fullmatch(event["expected_upstream_sha"]):
            raise UpstreamVerificationError("expected_upstream_sha_invalid")
        if not _SHA.fullmatch(event["current_head_sha"]):
            raise UpstreamVerificationError("current_head_sha_invalid")
        observed = resolver(upstream_url, upstream_ref).lower()
        if not _SHA.fullmatch(observed):
            raise UpstreamVerificationError("observed_upstream_sha_invalid")
        if observed != event["expected_upstream_sha"]:
            raise UpstreamVerificationError("upstream_moved_since_pinned_base")
        if not ancestry_check(observed, event["current_head_sha"]):
            raise UpstreamVerificationError("current_head_does_not_contain_upstream")
        decision, reason = "ALLOW_CHECK_ONLY", "upstream_fresh_and_ancestor"
    except Exception as exc:
        reason = str(exc) if isinstance(exc, UpstreamVerificationError) else "verification_error"
    event.update({
        "observed_upstream_sha": observed,
        "decision": decision,
        "reason": reason,
    })
    # If the index cannot record the result, no allow result is returned.
    record = _append_index(index_path, event)
    if decision != "ALLOW_CHECK_ONLY":
        raise UpstreamVerificationError(reason)
    return {"decision": decision, "reason": reason, "index_record": record}
