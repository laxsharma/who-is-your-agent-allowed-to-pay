"""Canonical JSON bytes and digests.

The canonical form is: object keys sorted, no insignificant whitespace, UTF-8,
and a restricted value set (strings, integers with magnitude below 2**53,
booleans, null, arrays, objects with ASCII keys). Floats are refused so that
every amount is an integer count of minor units.

This subset is meant to produce the same bytes as RFC 8785 for these value
types. That equivalence has not been tested against an RFC 8785
implementation.
"""

import hashlib
import json

MAX_SAFE_INT = 2**53 - 1


class CanonicalError(ValueError):
    """Raised when a value cannot be put in canonical form."""


def _check(value, path="$"):
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int):
        if abs(value) > MAX_SAFE_INT:
            raise CanonicalError(f"{path}: integer outside the safe range")
        return
    if isinstance(value, float):
        raise CanonicalError(f"{path}: floats are not allowed, use integer minor units")
    if isinstance(value, list):
        for i, item in enumerate(value):
            _check(item, f"{path}[{i}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key.isascii():
                raise CanonicalError(f"{path}: object keys must be ASCII strings")
            _check(item, f"{path}.{key}")
        return
    raise CanonicalError(f"{path}: unsupported type {type(value).__name__}")


def canonical_bytes(value):
    """Return the canonical UTF-8 encoding of value."""
    _check(value)
    text = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return text.encode("utf-8")


def digest(value):
    """Return 'sha256:<hex>' over the canonical bytes of value."""
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


ZERO_DIGEST = "sha256:" + "0" * 64
