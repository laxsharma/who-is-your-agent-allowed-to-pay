"""The five attacks in the attack table. Each must end in a signed deny record,
leave the ledger unchanged, and leave a log that an outside audit accepts."""

import unittest

from taskaccount import (
    EngineError,
    audit_log,
    issue_task_account,
    make_revocation,
    new_key,
    verify_record,
)
from taskaccount import engine as E
from taskaccount import keys
from taskaccount.policy import unsigned

from world import T_END, World


class AttackTests(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def assertRefused(self, record, reason, task_id="task-a"):
        self.assertEqual(record["decision"], "deny")
        self.assertEqual(record["reason"], reason)
        self.assertTrue(verify_record(record, self.w.engine.engine_kid))
        if task_id is not None:
            self.assertEqual(record["task_id"], task_id)

    def assertAuditClean(self, revocations=()):
        problems = audit_log(
            self.w.engine.log(),
            self.w.engine.engine_kid,
            [self.w.policy_a, self.w.policy_b],
            revocations=revocations,
            requests=self.w.requests,
        )
        self.assertEqual(problems, [])

    # 1. A prompt-injected agent asks to pay a counterparty the task does not name.
    def test_1_prompt_injected_agent_pays_unlisted_counterparty(self):
        self.assertEqual(self.w.pay_a("payee:acme-data", 3000)["decision"], "allow")
        # The agent itself is compromised, so the request carries a valid signature.
        record = self.w.pay_a("payee:attacker-wallet", 500)
        self.assertRefused(record, E.NOT_LISTED)
        self.assertEqual(self.w.engine.spent("task-a"), ({"payee:acme-data": 3000, "payee:render-co": 0}, 3000))
        # Listing the attacker in a rail binding of another payee does not help: ids are matched exactly.
        self.assertRefused(self.w.pay_a("0x00000000000000000000000000000000000000a1", 500), E.NOT_LISTED)
        self.assertAuditClean()

    # 2. The same listed counterparty, past its cap.
    def test_2_listed_counterparty_past_its_cap(self):
        self.assertEqual(self.w.pay_a("payee:acme-data", 10000)["decision"], "allow")
        self.assertRefused(self.w.pay_a("payee:acme-data", 2001), E.CAP_EXCEEDED)
        record = self.w.pay_a("payee:acme-data", 2000)
        self.assertEqual(record["decision"], "allow")
        self.assertEqual(record["spent_counterparty_minor"], 12000)
        self.assertRefused(self.w.pay_a("payee:acme-data", 1), E.CAP_EXCEEDED)
        # Splitting into small payments does not get round a cumulative cap.
        self.assertEqual(self.w.engine.spent("task-a")[0]["payee:acme-data"], 12000)
        self.assertAuditClean()

    # 3. A request that was allowed once is replayed after the principal revokes the task.
    def test_3_replay_after_revocation(self):
        request = self.w.request(self.w.agent_a, "task-a", "payee:render-co", 4000)
        self.assertEqual(self.w.engine.evaluate(request)["decision"], "allow")
        statement = make_revocation(self.w.principal, self.w.policy_a, self.w.clock.now)
        self.w.engine.revoke(statement)
        self.assertRefused(self.w.engine.evaluate(request), E.REVOKED)
        # A fresh, validly signed request is refused too.
        self.assertRefused(self.w.pay_a("payee:render-co", 1), E.REVOKED)
        self.assertEqual(self.w.engine.spent("task-a")[1], 4000)
        # Revoking task-a leaves task-b alone.
        other = self.w.engine.evaluate(self.w.request(self.w.agent_b, "task-b", "payee:print-shop", 100))
        self.assertEqual(other["decision"], "allow")
        self.assertAuditClean(revocations=[statement])

    def test_3b_replay_before_revocation_is_also_refused(self):
        request = self.w.request(self.w.agent_a, "task-a", "payee:render-co", 4000)
        self.assertEqual(self.w.engine.evaluate(request)["decision"], "allow")
        self.assertRefused(self.w.engine.evaluate(request), E.REPLAY)
        self.assertEqual(self.w.engine.spent("task-a")[1], 4000)
        self.assertAuditClean()

    # 4. A request after the task has ended.
    def test_4_request_after_expiry(self):
        self.w.clock.now = T_END - 1
        self.assertEqual(self.w.pay_a("payee:acme-data", 100)["decision"], "allow")
        self.w.clock.now = T_END
        self.assertRefused(self.w.pay_a("payee:acme-data", 100), E.EXPIRED)
        self.w.clock.now = T_END + 86400
        self.assertRefused(self.w.pay_a("payee:render-co", 100), E.EXPIRED)
        self.assertEqual(self.w.engine.spent("task-a")[1], 100)
        self.assertAuditClean()

    # 5. A stolen per-task key used on a different task.
    def test_5_stolen_task_key_used_on_another_task(self):
        stolen = self.w.agent_a
        # payee:acme-data is listed in task-b too, so only the key binding stops this.
        forged = self.w.request(stolen, "task-b", "payee:acme-data", 1000)
        self.assertRefused(self.w.engine.evaluate(forged), E.BAD_SIGNATURE, task_id="task-b")
        self.assertEqual(self.w.engine.spent("task-b")[1], 0)
        # Re-labelling a genuine task-a request as task-b breaks its signature.
        genuine = self.w.request(stolen, "task-a", "payee:acme-data", 1000)
        relabelled = dict(genuine, task_id="task-b", request_id="relabelled")
        self.assertRefused(self.w.engine.evaluate(relabelled), E.BAD_SIGNATURE, task_id="task-b")
        # The thief cannot bind the stolen key to a task of its own on this engine.
        thief = new_key()
        policy, _ = issue_task_account(
            thief, task_id="task-thief", asset="USD", budget_minor=10**6,
            counterparties=[{"id": "payee:attacker-wallet", "cap_minor": 10**6}],
            not_before="2026-10-08T15:00:00Z", expires="2026-10-09T15:00:00Z",
        )
        body = dict(unsigned(policy), agent_key=self.w.policy_a["agent_key"])
        resigned = dict(body, signature=keys.sign(thief, keys.CTX_POLICY, body))
        with self.assertRaisesRegex(EngineError, "agent key already bound"):
            self.w.engine.register(resigned)
        self.assertAuditClean()


if __name__ == "__main__":
    unittest.main()
