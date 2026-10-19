"""
Small security helpers: signed session cookies and API-key hashing.

Only the standard library is used so the portal has no extra runtime
dependency beyond ``cryptography`` (for secret encryption).
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional

API_KEY_PREFIX = "zoho_"


# ---------------------------------------------------------------------------
# API keys
# ---------------------------------------------------------------------------
def generate_api_key() -> str:
    """Return a new opaque API key that is safe to show once."""
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    """Return the storage hash for an API key."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def api_key_prefix(key: str) -> str:
    """Return a short, non-secret prefix for display."""
    return key[:12]


# ---------------------------------------------------------------------------
# Signed session cookies
# ---------------------------------------------------------------------------
def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(secret: str, payload: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return _b64encode(digest)


def sign_session(data: Dict[str, Any], secret: str, ttl: int) -> str:
    """Serialise *data* into a signed, expiring cookie value."""
    body = dict(data)
    body["exp"] = int(time.time()) + int(ttl)
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    token = _b64encode(raw)
    return f"{token}.{_sign(secret, raw)}"


def verify_session(cookie: Optional[str], secret: str) -> Optional[Dict[str, Any]]:
    """Return the session payload, or None when invalid or expired."""
    if not cookie or "." not in cookie:
        return None
    token, signature = cookie.rsplit(".", 1)
    try:
        raw = _b64decode(token)
    except Exception:
        return None
    expected = _sign(secret, raw)
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    if int(data.get("exp", 0)) < int(time.time()):
        return None
    return data


def random_token(nbytes: int = 24) -> str:
    """Return a URL-safe random token (PKCE verifier, OAuth state, nonce)."""
    return secrets.token_urlsafe(nbytes)


def pkce_challenge(verifier: str) -> str:
    """Return the S256 PKCE challenge for *verifier*."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return _b64encode(digest)
