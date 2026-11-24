import json
import pathlib
import unittest

POLICY = pathlib.Path(__file__).with_name("policy.json")


class WiseTagsPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))

    def test_default_deny_and_prepare_only(self):
        self.assertEqual(self.policy["default_decision"], "DENY")
        self.assertEqual(self.policy["execution_mode"], "PREPARE_ONLY")
        self.assertFalse(self.policy["live_provider_access"])

    def test_known_capabilities_are_declared(self):
        expected = {
            "WISE.READ", "WISE.BENEFICIARY.VERIFY", "WISE.TRANSFER.PREPARE",
            "WISE.TRANSFER.REVIEW", "WISE.TRANSFER.APPROVE",
            "WISE.TRANSFER.SUBMIT", "WISE.RECONCILE", "WISE.LIMIT.CONFIGURE",
        }
        self.assertEqual(set(self.policy["capabilities"]), expected)

    def test_submission_is_disabled(self):
        self.assertFalse(self.policy["capabilities"]["WISE.TRANSFER.SUBMIT"]["enabled_by_spec"])
        self.assertFalse(self.policy["transfer_submission"]["enabled"])
        self.assertTrue(self.policy["transfer_submission"]["requires_explicit_final_user_confirmation"])

    def test_approval_is_scoped_and_independent(self):
        approval = self.policy["approval"]
        self.assertTrue(approval["human_approval_required_for_consequential_operations"])
        self.assertTrue(approval["independent_reviewer_required_for_transfer_submission"])
        self.assertFalse(approval["requester_may_self_approve"])
        self.assertTrue(approval["bind_to_request_digest"])
        self.assertTrue(approval["single_use"])
        self.assertTrue(approval["replay_protection_required"])

    def test_purge_cannot_delete_existing_safeguards(self):
        purge = self.policy["purge"]
        self.assertFalse(purge["delete_existing_repository_safeguards"])
        self.assertIn("regression_tests_pass", purge["allow_removal_only_after"])


if __name__ == "__main__":
    unittest.main()
