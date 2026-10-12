"""The task-account policy object: schema, issuance and verification."""

import re
from datetime import datetime, timezone

from . import keys
from .canonical import CanonicalError, canonical_bytes, digest

POLICY_TYPE = "task-account/0.1"

_POLICY_KEYS = {
    "type",
    "task_id",
    "principal",
    "agent_key",
    "asset",
    "budget_minor",
    "counterparties",
    "not_before",
    "expires",
    "revocation",
    "signature",
}
_COUNTERPARTY_KEYS = {"id", "cap_minor"}
_COUNTERPARTY_OPTIONAL = {"rails"}
_REVOCATION_KEYS = {"by", "list"}

_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_ASSET_RE = re.compile(r"^[A-Z0-9]{2,12}$")
_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
MAX_COUNTERPARTIES = 64


class PolicyError(ValueError):
    """Raised when a policy object is malformed or its signature fails."""


def parse_time(text):
    """Parse 'YYYY-MM-DDTHH:MM:SSZ' (UTC only) to integer epoch seconds."""
    if not isinstance(text, str):
        raise PolicyError("time must be a string")
    try:
        parsed = datetime.strptime(text, _TIME_FORMAT)
    except ValueError as exc:
        raise PolicyError(f"bad time {text!r}") from exc
    return int(parsed.replace(tzinfo=timezone.utc).timestamp())


def format_time(epoch_seconds):
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).strftime(_TIME_FORMAT)


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def check_schema(policy):
    """Raise PolicyError unless policy has exactly the expected shape."""
    if not isinstance(policy, dict):
        raise PolicyError("policy must be an object")
    if set(policy) != _POLICY_KEYS:
        raise PolicyError(f"policy members must be exactly {sorted(_POLICY_KEYS)}")
    if policy["type"] != POLICY_TYPE:
        raise PolicyError("unsupported policy type")
    if not isinstance(policy["task_id"], str) or not _ID_RE.match(policy["task_id"]):
        raise PolicyError("bad task_id")
    for member in ("principal", "agent_key"):
        if not keys.is_key_id(policy[member]):
            raise PolicyError(f"bad {member}")
    if policy["principal"] == policy["agent_key"]:
        raise PolicyError("the agent key must differ from the principal key")
    if not isinstance(policy["asset"], str) or not _ASSET_RE.match(policy["asset"]):
        raise PolicyError("bad asset")
    if not _is_positive_int(policy["budget_minor"]):
        raise PolicyError("budget_minor must be a positive integer")

    parties = policy["counterparties"]
    if not isinstance(parties, list) or not 1 <= len(parties) <= MAX_COUNTERPARTIES:
        raise PolicyError("counterparties must be a non-empty list")
    seen = set()
    for party in parties:
        if not isinstance(party, dict):
            raise PolicyError("each counterparty must be an object")
        members = set(party)
        if not _COUNTERPARTY_KEYS <= members <= _COUNTERPARTY_KEYS | _COUNTERPARTY_OPTIONAL:
            raise PolicyError("counterparty members must be id, cap_minor and optional rails")
        if not isinstance(party["id"], str) or not _ID_RE.match(party["id"]):
            raise PolicyError("bad counterparty id")
        if party["id"] in seen:
            raise PolicyError(f"duplicate counterparty {party['id']}")
        seen.add(party["id"])
        if not _is_positive_int(party["cap_minor"]):
            raise PolicyError("cap_minor must be a positive integer")
        rails = party.get("rails", {})
        if not isinstance(rails, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in rails.items()
        ):
            raise PolicyError("rails must map strings to strings")

    if parse_time(policy["not_before"]) >= parse_time(policy["expires"]):
        raise PolicyError("not_before must be earlier than expires")

    revocation = policy["revocation"]
    if not isinstance(revocation, dict) or set(revocation) != _REVOCATION_KEYS:
        raise PolicyError("revocation must have members by and list")
    if revocation["by"] != "principal" or not isinstance(revocation["list"], str):
        raise PolicyError("revocation.by must be 'principal' and list a string")
    if not isinstance(policy["signature"], str):
        raise PolicyError("signature must be a string")
    try:
        canonical_bytes(policy)
    except CanonicalError as exc:
        raise PolicyError(str(exc)) from exc


def unsigned(obj):
    return {k: v for k, v in obj.items() if k != "signature"}


def verify_policy(policy):
    """Check shape and the principal's signature. Returns the policy digest."""
    check_schema(policy)
    if not keys.verify(policy["principal"], keys.CTX_POLICY, unsigned(policy), policy["signature"]):
        raise PolicyError("principal signature does not verify")
    return policy_digest(policy)


def policy_digest(policy):
    """Digest over the whole signed object, signature included."""
    return digest(policy)


def issue_task_account(
    principal_key,
    *,
    task_id,
    asset,
    budget_minor,
    counterparties,
    not_before,
    expires,
    revocation_list="local:revocations",
):
    """Create a fresh per-task agent key and the principal-signed policy naming it.

    Returns (policy, agent_private_key). The agent key exists for this task only.
    """
    agent_key = keys.new_key()
    body = {
        "type": POLICY_TYPE,
        "task_id": task_id,
        "principal": keys.key_id(principal_key),
        "agent_key": keys.key_id(agent_key),
        "asset": asset,
        "budget_minor": budget_minor,
        "counterparties": counterparties,
        "not_before": not_before,
        "expires": expires,
        "revocation": {"by": "principal", "list": revocation_list},
    }
    check_schema(dict(body, signature=""))
    policy = dict(body, signature=keys.sign(principal_key, keys.CTX_POLICY, body))
    verify_policy(policy)
    return policy, agent_key
