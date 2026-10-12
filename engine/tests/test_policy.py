"""Policy object shape, signature, canonical form and keys."""

import unittest

from taskaccount import CanonicalError, PolicyError, canonical_bytes, digest, new_key, verify_policy
from taskaccount import keys
from taskaccount.policy import issue_task_account, unsigned


def issue(**overrides):
    args = dict(
        task_id="task-x",
        asset="USD",
        budget_minor=1000,
        counterparties=[{"id": "payee:one", "cap_minor": 600}],
        not_before="2026-10-08T15:00:00Z",
        expires="2026-10-08T16:00:00Z",
    )
    args.update(overrides)
    return issue_task_account(new_key(), **args)


class PolicyTests(unittest.TestCase):
    def test_issued_policy_verifies(self):
        policy, agent = issue()
        self.assertTrue(verify_policy(policy).startswith("sha256:"))
        self.assertEqual(policy["agent_key"], keys.key_id(agent))

    def test_bad_shapes_are_refused(self):
        bad_args = [
            dict(budget_minor=0),
            dict(budget_minor=10.0),
            dict(counterparties=[]),
            dict(counterparties=[{"id": "payee:one", "cap_minor": 1}, {"id": "payee:one", "cap_minor": 2}]),
            dict(counterparties=[{"id": "payee:one", "cap_minor": 1, "note": "x"}]),
            dict(counterparties=[{"id": "has space", "cap_minor": 1}]),
            dict(not_before="2026-10-08T16:00:00Z", expires="2026-10-08T16:00:00Z"),
            dict(expires="2026-10-08 16:00:00"),
            dict(expires="2026-10-08T16:00:00+01:00"),
            dict(asset="usd"),
        ]
        for args in bad_args:
            with self.assertRaises(PolicyError, msg=str(args)):
                issue(**args)

    def test_extra_or_missing_members_are_refused(self):
        policy, _ = issue()
        with self.assertRaises(PolicyError):
            verify_policy(dict(policy, note="x"))
        with self.assertRaises(PolicyError):
            verify_policy({k: v for k, v in policy.items() if k != "expires"})

    def test_signature_covers_every_member(self):
        policy, _ = issue()
        for member, value in [
            ("budget_minor", 1001),
            ("expires", "2026-10-08T17:00:00Z"),
            ("counterparties", [{"id": "payee:two", "cap_minor": 600}]),
            ("agent_key", keys.key_id(new_key())),
        ]:
            with self.assertRaises(PolicyError, msg=member):
                verify_policy(dict(policy, **{member: value}))

    def test_signature_contexts_are_separate(self):
        policy, _ = issue()
        body = unsigned(policy)
        signer = new_key()
        sig = keys.sign(signer, keys.CTX_REQUEST, body)
        self.assertFalse(keys.verify(keys.key_id(signer), keys.CTX_POLICY, body, sig))
        self.assertTrue(keys.verify(keys.key_id(signer), keys.CTX_REQUEST, body, sig))

    def test_canonical_form(self):
        self.assertEqual(canonical_bytes({"b": 1, "a": [True, None, "x"]}), b'{"a":[true,null,"x"],"b":1}')
        self.assertEqual(digest({"a": 1, "b": 2}), digest({"b": 2, "a": 1}))
        for bad in (1.0, {"a": 0.5}, 2**53, {1: "x"}, {"é": 1}, b"bytes"):
            with self.assertRaises(CanonicalError):
                canonical_bytes(bad)

    def test_key_ids_are_strict(self):
        kid = keys.key_id(new_key())
        self.assertTrue(keys.is_key_id(kid))
        self.assertFalse(keys.is_key_id(kid + "A"))
        self.assertFalse(keys.is_key_id(kid.replace("ed25519:", "secp256k1:")))
        self.assertFalse(keys.is_key_id("ed25519:" + "!" * 43))


if __name__ == "__main__":
    unittest.main()
