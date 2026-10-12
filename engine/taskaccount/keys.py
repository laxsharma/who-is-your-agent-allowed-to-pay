"""Ed25519 keys, key identifiers and domain-separated signatures."""

import base64
import binascii

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .canonical import canonical_bytes

KEY_PREFIX = "ed25519:"

# Each signed object type has its own context string, so a signature made for
# one kind of object can never verify as another kind.
CTX_POLICY = "task-account/0.1 policy"
CTX_REQUEST = "task-account/0.1 payment-request"
CTX_REVOCATION = "task-account/0.1 revocation"
CTX_RECORD = "task-account/0.1 decision-record"


def b64u(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64u_decode(text):
    """Strict base64url decoding: alphabet checked, padding-free form only."""
    if not isinstance(text, str) or not text.isascii():
        raise ValueError("not base64url text")
    padded = text + "=" * (-len(text) % 4)
    try:
        raw = base64.b64decode(padded, altchars=b"-_", validate=True)
    except binascii.Error as exc:
        raise ValueError("not base64url text") from exc
    if b64u(raw) != text:
        raise ValueError("non-canonical base64url")
    return raw


def new_key():
    """Generate a fresh Ed25519 private key."""
    return Ed25519PrivateKey.generate()


def key_id(key):
    """Identifier 'ed25519:<base64url raw public key>' for a private or public key."""
    if isinstance(key, Ed25519PrivateKey):
        key = key.public_key()
    raw = key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return KEY_PREFIX + b64u(raw)


def load_public(kid):
    if not isinstance(kid, str) or not kid.startswith(KEY_PREFIX):
        raise ValueError("unsupported key identifier")
    raw = b64u_decode(kid[len(KEY_PREFIX):])
    if len(raw) != 32:
        raise ValueError("Ed25519 public keys are 32 bytes")
    return Ed25519PublicKey.from_public_bytes(raw)


def is_key_id(kid):
    try:
        load_public(kid)
    except ValueError:
        return False
    return True


def signing_input(context, body):
    return context.encode("ascii") + b"\x00" + canonical_bytes(body)


def sign(private_key, context, body):
    return b64u(private_key.sign(signing_input(context, body)))


def verify(kid, context, body, signature):
    """True only if signature is a valid Ed25519 signature by kid over body."""
    try:
        public_key = load_public(kid)
        raw_sig = b64u_decode(signature)
        public_key.verify(raw_sig, signing_input(context, body))
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True
