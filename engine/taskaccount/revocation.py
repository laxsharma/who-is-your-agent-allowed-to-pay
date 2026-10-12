"""Principal-signed revocation statements and a list of them.

Revocation is one step: the principal signs one statement naming the task and
the digest of the policy it ends. Anyone holding the policy can verify the
statement offline with the principal key named inside the policy. There is no
un-revoke.
"""

from . import keys
from .canonical import digest
from .policy import POLICY_TYPE, format_time, policy_digest, unsigned

REVOCATION_TYPE = "task-revocation/0.1"
_KEYS = {"type", "task_id", "policy_digest", "revoked_at", "signature"}


class RevocationError(ValueError):
    """Raised when a revocation statement is malformed or does not verify."""


def make_revocation(principal_key, policy, revoked_at_epoch):
    body = {
        "type": REVOCATION_TYPE,
        "task_id": policy["task_id"],
        "policy_digest": policy_digest(policy),
        "revoked_at": format_time(revoked_at_epoch),
    }
    return dict(body, signature=keys.sign(principal_key, keys.CTX_REVOCATION, body))


def verify_revocation(statement, policy):
    """True if statement is a valid revocation of exactly this policy."""
    if not isinstance(statement, dict) or set(statement) != _KEYS:
        return False
    if statement["type"] != REVOCATION_TYPE or policy.get("type") != POLICY_TYPE:
        return False
    if statement["task_id"] != policy["task_id"]:
        return False
    if statement["policy_digest"] != policy_digest(policy):
        return False
    return keys.verify(
        policy["principal"], keys.CTX_REVOCATION, unsigned(statement), statement["signature"]
    )


class RevocationList:
    """Append-only set of verified revocation statements, keyed by task_id."""

    def __init__(self):
        self._by_task = {}

    def add(self, statement, policy):
        if not verify_revocation(statement, policy):
            raise RevocationError("revocation statement does not verify against the policy")
        self._by_task.setdefault(statement["task_id"], statement)

    def is_revoked(self, task_id):
        return task_id in self._by_task

    def statements(self):
        return [self._by_task[t] for t in sorted(self._by_task)]

    def list_digest(self):
        return digest(self.statements())
