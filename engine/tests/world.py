"""Shared fixture: one principal, one engine, two tasks with their own agent keys."""

from taskaccount import PolicyEngine, digest, issue_task_account, make_request, new_key
from taskaccount.policy import parse_time

NOT_BEFORE = "2026-10-08T15:00:00Z"
EXPIRES = "2026-10-08T23:00:00Z"
T0 = parse_time(NOT_BEFORE)
T_END = parse_time(EXPIRES)


class FakeClock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


class World:
    def __init__(self):
        self.clock = FakeClock(T0 + 60)
        self.principal = new_key()
        self.engine = PolicyEngine(new_key(), self.clock)

        self.policy_a, self.agent_a = issue_task_account(
            self.principal,
            task_id="task-a",
            asset="USD",
            budget_minor=25000,
            counterparties=[
                {"id": "payee:acme-data", "cap_minor": 12000, "rails": {"evm:8453": "0x00000000000000000000000000000000000000a1"}},
                {"id": "payee:render-co", "cap_minor": 15000},
            ],
            not_before=NOT_BEFORE,
            expires=EXPIRES,
        )
        self.policy_b, self.agent_b = issue_task_account(
            self.principal,
            task_id="task-b",
            asset="USD",
            budget_minor=8000,
            counterparties=[
                {"id": "payee:acme-data", "cap_minor": 5000},
                {"id": "payee:print-shop", "cap_minor": 5000},
            ],
            not_before=NOT_BEFORE,
            expires=EXPIRES,
        )
        self.engine.register(self.policy_a)
        self.engine.register(self.policy_b)
        self._n = 0
        self.requests = {}

    def request(self, agent_key, task_id, counterparty, amount, asset="USD", request_id=None):
        self._n += 1
        req = make_request(
            agent_key,
            task_id=task_id,
            request_id=request_id or f"req-{self._n}",
            counterparty=counterparty,
            amount_minor=amount,
            asset=asset,
        )
        self.requests[digest(req)] = req
        return req

    def pay_a(self, counterparty, amount, **kw):
        return self.engine.evaluate(self.request(self.agent_a, "task-a", counterparty, amount, **kw))
