"""
Per-user Zoho connections.

Each user of the portal brings their own Zoho API client ID/secret, completes
the OAuth consent flow, and the resulting refresh token is stored (encrypted)
in SQLite.  This module turns that stored connection into a ready-to-use
:class:`~src.api_router.APIRouter` and tracks the request-scoped context used
by the MCP tools.
"""

import logging
import threading
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

try:  # Support both package and script imports.
    from ..api_router import APIRouter
    from ..app_registry import AppRegistry
    from ..runtime import ActiveContext
    from ..scopes import expand_scopes
    from ..zoho_auth import DC_HOSTS, ZohoAuth
except ImportError:  # pragma: no cover - script mode
    from api_router import APIRouter
    from app_registry import AppRegistry
    from runtime import ActiveContext
    from scopes import expand_scopes
    from zoho_auth import DC_HOSTS, ZohoAuth

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data-centre helpers
# ---------------------------------------------------------------------------
def accounts_domain_for(dc: str) -> str:
    host = DC_HOSTS.get(dc, f"zoho.{dc}")
    return f"https://accounts.{host}"


def api_domain_for(dc: str) -> str:
    return f"https://www.zohoapis.{dc}"


def normalize_dc(dc: Optional[str]) -> str:
    dc = (dc or "com").strip().lower()
    return dc if dc in DC_HOSTS else "com"


def authorization_url(connection: Dict[str, Any], redirect_uri: str) -> str:
    """Build the Zoho consent URL for a pending connection."""
    params = {
        "scope": expand_scopes(connection.get("scopes") or "all"),
        "client_id": connection.get("client_id") or "",
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{accounts_domain_for(connection['dc'])}/oauth/v2/auth?{urlencode(params)}"


def exchange_code(
    connection: Dict[str, Any], code: str, redirect_uri: str
) -> Dict[str, Any]:
    """Exchange an authorization code for tokens, raising on failure."""
    url = f"{accounts_domain_for(connection['dc'])}/oauth/v2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": connection.get("client_id"),
        "client_secret": connection.get("client_secret"),
        "redirect_uri": redirect_uri,
        "code": code,
    }
    response = requests.post(url, data=payload, timeout=30)
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Zoho returned a non-JSON token response ({response.status_code})") from exc
    if not data.get("access_token"):
        error = data.get("error") or f"HTTP {response.status_code}"
        raise RuntimeError(f"Zoho token exchange failed: {error}")
    return data


# ---------------------------------------------------------------------------
# Connection-backed auth
# ---------------------------------------------------------------------------
class ConnectionAuth(ZohoAuth):
    """A :class:`ZohoAuth` whose tokens live in the portal database."""

    def __init__(self, connection: Dict[str, Any], store):
        self._store = store
        self._connection_id = connection["id"]
        self._dc = normalize_dc(connection.get("dc"))
        api_domain = connection.get("api_domain") or api_domain_for(self._dc)
        accounts_domain = connection.get("accounts_domain") or accounts_domain_for(self._dc)
        scopes = connection.get("granted_scopes") or connection.get("scopes") or "all"

        super().__init__(
            client_id=connection["client_id"],
            client_secret=connection["client_secret"],
            redirect_uri=connection["redirect_uri"],
            scope=expand_scopes(scopes),
            token_file_path=None,
            api_domain=api_domain,
            accounts_domain=accounts_domain,
            refresh_token=connection.get("refresh_token"),
        )

        # Seed any cached access token so the first call avoids a refresh.
        if connection.get("access_token"):
            self.access_token = connection["access_token"]
        if connection.get("access_expires_at"):
            self.token_expires_at = connection["access_expires_at"]
        if connection.get("api_domain"):
            self.api_domain_for_tokens = connection["api_domain"]
        if connection.get("granted_scopes"):
            self.granted_scope = connection["granted_scopes"]

    def get_data_center(self) -> str:
        """Always use the data centre stored with the connection."""
        return self._dc

    def _save_tokens(self, tokens: Dict[str, Any]) -> None:
        """Persist refreshed tokens to the database, never to a file."""
        super()._save_tokens(tokens)  # updates in-memory state
        try:
            self._store.store_tokens(
                self._connection_id,
                tokens,
                access_expires_at=self.token_expires_at,
                granted_scopes=self.granted_scope,
                api_domain=self.api_domain_for_tokens,
                accounts_domain=self.accounts_domain,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not persist tokens for connection %s: %s", self._connection_id, exc)


# ---------------------------------------------------------------------------
# Manager / cache
# ---------------------------------------------------------------------------
class ConnectionManager:
    """Builds and caches request contexts for user connections."""

    def __init__(self, store):
        self.store = store
        self._contexts: Dict[int, ActiveContext] = {}
        self._lock = threading.Lock()

    def invalidate(self, connection_id: int) -> None:
        with self._lock:
            self._contexts.pop(connection_id, None)

    def _build(self, connection: Dict[str, Any], user: Optional[dict]) -> ActiveContext:
        auth = ConnectionAuth(connection, self.store)
        registry = AppRegistry(auth.scope or "all")
        router = APIRouter(auth, registry)
        return ActiveContext(router=router, registry=registry, user=user, connection=connection)

    def context_for_connection(
        self, connection: Dict[str, Any], user: Optional[dict] = None
    ) -> ActiveContext:
        key = connection["id"]
        cached = self._contexts.get(key)
        if cached is not None:
            if user is not None:
                cached.user = user
            return cached
        context = self._build(connection, user)
        with self._lock:
            self._contexts[key] = context
        return context

    def context_for_user(self, user: Dict[str, Any]) -> Optional[ActiveContext]:
        connection = self.store.get_connection_for_user(user["id"])
        if not connection:
            return None
        return self.context_for_connection(connection, user)
