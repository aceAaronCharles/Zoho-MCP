"""
Minimal, provider-agnostic OpenID Connect client.

Supports any issuer that publishes ``/.well-known/openid-configuration``
(Google, Microsoft Entra, Okta, Auth0, Keycloak, ...).  GitHub is plain
OAuth2 and is not supported by this generic client.

Only the authorization-code flow with PKCE is implemented.  The user profile
is read from the ``userinfo`` endpoint so no JWT verification is required.
"""

import logging
import threading
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .security import pkce_challenge, random_token

logger = logging.getLogger(__name__)


class OIDCError(RuntimeError):
    """Raised when the identity provider cannot be used."""


class OIDCClient:
    def __init__(
        self,
        issuer: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: str = "openid email profile",
        timeout: int = 15,
    ):
        self.issuer = issuer.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.timeout = timeout
        self._discovery: Optional[Dict[str, Any]] = None
        self._discovery_at = 0.0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    def discovery(self) -> Dict[str, Any]:
        with self._lock:
            if self._discovery and time.time() - self._discovery_at < 3600:
                return self._discovery
            url = f"{self.issuer}/.well-known/openid-configuration"
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                raise OIDCError(f"Could not load OIDC discovery from {url}: {exc}") from exc
            for key in ("authorization_endpoint", "token_endpoint"):
                if not data.get(key):
                    raise OIDCError(f"OIDC discovery document is missing {key}")
            self._discovery = data
            self._discovery_at = time.time()
            return data

    # ------------------------------------------------------------------
    # Authorization request
    # ------------------------------------------------------------------
    def build_authorization_url(self, state: str, nonce: str, code_verifier: str) -> str:
        endpoints = self.discovery()
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes,
            "state": state,
            "nonce": nonce,
            "code_challenge": pkce_challenge(code_verifier),
            "code_challenge_method": "S256",
        }
        return f"{endpoints['authorization_endpoint']}?{urlencode(params)}"

    # ------------------------------------------------------------------
    # Token exchange
    # ------------------------------------------------------------------
    def exchange_code(self, code: str, code_verifier: str) -> Dict[str, Any]:
        endpoints = self.discovery()
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code_verifier": code_verifier,
        }
        try:
            response = requests.post(
                endpoints["token_endpoint"],
                data=payload,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
        except Exception as exc:
            raise OIDCError(f"Token exchange failed: {exc}") from exc
        if response.status_code != 200:
            raise OIDCError(
                f"Identity provider rejected the token exchange ({response.status_code})"
            )
        return response.json()

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------
    def userinfo(self, access_token: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        endpoints = self.discovery()
        url = endpoints.get("userinfo_endpoint")
        if url:
            try:
                response = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning("userinfo endpoint returned %s", response.status_code)
            except Exception as exc:
                logger.warning("Could not read userinfo: %s", exc)
        return fallback or {}

    @staticmethod
    def new_pkce_verifier() -> str:
        return random_token(48)
