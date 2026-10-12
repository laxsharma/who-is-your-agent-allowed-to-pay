# Task-account policy engine (offline reference)

A small engine that takes a principal-signed task-account object (see [TASK-ACCOUNT.md](../TASK-ACCOUNT.md)), binds a
fresh Ed25519 key to that one task, evaluates agent-signed payment requests against the policy, and
writes every decision as an engine-signed record chained to the previous one. No network, no
blockchain, no money movement. Standard library plus `cryptography`.

Run the tests (any working directory):

```
python -I run_tests.py
```

Result on 9 Oct 2026: 33 tests, all pass (Python 3.12.11, cryptography 50.0.1).

The article's afternoon (the Austin trip: the airline up to $500, the hotel up to $600, $1,000 in all, 13:00 to
midnight UTC) replayed through the engine, printed as receipt lines with an audit at the end:

```
python -I trip_demo.py
```

`tests/test_trip.py` pins every decision it prints. The run the article's receipt figure copies is saved in
`runs/trip-2026-10-09.txt`; digests differ on every run because keys are fresh. One allow in it is deliberate: a
$10 upgrade at 21:00 passes every check, because nothing tells the engine the trip was booked at 15:40.

## Files

| File | Role |
|---|---|
| `taskaccount/canonical.py` | canonical JSON bytes and `sha256:` digests; floats refused |
| `taskaccount/keys.py` | Ed25519 keys, `ed25519:<base64url>` key ids, signatures with one context string per object type |
| `taskaccount/policy.py` | policy schema, `issue_task_account` (new per-task key plus principal signature), `verify_policy` |
| `taskaccount/revocation.py` | principal-signed revocation statement and the revocation list |
| `taskaccount/engine.py` | `PolicyEngine` (register, revoke, evaluate), `make_request`, `verify_record`, `audit_log` |
| `tests/` | `test_attacks.py` (the table below), `test_engine.py`, `test_policy.py`, `test_trip.py`, fixture `world.py` |
| `trip_demo.py` | the article's afternoon as two runs, printed as receipts |

## Checks, in order

A request is `{type, task_id, request_id, counterparty, amount_minor, asset, signature}`, signed by the
agent key over everything except the signature. The engine runs these checks and stops at the first
failure; only an allow changes the ledger.

1. well-formed (exact members, integer amount above zero) else `malformed_request`
2. task registered else `unknown_task`
3. signature by the agent key named in **that task's** policy else `bad_signature`
4. task not revoked else `task_revoked`
5. `not_before <= now < expires` else `not_yet_valid` or `task_expired`
6. `request_id` not already allowed for this task else `replay`
7. asset matches else `asset_mismatch`
8. counterparty id listed else `counterparty_not_listed`
9. counterparty total plus amount within its cap else `counterparty_cap_exceeded`
10. task total plus amount within the budget else `task_budget_exceeded`

Registration refuses a bad principal signature, a task id already registered (so counters cannot be
reset) and an agent key already bound to another task. Revocation accepts only a statement signed by
the principal key named in the policy, over that policy's digest.

## Decision record

Every successful registration and revocation, and every payment decision (allow or deny), is a record with `seq`, `prev` (digest of the previous
record), `kind`, `decision`, `reason`, `task_id`, `policy_digest`, `subject_digest` (digest of the
request, policy or revocation statement), the request's id, payee and amount, the running totals,
`evaluated_at` and the engine key id, signed by the engine. `verify_record` checks one record.
`audit_log` re-derives every allow from the policies, the revocation statements and (optionally) the
signed requests, and reports any allow that breaks a rule (asset included, when the requests are given), any
allow after a revocation statement it holds even if the log never shows that revocation, any wrong total and
any break in the chain. A refused registration or revocation raises an error and leaves no record.

## Attack table

| # | Attack | What the attacker sends | Stopped by | Reason | Test |
|---|---|---|---|---|---|
| 1 | Prompt-injected agent pays a counterparty the task does not name | a request signed with the genuine task key to `payee:attacker-wallet`, and one to a raw address that appears only in another payee's rail binding | check 8, exact id match | `counterparty_not_listed` | `test_1_prompt_injected_agent_pays_unlisted_counterparty` |
| 2 | Same listed counterparty past its cap | 10000 then 2001 against a 12000 cap; then 2000 (allowed, reaches the cap) and 1 | check 9, cumulative per payee | `counterparty_cap_exceeded` | `test_2_listed_counterparty_past_its_cap` |
| 3 | Replay after revocation | the exact bytes of a request that was allowed, after the principal's revocation; then a fresh request | check 4 (revocation runs before the replay check) | `task_revoked` | `test_3_replay_after_revocation`; the same replay before revocation gets `replay` in `test_3b_...` |
| 4 | Request after expiry | requests at `expires` and a day later (one second earlier is allowed) | check 5 | `task_expired` | `test_4_request_after_expiry` |
| 5 | Stolen per-task key used on a different task | task-a's key signs a request naming task-b and a payee both tasks list; a genuine task-a request relabelled as task-b; a thief's own policy, re-signed, naming the stolen key | check 3 (only task-b's key verifies for task-b); registration refuses a key bound to another task | `bad_signature`; `EngineError` at register | `test_5_stolen_task_key_used_on_another_task` |

Each attack test also asserts that the deny record verifies under the engine key, that the ledger did
not move, and that `audit_log` over the whole log, with the signed requests, reports no problem.

Mutation check (8 Oct): removing any one of the checks for counterparty, cap, budget, revocation,
expiry, signature or replay makes the suite fail.

## What this prototype does not do

- The engine is a single trusted evaluator holding state in memory. The log makes its decisions
  checkable after the fact; it does not stop a dishonest engine from deciding wrongly in the moment,
  and an engine that writes a false `evaluated_at` passes the audit, since the auditor has no other
  clock. A revocation the auditor never receives cannot be checked either.
- A stolen key used **within its own task** is bounded by that task's caps, budget and expiry, and
  ends with revocation; the engine cannot tell the thief from the agent.
- The revocation list is local. Publishing it (a status list, a log, a chain) is out of scope, and a
  payee who cannot reach it cannot know about a revocation.
- The canonical form is a JSON subset intended to match RFC 8785 for its value types; not tested
  against an RFC 8785 implementation.
- Nothing moves money; an allow is a decision a rail adapter would act on.
