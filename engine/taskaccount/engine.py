"""Offline policy engine for task accounts.

The engine holds registered task policies, a revocation list and a ledger of
what each task has paid. It evaluates agent-signed payment requests and writes
every decision as an engine-signed record that links to the previous record by
digest, so the log is append-only and can be re-checked by anyone holding the
engine's public key and the policies.

No network, no blockchain: the engine decides; moving money is out of scope.
"""

from . import keys
from .canonical import ZERO_DIGEST, CanonicalError, digest
from .policy import PolicyError, format_time, parse_time, unsigned, verify_policy
from .revocation import RevocationList, verify_revocation

REQUEST_TYPE = "payment-request/0.1"
RECORD_TYPE = "decision-record/0.1"
_REQUEST_KEYS = {"type", "task_id", "request_id", "counterparty", "amount_minor", "asset", "signature"}

# Reason codes, in the order the checks run.
MALFORMED = "malformed_request"
UNKNOWN_TASK = "unknown_task"
BAD_SIGNATURE = "bad_signature"
REVOKED = "task_revoked"
NOT_YET_VALID = "not_yet_valid"
EXPIRED = "task_expired"
REPLAY = "replay"
ASSET_MISMATCH = "asset_mismatch"
NOT_LISTED = "counterparty_not_listed"
CAP_EXCEEDED = "counterparty_cap_exceeded"
BUDGET_EXCEEDED = "task_budget_exceeded"
OK = "ok"


class EngineError(ValueError):
    """Raised for operator errors (registration, revocation), never for payment requests."""


def make_request(agent_key, *, task_id, request_id, counterparty, amount_minor, asset):
    """Build a payment request signed by the per-task agent key."""
    body = {
        "type": REQUEST_TYPE,
        "task_id": task_id,
        "request_id": request_id,
        "counterparty": counterparty,
        "amount_minor": amount_minor,
        "asset": asset,
    }
    return dict(body, signature=keys.sign(agent_key, keys.CTX_REQUEST, body))


def _well_formed_request(request):
    if not isinstance(request, dict) or set(request) != _REQUEST_KEYS:
        return False
    if request["type"] != REQUEST_TYPE:
        return False
    for member in ("task_id", "request_id", "counterparty", "asset", "signature"):
        value = request[member]
        if not isinstance(value, str) or not 1 <= len(value) <= 256:
            return False
    amount = request["amount_minor"]
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        return False
    try:
        digest(request)
    except CanonicalError:
        return False
    return True


def verify_record(record, engine_kid):
    """True if record is a decision record signed by the engine key engine_kid."""
    if not isinstance(record, dict) or "signature" not in record:
        return False
    if record.get("type") != RECORD_TYPE or record.get("engine") != engine_kid:
        return False
    return keys.verify(engine_kid, keys.CTX_RECORD, unsigned(record), record["signature"])


class _TaskState:
    def __init__(self, policy, pdigest):
        self.policy = policy
        self.digest = pdigest
        self.not_before = parse_time(policy["not_before"])
        self.expires = parse_time(policy["expires"])
        self.caps = {p["id"]: p["cap_minor"] for p in policy["counterparties"]}
        self.spent = {p["id"]: 0 for p in policy["counterparties"]}
        self.spent_total = 0
        self.used_request_ids = set()


