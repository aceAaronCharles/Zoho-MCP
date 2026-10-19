"""
Portal configuration.

Everything the multi-tenant setup interface needs is read from the
environment so the same image can be configured for local development or a
hosted deployment.  Nothing here touches Zoho credentials; those belong to
each individual user and live in the encrypted connection store.
"""

import os
from dataclasses import dataclass


def _flag(name: str, default: bool = False) -> bool:
    value = (os.getenv(name) or "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int((os.getenv(name) or "").strip() or default)
    except (TypeError, ValueError):
        return default


@dataclass
class PortalConfig:
    """Resolved settings for the connection portal."""

    enabled: bool = False
    base_url: str = "http://localhost:8000"
    db_path: str = "portal.db"
    session_secret: str = ""
    session_ttl: int = 60 * 60 * 24 * 7
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_scopes: str = "openid email profile"
    oidc_provider_name: str = "SSO"
    zoho_redirect_uri: str = ""
    cookie_secure: bool = False
    allow_dev_login: bool = False

    @classmethod
    def from_env(cls) -> "PortalConfig":
        base_url = (os.getenv("PORTAL_BASE_URL") or "http://localhost:8000").rstrip("/")
        redirect_uri = (os.getenv("ZOHO_OAUTH_REDIRECT_URI") or "").strip()
        if not redirect_uri:
            redirect_uri = f"{base_url}/oauth/zoho/callback"

        issuer = (os.getenv("PORTAL_OIDC_ISSUER") or "").strip()
        client_id = (os.getenv("PORTAL_OIDC_CLIENT_ID") or "").strip()
        client_secret = (os.getenv("PORTAL_OIDC_CLIENT_SECRET") or "").strip()

        session_secret = (
            (os.getenv("PORTAL_SESSION_SECRET") or "").strip()
            or (os.getenv("MCP_SECRET_KEY") or "").strip()
        )

        return cls(
            enabled=_flag("PORTAL_ENABLED", False),
            base_url=base_url,
            db_path=(os.getenv("PORTAL_DB_PATH") or "portal.db").strip(),
            session_secret=session_secret,
            session_ttl=_int("PORTAL_SESSION_TTL", 60 * 60 * 24 * 7),
            oidc_issuer=issuer,
            oidc_client_id=client_id,
            oidc_client_secret=client_secret,
            oidc_scopes=(os.getenv("PORTAL_OIDC_SCOPES") or "openid email profile").strip(),
            oidc_provider_name=(os.getenv("PORTAL_OIDC_NAME") or "SSO").strip(),
            zoho_redirect_uri=redirect_uri,
            cookie_secure=_flag("PORTAL_COOKIE_SECURE", base_url.startswith("https://")),
            allow_dev_login=_flag("PORTAL_DEV_LOGIN", False),
        )

    @property
    def oidc_redirect_uri(self) -> str:
        """The callback URL that must be registered with the identity provider."""
        return f"{self.base_url}/portal/auth/callback"

    def oidc_configured(self) -> bool:
        return bool(self.oidc_issuer and self.oidc_client_id and self.oidc_client_secret)
