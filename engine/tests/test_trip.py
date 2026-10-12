"""Pins the decisions trip_demo.py prints, which the article's receipt figure shows."""

import unittest

import trip_demo


def decisions(afternoon):
    return [(r["decision"], r["reason"], r["amount_minor"]) for r, _ in afternoon.lines]


class TripTests(unittest.TestCase):
    def test_the_trip_goes_ahead(self):
        a = trip_demo.goes_ahead()
        self.assertEqual(decisions(a), [
            ("deny", "counterparty_not_listed", 60000),
            ("allow", "ok", 48000),
            ("deny", "task_budget_exceeded", 59000),
            ("allow", "ok", 51000),
            # The task finished at 15:40, but nothing told the engine, so the upgrade passes.
            ("allow", "ok", 1000),
            ("deny", "replay", 1000),
            ("deny", "bad_signature", 1000),
            ("deny", "task_expired", 100),
        ])
        self.assertEqual(a.engine.spent("trip-austin"), ({"payee:airline": 49000, "payee:hotel": 51000}, 100000))
        self.assertEqual(a.engine.spent("trip-denver")[1], 0)
        self.assertEqual(a.audit(), [])

    def test_the_offsite_is_cancelled(self):
        a = trip_demo.cancelled()
        self.assertEqual(decisions(a), [
            ("allow", "ok", 48000),
            ("accepted", "ok", None),
            ("deny", "task_revoked", 51000),
        ])
        self.assertEqual(a.engine.spent("trip-austin")[1], 48000)
        self.assertEqual(a.audit(), [])


if __name__ == "__main__":
    unittest.main()