class PolicyEngine:
    def __init__(self, engine_key, clock):
        """engine_key: Ed25519 private key that signs records. clock: () -> epoch seconds."""
        self._key = engine_key
        self._kid = keys.key_id(engine_key)
        self._clock = clock
        self._tasks = {}
        self._agent_keys = {}
        self._revocations = RevocationList()
        self._log = []

    @property
    def engine_kid(self):
        return self._kid

    @property
    def revocations(self):
        return self._revocations

    def log(self):
        return [dict(r) for r in self._log]

    def spent(self, task_id):
        state = self._tasks[task_id]
        return dict(state.spent), state.spent_total

    # Records -------------------------------------------------------------

    def _append(self, kind, decision, reason, *, task_id=None, policy_digest_=None,
                subject_digest=None, request=None, state=None):
        counterparty = request["counterparty"] if request else None
        body = {
            "type": RECORD_TYPE,
            "seq": len(self._log),
            "prev": digest(self._log[-1]) if self._log else ZERO_DIGEST,
            "kind": kind,
            "decision": decision,
            "reason": reason,
            "task_id": task_id,
            "policy_digest": policy_digest_,
            "subject_digest": subject_digest,
            "request_id": request["request_id"] if request else None,
            "counterparty": counterparty,
            "amount_minor": request["amount_minor"] if request else None,
            "spent_counterparty_minor": (
                state.spent.get(counterparty) if state is not None and counterparty else None
            ),
            "spent_total_minor": state.spent_total if state is not None else None,
            "evaluated_at": format_time(self._clock()),
            "engine": self._kid,
        }
        record = dict(body, signature=keys.sign(self._key, keys.CTX_RECORD, body))
        self._log.append(record)
        return dict(record)

    # Operator actions ----------------------------------------------------

    def register(self, policy):
        """Accept a principal-signed policy. A task id or agent key can be registered once."""
        try:
            pdigest = verify_policy(policy)
        except PolicyError as exc:
            raise EngineError(f"policy rejected: {exc}") from exc
        if policy["task_id"] in self._tasks:
            raise EngineError("task_id already registered")
        if policy["agent_key"] in self._agent_keys:
            raise EngineError("agent key already bound to another task")
        state = _TaskState(policy, pdigest)
        self._tasks[policy["task_id"]] = state
        self._agent_keys[policy["agent_key"]] = policy["task_id"]
        return self._append("register", "accepted", OK, task_id=policy["task_id"],
                            policy_digest_=pdigest, subject_digest=pdigest, state=state)

    def revoke(self, statement):
        """Apply one principal-signed revocation statement."""
        task_id = statement.get("task_id") if isinstance(statement, dict) else None
        state = self._tasks.get(task_id)
        if state is None:
            raise EngineError("unknown task")
        if not verify_revocation(statement, state.policy):
            raise EngineError("revocation statement does not verify")
        if self._revocations.is_revoked(task_id):
            raise EngineError("task already revoked")
        self._revocations.add(statement, state.policy)
        return self._append("revoke", "accepted", OK, task_id=task_id,
                            policy_digest_=state.digest, subject_digest=digest(statement),
                            state=state)

    # Payment requests ----------------------------------------------------

    def evaluate(self, request):
        """Decide one payment request. Never raises; always returns a signed record."""
        if not _well_formed_request(request):
            try:
                subject = digest(request)
            except (CanonicalError, TypeError):
                subject = None
            return self._append("payment", "deny", MALFORMED, subject_digest=subject)

        subject = digest(request)
        task_id = request["task_id"]
        state = self._tasks.get(task_id)

        def deny(reason):
            return self._append("payment", "deny", reason, task_id=task_id,
                                policy_digest_=state.digest if state else None,
                                subject_digest=subject, request=request, state=state)

        if state is None:
            return deny(UNKNOWN_TASK)
        # The request names its task inside the signed body, and only that
        # task's agent key is accepted, so a key from another task fails here.
        if not keys.verify(state.policy["agent_key"], keys.CTX_REQUEST,
                           unsigned(request), request["signature"]):
            return deny(BAD_SIGNATURE)
        if self._revocations.is_revoked(task_id):
            return deny(REVOKED)
        now = self._clock()
        if now < state.not_before:
            return deny(NOT_YET_VALID)
        if now >= state.expires:
            return deny(EXPIRED)
        if request["request_id"] in state.used_request_ids:
            return deny(REPLAY)
        if request["asset"] != state.policy["asset"]:
            return deny(ASSET_MISMATCH)
        payee = request["counterparty"]
        if payee not in state.caps:
            return deny(NOT_LISTED)
        amount = request["amount_minor"]
        if state.spent[payee] + amount > state.caps[payee]:
            return deny(CAP_EXCEEDED)
        if state.spent_total + amount > state.policy["budget_minor"]:
            return deny(BUDGET_EXCEEDED)

        state.spent[payee] += amount
        state.spent_total += amount
        state.used_request_ids.add(request["request_id"])
        return self._append("payment", "allow", OK, task_id=task_id,
                            policy_digest_=state.digest, subject_digest=subject,
                            request=request, state=state)


