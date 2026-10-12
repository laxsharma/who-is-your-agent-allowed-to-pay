"""Normal flows, the remaining refusals, and the verifiability of the decision log."""

import unittest

from taskaccount import (
    EngineError,
    PolicyEngine,
    audit_log,
    digest,
    make_revocation,
    new_key,
    verify_record,
    verify_revocation,
)
from taskaccount import engine as E
from taskaccount import keys
from taskaccount.policy import unsigned

from world import T0, World


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def audit(self, records=None, revocations=()):
        return audit_log(
            self.w.engine.log() if records is None else records,
            self.w.engine.engine_kid,
            [self.w.policy_a, self.w.policy_b],
            revocations=revocations,
            requests=self.w.requests,
        )

    def test_task_budget_binds_across_counterparties(self):
        self.assertEqual(self.w.pay_a("payee:acme-data", 12000)["decision"], "allow")
        self.assertEqual(self.w.pay_a("payee:render-co", 13000)["decision"], "allow")
        record = self.w.pay_a("payee:render-co", 1)  # render-co cap 15000 not reached
        self.assertEqual(record["reason"], E.BUDGET_EXCEEDED)
        self.assertEqual(self.w.engine.spent("task-a")[1], 25000)
        self.assertEqual(self.audit(), [])

    def test_not_yet_valid(self):
        self.w.clock.now = T0 - 1
        self.assertEqual(self.w.pay_a("payee:acme-data", 1)["reason"], E.NOT_YET_VALID)
        self.w.clock.now = T0
        self.assertEqual(self.w.pay_a("payee:acme-data", 1)["decision"], "allow")

    def test_asset_mismatch(self):
        self.assertEqual(self.w.pay_a("payee:acme-data", 1, asset="EUR")["reason"], E.ASSET_MISMATCH)

    def test_unknown_task(self):
        record = self.w.engine.evaluate(self.w.request(self.w.agent_a, "task-zzz", "payee:acme-data", 1))
        self.assertEqual(record["reason"], E.UNKNOWN_TASK)

    def test_tampered_amount_breaks_signature(self):
        request = self.w.request(self.w.agent_a, "task-a", "payee:acme-data", 100)
        tampered = dict(request, amount_minor=11000)
        self.assertEqual(self.w.engine.evaluate(tampered)["reason"], E.BAD_SIGNATURE)

    def test_malformed_requests(self):
        good = self.w.request(self.w.agent_a, "task-a", "payee:acme-data", 100)
        for bad in (
            dict(good, amount_minor=1.5),
            dict(good, amount_minor=-5),
            dict(good, amount_minor=0),
            dict(good, amount_minor=True),
            dict(good, extra="x"),
            {k: v for k, v in good.items() if k != "signature"},
            "not an object",
            None,
        ):
            record = self.w.engine.evaluate(bad)
            self.assertEqual(record["reason"], E.MALFORMED, bad)
            self.assertTrue(verify_record(record, self.w.engine.engine_kid))
        self.assertEqual(self.w.engine.spent("task-a")[1], 0)

    def test_revocation_must_come_from_the_principal(self):
        forged = make_revocation(self.w.agent_a, self.w.policy_a, self.w.clock.now)
        self.assertFalse(verify_revocation(forged, self.w.policy_a))
        with self.assertRaises(EngineError):
            self.w.engine.revoke(forged)
        # A genuine statement for task-b cannot be pointed at task-a.
        for_b = make_revocation(self.w.principal, self.w.policy_b, self.w.clock.now)
        with self.assertRaises(EngineError):
            self.w.engine.revoke(dict(for_b, task_id="task-a"))
        self.assertEqual(self.w.pay_a("payee:acme-data", 1)["decision"], "allow")

    def test_revocation_is_one_statement_any_holder_of_the_policy_can_check(self):
        statement = make_revocation(self.w.principal, self.w.policy_a, self.w.clock.now)
        self.assertTrue(verify_revocation(statement, self.w.policy_a))
        self.assertFalse(verify_revocation(statement, self.w.policy_b))
        record = self.w.engine.revoke(statement)
        self.assertEqual(record["subject_digest"], digest(statement))
        self.assertTrue(self.w.engine.revocations.is_revoked("task-a"))
        with self.assertRaises(EngineError):
            self.w.engine.revoke(statement)

    def test_agent_cannot_widen_its_own_policy(self):
        engine = PolicyEngine(new_key(), self.w.clock)
        widened = dict(self.w.policy_a, budget_minor=10**9)
        with self.assertRaisesRegex(EngineError, "signature"):
            engine.register(widened)
        added = dict(self.w.policy_a, counterparties=self.w.policy_a["counterparties"]
                     + [{"id": "payee:attacker-wallet", "cap_minor": 1}])
        with self.assertRaisesRegex(EngineError, "signature"):
            engine.register(added)

    def test_re_registering_a_task_cannot_reset_its_counters(self):
        self.assertEqual(self.w.pay_a("payee:acme-data", 12000)["decision"], "allow")
        with self.assertRaisesRegex(EngineError, "already registered"):
            self.w.engine.register(self.w.policy_a)
        self.assertEqual(self.w.pay_a("payee:acme-data", 1)["reason"], E.CAP_EXCEEDED)

    def test_each_task_gets_its_own_key(self):
        self.assertNotEqual(self.w.policy_a["agent_key"], self.w.policy_b["agent_key"])
        self.assertNotEqual(self.w.policy_a["agent_key"], self.w.policy_a["principal"])

    def test_payee_can_check_a_decision_offline(self):
        record = self.w.pay_a("payee:render-co", 2500)
        # What the payee holds: the record, the signed policy, the engine key id, the revocation list.
        self.assertTrue(verify_record(record, self.w.engine.engine_kid))
        self.assertEqual(record["policy_digest"], digest(self.w.policy_a))
        self.assertEqual((record["counterparty"], record["amount_minor"]), ("payee:render-co", 2500))
        self.assertFalse(self.w.engine.revocations.is_revoked(record["task_id"]))
        # A record signed by any other key does not verify as this engine's.
        self.assertFalse(verify_record(record, keys.key_id(new_key())))

    def test_tampered_record_is_detected(self):
        self.w.pay_a("payee:acme-data", 100)
        records = self.w.engine.log()
        records[-1] = dict(records[-1], reason="ok", decision="allow", amount_minor=99999)
        self.assertFalse(verify_record(records[-1], self.w.engine.engine_kid))
        self.assertTrue(any("signature" in p for p in self.audit(records)))

    def test_deleted_record_breaks_the_chain(self):
        self.w.pay_a("payee:acme-data", 100)
        self.w.pay_a("payee:attacker-wallet", 100)
        self.w.pay_a("payee:acme-data", 100)
        records = self.w.engine.log()
        del records[3]  # drop the deny for the unlisted payee
        self.assertTrue(any("chain broken" in p for p in self.audit(records)))

    def test_forged_allow_from_a_rogue_engine_is_caught(self):
        rogue_key = new_key()
        rogue = PolicyEngine(rogue_key, self.w.clock)
        rogue.register(self.w.policy_a)
        rogue.register(self.w.policy_b)
        # Even a correctly signed log from the expected engine is re-checked against the policy:
        # forge a record that claims an allow to an unlisted payee, signed by the real engine key.
        records = self.w.engine.log()
        body = dict(unsigned(records[-1]), seq=len(records), prev=digest(records[-1]),
                    kind="payment", decision="allow", reason="ok", counterparty="payee:attacker-wallet",
                    amount_minor=500, request_id="forged", spent_counterparty_minor=500,
                    spent_total_minor=500, subject_digest=None, task_id="task-a",
                    policy_digest=digest(self.w.policy_a))
        forged = dict(body, signature=keys.sign(self.w.engine._key, keys.CTX_RECORD, body))
        problems = audit_log(records + [forged], self.w.engine.engine_kid,
                             [self.w.policy_a, self.w.policy_b])
        self.assertTrue(any("unlisted counterparty" in p for p in problems))
        # And the rogue engine's records do not verify under the real engine key.
        self.assertTrue(audit_log(rogue.log(), self.w.engine.engine_kid, [self.w.policy_a]))

    def _forge_allow(self, request, **extra):
        # An allow written and signed by the real engine key, as a dishonest engine would.
        records = self.w.engine.log()
        body = dict(unsigned(records[-1]), seq=len(records), prev=digest(records[-1]),
                    kind="payment", decision="allow", reason="ok", task_id=request["task_id"],
                    policy_digest=digest(self.w.policy_a), subject_digest=digest(request),
                    request_id=request["request_id"], counterparty=request["counterparty"],
                    amount_minor=request["amount_minor"],
                    spent_counterparty_minor=request["amount_minor"],
                    spent_total_minor=request["amount_minor"], **extra)
        return records + [dict(body, signature=keys.sign(self.w.engine._key, keys.CTX_RECORD, body))]

    def test_audit_catches_an_allow_in_the_wrong_asset(self):
        request = self.w.request(self.w.agent_a, "task-a", "payee:acme-data", 500, asset="EUR")
        problems = self.audit(self._forge_allow(request))
        self.assertTrue(any("asset" in p for p in problems))

    def test_audit_catches_an_allow_after_a_revocation_the_engine_never_logged(self):
        statement = make_revocation(self.w.principal, self.w.policy_a, self.w.clock.now)
        self.w.clock.now += 60
        record = self.w.pay_a("payee:acme-data", 700)  # the engine was never told
        self.assertEqual(record["decision"], "allow")
        problems = self.audit(revocations=[statement])
        self.assertTrue(any("signed revocation" in p for p in problems))

    def test_clean_run_audits_clean(self):
        self.w.pay_a("payee:acme-data", 5000)
        self.w.pay_a("payee:render-co", 5000)
        self.w.pay_a("payee:nobody", 5)
        statement = make_revocation(self.w.principal, self.w.policy_a, self.w.clock.now)
        self.w.engine.revoke(statement)
        self.w.pay_a("payee:acme-data", 5)
        self.assertEqual(self.audit(revocations=[statement]), [])


if __name__ == "__main__":
    unittest.main()
