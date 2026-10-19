"""
Symmetric encryption for stored Zoho credentials and tokens.

A single master secret (``MCP_SECRET_KEY``) protects every per-user secret at
rest.  The value may be either a valid Fernet key or any sufficiently long
passphrase, in which case a key is derived with SHA-256.
"""

import base64
import hashlib
import os
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


class CryptoError(RuntimeError):
    """Raised when secrets cannot be decrypted."""


@lru_cache(maxsize=8)
def _fernet(secret: str) -> Fernet:
    raw = secret.encode("utf-8")
    try:
        return Fernet(raw)
    except Exception:
        derived = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
        return Fernet(derived)


def _secret() -> str:
    value = (os.getenv("MCP_SECRET_KEY") or "").strip()
    if not value:
        raise CryptoError(
            "MCP_SECRET_KEY is required to encrypt stored Zoho credentials. "
            "Generate one with: python -c \"import secrets;print(secrets.token_urlsafe(48))\""
        )
    return value


def is_configured() -> bool:
    """Return True when a master key is present."""
    return bool((os.getenv("MCP_SECRET_KEY") or "").strip())


def encrypt(plaintext: str) -> str:
    """Encrypt *plaintext* to an opaque token safe for storage."""
    return _fernet(_secret()).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(token: Optional[str]) -> Optional[str]:
    """Decrypt a stored token.  Returns None for None input."""
    if token is None:
        return None
    try:
        return _fernet(_secret()).decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:  # pragma: no cover - operator error
        raise CryptoError(
            "Stored secret could not be decrypted with the current MCP_SECRET_KEY. "
            "Did the master key change?"
        ) from exc