def audit_log(records, engine_kid, policies, revocations=(), requests=None):
    """Re-check a decision log without trusting the engine. Returns a list of problems.

    policies: the signed policy objects. revocations: the signed statements.
    requests: optional {subject_digest: request}; when given, every allowed
    payment's request must be present and carry a valid agent signature.
    """
    problems = []
    by_digest = {}
    for policy in policies:
        try:
            by_digest[verify_policy(policy)] = policy
        except PolicyError as exc:
            problems.append(f"policy {policy.get('task_id')!r} does not verify: {exc}")
    statements = {digest(s): s for s in revocations}
    # A revocation the auditor holds counts even if the engine never logged it.
    signed_revoked_at = {}
    for statement in revocations:
        policy = by_digest.get(statement.get("policy_digest"))
        if policy is not None and verify_revocation(statement, policy):
            t = parse_time(statement["revoked_at"])
            signed_revoked_at[policy["task_id"]] = min(t, signed_revoked_at.get(policy["task_id"], t))
    tasks = {}
    revoked_at = {}
    prev = ZERO_DIGEST
    for i, record in enumerate(records):
        where = f"record {i}"
        if not verify_record(record, engine_kid):
            problems.append(f"{where}: signature does not verify")
            continue
        if record["seq"] != i or record["prev"] != prev:
            problems.append(f"{where}: chain broken")
        prev = digest(record)
        task_id, kind = record["task_id"], record["kind"]
        when = parse_time(record["evaluated_at"])

        if kind == "register":
            policy = by_digest.get(record["policy_digest"])
            if policy is None or policy["task_id"] != task_id:
                problems.append(f"{where}: registered policy not supplied")
                continue
            tasks[task_id] = _TaskState(policy, record["policy_digest"])
            continue
        state = tasks.get(task_id)
        if kind == "revoke":
            statement = statements.get(record["subject_digest"])
            if state is None or statement is None or not verify_revocation(statement, state.policy):
                problems.append(f"{where}: revocation statement missing or invalid")
            revoked_at.setdefault(task_id, when)
            continue
        if kind != "payment":
            problems.append(f"{where}: unknown kind")
            continue
        if record["decision"] == "deny":
            if state is not None and record["spent_total_minor"] != state.spent_total:
                problems.append(f"{where}: deny record reports wrong totals")
            continue
        # An allow must hold against the policy, the time and the running totals.
        if state is None:
            problems.append(f"{where}: allow for an unregistered task")
            continue
        payee, amount = record["counterparty"], record["amount_minor"]
        if task_id in revoked_at:
            problems.append(f"{where}: allow after revocation")
        elif task_id in signed_revoked_at and when > signed_revoked_at[task_id]:
            problems.append(f"{where}: allow after a signed revocation the log does not show")
        if not state.not_before <= when < state.expires:
            problems.append(f"{where}: allow outside the task window")
        if payee not in state.caps:
            problems.append(f"{where}: allow to an unlisted counterparty")
            continue
        if record["request_id"] in state.used_request_ids:
            problems.append(f"{where}: request id allowed twice")
        state.used_request_ids.add(record["request_id"])
        state.spent[payee] += amount
        state.spent_total += amount
        if state.spent[payee] > state.caps[payee]:
            problems.append(f"{where}: counterparty cap exceeded")
        if state.spent_total > state.policy["budget_minor"]:
            problems.append(f"{where}: task budget exceeded")
        if (record["spent_counterparty_minor"], record["spent_total_minor"]) != (
            state.spent[payee], state.spent_total
        ):
            problems.append(f"{where}: reported totals do not match the replay")
        if requests is not None:
            request = requests.get(record["subject_digest"])
            if request is None or digest(request) != record["subject_digest"]:
                problems.append(f"{where}: request not supplied")
            elif not keys.verify(state.policy["agent_key"], keys.CTX_REQUEST,
                                 unsigned(request), request["signature"]):
                problems.append(f"{where}: request signature does not verify")
            elif (request["task_id"], request["counterparty"], request["amount_minor"]) != (
                task_id, payee, amount
            ):
                problems.append(f"{where}: record does not match its request")
            elif request["asset"] != state.policy["asset"]:
                problems.append(f"{where}: allow in an asset the policy does not name")
    return problems
