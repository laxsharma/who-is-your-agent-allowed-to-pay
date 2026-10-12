"""The article's errand, replayed through the engine.

    python -I trip_demo.py

Book the Austin offsite trip: the airline up to $500, the hotel up to $600, $1,000 in all, from
13:00 until midnight (UTC in this example). Two afternoons run on a fresh engine each:

  goes ahead   a lookalike site, a flight, a hotel quote over budget, a cheaper hotel, a seat
               upgrade at 21:00 after the trip was booked, a replay, a key from another trip,
               and one request at midnight
  cancelled    a flight, then the principal revokes at 14:10, then the hotel request the agent
               had already signed

Prints each signed decision record as a receipt line and runs audit_log over both logs.
tests/test_trip.py pins every decision printed here.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from taskaccount import (  # noqa: E402
    PolicyEngine,
    audit_log,
    digest,
    issue_task_account,
    make_request,
    make_revocation,
    new_key,
)
from taskaccount.policy import parse_time  # noqa: E402

DAY = "2026-10-21"
NOT_BEFORE = f"{DAY}T13:00:00Z"
EXPIRES = "2026-10-22T00:00:00Z"


def at(hhmm, day=DAY):
    return parse_time(f"{day}T{hhmm}:00Z")


class Clock:
    def __init__(self):
        self.now = at("13:00")

    def __call__(self):
        return self.now


class Afternoon:
    """One engine, the Austin trip, and a second trip whose key gets stolen."""

    def __init__(self):
        self.clock = Clock()
        self.principal = new_key()
        self.engine = PolicyEngine(new_key(), self.clock)
        self.trip, self.key = issue_task_account(
            self.principal,
            task_id="trip-austin",
            asset="USD",
            budget_minor=100000,
            counterparties=[
                {"id": "payee:airline", "cap_minor": 50000},
                {"id": "payee:hotel", "cap_minor": 60000},
            ],
            not_before=NOT_BEFORE,
            expires=EXPIRES,
        )
        self.other, self.other_key = issue_task_account(
            self.principal,
            task_id="trip-denver",
            asset="USD",
            budget_minor=80000,
            counterparties=[
                {"id": "payee:airline", "cap_minor": 40000},
                {"id": "payee:hotel", "cap_minor": 50000},
            ],
            not_before=NOT_BEFORE,
            expires=EXPIRES,
        )
        self.engine.register(self.trip)
        self.engine.register(self.other)
        self.requests = {}
        self.revocations = []
        self.lines = []
        self._n = 0

    def signed(self, payee, amount, *, key=None, task_id="trip-austin"):
        self._n += 1
        req = make_request(
            key or self.key,
            task_id=task_id,
            request_id=f"r{self._n}",
            counterparty=payee,
            amount_minor=amount,
            asset="USD",
        )
        self.requests[digest(req)] = req
        return req

    def send(self, when, note, req):
        self.clock.now = when
        record = self.engine.evaluate(req)
        self.lines.append((record, note))
        return record

    def pay(self, when, note, payee, amount, **kw):
        return self.send(when, note, self.signed(payee, amount, **kw))

    def revoke(self, when, note):
        self.clock.now = when
        statement = make_revocation(self.principal, self.trip, when)
        self.revocations.append(statement)
        self.lines.append((self.engine.revoke(statement), note))

    def audit(self):
        return audit_log(
            self.engine.log(),
            self.engine.engine_kid,
            [self.trip, self.other],
            revocations=self.revocations,
            requests=self.requests,
        )


def goes_ahead():
    a = Afternoon()
    a.pay(at("13:20"), "a lookalike booking site asks for the deposit", "payee:lookalike-bookings", 60000)
    a.pay(at("14:00"), "the flight", "payee:airline", 48000)
    a.pay(at("14:05"), "the hotel, first quote", "payee:hotel", 59000)
    a.pay(at("14:30"), "the hotel, a cheaper room", "payee:hotel", 51000)
    upgrade = a.signed("payee:airline", 1000)
    a.send(at("21:00"), "a seat upgrade; the trip was booked at 15:40", upgrade)
    a.send(at("21:01"), "the same upgrade request, sent again", upgrade)
    a.pay(at("21:02"), "the Austin key, on the Denver trip", "payee:airline", 1000,
          task_id="trip-denver")
    a.pay(at("00:00", "2026-10-22"), "midnight", "payee:hotel", 100)
    return a


def cancelled():
    a = Afternoon()
    a.pay(at("14:00"), "the flight", "payee:airline", 48000)
    hotel = a.signed("payee:hotel", 51000)  # signed by the agent at 14:09
    a.revoke(at("14:10"), "the offsite is cancelled: one signed statement")
    a.send(at("14:11"), "the hotel request the agent signed at 14:09", hotel)
    return a


def receipt(title, a):
    out = [title, "-" * len(title)]
    for record, note in a.lines:
        when = record["evaluated_at"][11:16]
        if record["kind"] == "revoke":
            what = "REVOKE"
        else:
            what = f"{record['counterparty'] or '':26} {record['amount_minor'] / 100:>8.2f}"
        total = record["spent_total_minor"]
        out.append(
            f"{when}  {what:36} {record['decision'].upper():8} {record['reason']:27} "
            f"total {total / 100 if total is not None else 0:>8.2f}  #{record['seq']} "
            f"prev {record['prev'][7:15]}  {note}"
        )
    problems = a.audit()
    out.append(f"audit: {'clean' if not problems else problems}")
    return "\n".join(out)


if __name__ == "__main__":
    print(receipt("Afternoon 1: the trip goes ahead", goes_ahead()))
    print()
    print(receipt("Afternoon 2: the offsite is cancelled at 14:10", cancelled()))
