import json
import os
import tempfile
import unittest

from tools.upstream_index import UpstreamVerificationError, verify_upstream_before_mutation

UPSTREAM = "a" * 40
HEAD = "b" * 40


class UpstreamIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.index = os.path.join(self.temp.name, "upstream-index.jsonl")

    def tearDown(self):
        self.temp.cleanup()

    def run_gate(self, remote=UPSTREAM, ancestor=True, expected=UPSTREAM):
        return verify_upstream_before_mutation(
            upstream_url="https://github.com/Vanellye/Ash.git",
            upstream_ref="refs/heads/main",
            expected_upstream_sha=expected,
            current_head_sha=HEAD,
            index_path=self.index,
            resolver=lambda url, ref: remote,
            ancestry_check=lambda base, head: ancestor,
        )

    def test_fresh_upstream_is_check_only_and_indexed(self):
        result = self.run_gate()
        self.assertEqual(result["decision"], "ALLOW_CHECK_ONLY")
        self.assertEqual(result["index_record"]["sequence"], 1)
        self.assertEqual(result["index_record"]["next_action"], "CONTINUE_TO_SEPARATE_AUTHORIZATION")

    def test_upstream_moved_is_logged_with_fix_guidance(self):
        with self.assertRaisesRegex(UpstreamVerificationError, "upstream_moved_since_pinned_base") as caught:
            self.run_gate(remote="c" * 40)
        self.assertEqual(caught.exception.index_record["decision"], "DENY")
        self.assertEqual(caught.exception.index_record["next_action"], "LOG_AND_FIX")
        self.assertIn("Fetch/review", caught.exception.remediation)
        rows = [json.loads(line) for line in open(self.index, encoding="utf-8")]
        self.assertEqual(rows[-1]["decision"], "DENY")
        self.assertTrue(rows[-1]["remediation"])

    def test_branch_missing_upstream_ancestor_is_logged(self):
        with self.assertRaisesRegex(UpstreamVerificationError, "current_head_does_not_contain_upstream") as caught:
            self.run_gate(ancestor=False)
        self.assertEqual(caught.exception.index_record["next_action"], "LOG_AND_FIX")

    def test_index_revolves_with_hash_chain(self):
        self.run_gate()
        self.run_gate()
        rows = [json.loads(line) for line in open(self.index, encoding="utf-8")]
        self.assertEqual([row["sequence"] for row in rows], [1, 2])
        self.assertEqual(rows[1]["previous_record_sha256"], rows[0]["record_sha256"])

    def test_tampered_index_fails_closed(self):
        self.run_gate()
        with open(self.index, "r+", encoding="utf-8") as stream:
            value = json.loads(stream.readline())
            value["reason"] = "tampered"
            stream.seek(0)
            stream.write(json.dumps(value) + "\n")
            stream.truncate()
        with self.assertRaisesRegex(UpstreamVerificationError, "index_record_hash_mismatch"):
            self.run_gate()

    def test_invalid_expected_sha_is_logged_with_remediation(self):
        with self.assertRaisesRegex(UpstreamVerificationError, "expected_upstream_sha_invalid") as caught:
            self.run_gate(expected="not-a-sha")
        self.assertEqual(caught.exception.index_record["decision"], "DENY")
        self.assertIn("trusted event", caught.exception.remediation)


if __name__ == "__main__":
    unittest.main()
