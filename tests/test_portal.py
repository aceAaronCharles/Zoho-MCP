"""Tests for the multi-tenant connection portal."""

import json
import time
from urllib.parse import parse_qs, urlparse

import pytest

from src.portal import crypto, security
from src.portal.connections import (
    ConnectionManager,
    accounts_domain_for,
    api_domain_for,
    authorization_url,
    normalize_dc,
)
from src.portal.db import Database
from src.runtime import ActiveContext, RouterProxy, get_active_context, reset_active_context, set_active_context


@pytest.fixture(autouse=True)
def master_key(monkeypatch):
    monkeypatch.setenv("MCP_SECRET_KEY", "test-master-key-for-portal-tests")
    crypto._fernet.cache_clear()
    yield
    crypto._fernet.cache_clear()


@pytest.fixture()
def store(tmp_path):
    db = Database(str(tmp_path / "portal.db"))
    db.init_schema()
    return db


# ---------------------------------------------------------------------------
# Crypto / security
# ---------------------------------------------------------------------------
def test_crypto_roundtrip():
    token = crypto.encrypt("s3cret-value")
    assert token != "s3cret-value"
    assert crypto.decrypt(token) == "s3cret-value"
    assert crypto.decrypt(None) is None


def test_session_sign_and_verify():
    cookie = security.sign_session({"uid": 7}, "secret", ttl=60)
    payload = security.verify_session(cookie, "secret")
    assert payload and payload["uid"] == 7
    assert security.verify_session(cookie, "wrong-secret") is None
    assert security.verify_session(cookie + "x", "secret") is None


def test_session_expiry():
    cookie = security.sign_session({"uid": 1}, "secret", ttl=-1)
    assert security.verify_session(cookie, "secret") is None


def test_api_key_hash_is_deterministic():
    key = security.generate_api_key()
    assert key.startswith("zoho_")
    assert security.hash_api_key(key) == security.hash_api_key(key)
    assert security.hash_api_key(key) != key


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def test_user_and_connection_lifecycle(store):
    user = store.upsert_user("oidc", "sub-1", "a@example.com", "Alice")
    assert user["id"]

    conn = store.create_connection(
        user["id"], "client-123", "secret-abc", "eu", "all", "https://host/oauth/zoho/callback"
    )
    # The plaintext secret must not be stored verbatim.
    assert conn["client_secret"] == "secret-abc"
    assert conn["status"] == "pending"

    store.store_tokens(
        conn["id"],
        {"access_token": "at", "refresh_token": "rt", "scope": "ZohoCRM.modules.ALL"},
        access_expires_at=time.time() + 3600,
        granted_scopes="ZohoCRM.modules.ALL",
        api_domain="https://www.zohoapis.eu",
    )
    reloaded = store.get_connection_for_user(user["id"])
    assert reloaded["status"] == "connected"
    assert reloaded["refresh_token"] == "rt"
    assert reloaded["access_token"] == "at"
    assert reloaded["granted_scopes"] == "ZohoCRM.modules.ALL"


def test_upsert_user_is_idempotent(store):
    first = store.upsert_user("oidc", "sub-2", "b@example.com", "Bob")
    second = store.upsert_user("oidc", "sub-2", "b2@example.com", "Bobby")
    assert first["id"] == second["id"]
    assert second["email"] == "b2@example.com"


def test_api_key_lookup_and_revoke(store):
    user = store.upsert_user("oidc", "sub-3", "c@example.com", "Carol")
    key = security.generate_api_key()
    record = store.create_api_key(user["id"], security.hash_api_key(key), security.api_key_prefix(key), "laptop")
    found = store.find_api_key(security.hash_api_key(key))
    assert found and found["id"] == record["id"]
    store.revoke_api_key(record["id"], user["id"])
    assert store.find_api_key(security.hash_api_key(key)) is None


def test_oauth_state_is_single_use(store):
    user = store.upsert_user("oidc", "sub-4", "d@example.com", "Dan")
    conn = store.create_connection(user["id"], "cid", "sec", "com", "all", "https://h/cb")
    store.create_state("state-1", user["id"], conn["id"])
    assert store.consume_state("state-1")["connection_id"] == conn["id"]
    assert store.consume_state("state-1") is None


def test_connection_is_unique_per_user(store):
    user = store.upsert_user("oidc", "sub-5", "e@example.com", "Eve")
    store.create_connection(user["id"], "cid1", "sec1", "com", "all", "https://h/cb")
    store.create_connection(user["id"], "cid2", "sec2", "eu", "all", "https://h/cb")
    connection = store.get_connection_for_user(user["id"])
    assert connection["client_id"] == "cid2"
    assert connection["dc"] == "eu"
    assert connection["status"] == "pending"


# ---------------------------------------------------------------------------
# Data-centre helpers
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "dc,accounts,api",
    [
        ("com", "https://accounts.zoho.com", "https://www.zohoapis.com"),
        ("eu", "https://accounts.zoho.eu", "https://www.zohoapis.eu"),
        ("ca", "https://accounts.zohocloud.ca", "https://www.zohoapis.ca"),
    ],
)
def test_datacentre_domains(dc, accounts, api):
    assert accounts_domain_for(dc) == accounts
    assert api_domain_for(dc) == api


def test_normalize_dc():
    assert normalize_dc("EU") == "eu"
    assert normalize_dc("nonsense") == "com"
    assert normalize_dc(None) == "com"


def test_authorization_url_contains_offline_consent():
    url = authorization_url(
        {"dc": "com", "client_id": "abc", "scopes": "ZohoCRM.modules.ALL"},
        "https://host/oauth/zoho/callback",
    )
    assert url.startswith("https://accounts.zoho.com/oauth/v2/auth?")
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    assert "client_id=abc" in url


def test_authorization_url_expands_scope_presets():
    url = authorization_url(
        {"dc": "com", "client_id": "abc", "scopes": "recommended"},
        "https://host/oauth/zoho/callback",
    )
    scope = parse_qs(urlparse(url).query)["scope"][0]
    assert scope != "recommended"
    assert "ZohoCRM.modules.ALL" in scope
    assert "ZohoVault.secrets.ALL" not in scope

    url_all = authorization_url(
        {"dc": "com", "client_id": "abc", "scopes": "all"},
        "https://host/oauth/zoho/callback",
    )
    scope_all = parse_qs(urlparse(url_all).query)["scope"][0]
    assert "ZohoVault.secrets.ALL" in scope_all
    assert "ZohoCRM.modules.ALL" in scope_all


# ---------------------------------------------------------------------------
# Manager / runtime dispatch
# ---------------------------------------------------------------------------
def _make_connection(store):
    user = store.upsert_user("oidc", "sub-9", "z@example.com", "Zoe")
    store.create_connection(user["id"], "cid", "sec", "com", "all", "https://h/cb")
    store.store_tokens(
        user["id"] and store.get_connection_for_user(user["id"])["id"],
        {"access_token": "at", "refresh_token": "rt"},
        access_expires_at=time.time() + 3600,
        granted_scopes="ZohoCRM.modules.ALL ZohoBooks.fullaccess.all",
    )
    return user, store.get_connection_for_user(user["id"])


def test_connection_manager_builds_context(store):
    user, connection = _make_connection(store)
    manager = ConnectionManager(store)
    context = manager.context_for_connection(connection, user)
    assert isinstance(context, ActiveContext)
    assert context.user["email"] == "z@example.com"
    assert context.router.auth.refresh_token == "rt"
    # Registry reflects the granted scopes.
    enabled = [app.name for app in context.registry.list_enabled_apps()]
    assert "CRM" in enabled


def test_connection_manager_caches_context(store):
    user, connection = _make_connection(store)
    manager = ConnectionManager(store)
    first = manager.context_for_connection(connection, user)
    second = manager.context_for_connection(connection, user)
    assert first is second
    manager.invalidate(connection["id"])
    assert manager.context_for_connection(connection, user) is not first


def test_router_proxy_dispatches_to_active_context(store):
    user, connection = _make_connection(store)
    manager = ConnectionManager(store)
    context = manager.context_for_connection(connection, user)

    class DummyRouter:
        def make_request(self, **kwargs):
            return {"status": "success", "marker": "active"}

    fallback = DummyRouter()
    proxy = RouterProxy(fallback)
    assert proxy.make_request(app_name="CRM", endpoint="Leads")["marker"] == "active"

    active = ActiveContext(router=DummyRouter(), registry=context.registry)
    token = set_active_context(active)
    try:
        assert proxy.make_request(app_name="CRM", endpoint="Leads")["marker"] == "active"
        assert get_active_context() is active
    finally:
        reset_active_context(token)
    assert proxy.make_request(app_name="CRM", endpoint="Leads")["marker"] == "active"


def test_accounts_domain_survives_environment_dc_override(store, monkeypatch):
    # A global ZOHO_DC must not leak into per-user connections.
    monkeypatch.setenv("ZOHO_DC", "in")
    user, connection = _make_connection(store)
    manager = ConnectionManager(store)
    context = manager.context_for_connection(connection, user)
    assert context.router.auth.get_data_center() == "com"
    assert context.router.auth.accounts_domain == "https://accounts.zoho.com"


# ---------------------------------------------------------------------------
# Bearer resolution
# ---------------------------------------------------------------------------
def test_resolve_bearer_maps_key_to_connection(store):
    from src.portal.app import BearerError, Portal
    from src.portal.config import PortalConfig

    user, _ = _make_connection(store)
    key = security.generate_api_key()
    store.create_api_key(user["id"], security.hash_api_key(key), security.api_key_prefix(key), None)

    portal = Portal(PortalConfig(enabled=True), store, ConnectionManager(store), None)
    context = portal.resolve_bearer(key)
    assert context.connection["client_id"] == "cid"

    with pytest.raises(BearerError):
        portal.resolve_bearer("zoho_not-a-real-key")


def test_resolve_bearer_without_connection(store):
    from src.portal.app import BearerError, Portal
    from src.portal.config import PortalConfig

    user = store.upsert_user("oidc", "sub-11", "n@example.com", "No Conn")
    key = security.generate_api_key()
    store.create_api_key(user["id"], security.hash_api_key(key), security.api_key_prefix(key), None)

    portal = Portal(PortalConfig(enabled=True), store, ConnectionManager(store), None)
    with pytest.raises(BearerError) as exc:
        portal.resolve_bearer(key)
    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# OIDC
# ---------------------------------------------------------------------------
def test_oidc_authorization_url_uses_pkce():
    from src.portal.oidc import OIDCClient

    client = OIDCClient(
        "https://idp.example",
        "client-id",
        "client-secret",
        "https://host/portal/auth/callback",
        "openid email profile",
    )
    client._discovery = {
        "authorization_endpoint": "https://idp.example/authorize",
        "token_endpoint": "https://idp.example/token",
    }
    client._discovery_at = time.time()

    url = client.build_authorization_url("state-1", "nonce-1", "verifier-1")
    assert url.startswith("https://idp.example/authorize?")
    assert "code_challenge_method=S256" in url
    assert "code_challenge=" + security.pkce_challenge("verifier-1") in url
    assert "state=state-1" in url
    assert "nonce=nonce-1" in url
    assert "scope=openid+email+profile" in url


def test_oidc_userinfo_falls_back_without_endpoint():
    from src.portal.oidc import OIDCClient

    client = OIDCClient("https://idp.example", "c", "s", "https://h/cb")
    client._discovery = {
        "authorization_endpoint": "https://idp.example/authorize",
        "token_endpoint": "https://idp.example/token",
    }
    client._discovery_at = time.time()
    assert client.userinfo("token", fallback={"sub": "fallback"}) == {"sub": "fallback"}


def test_portal_config_from_env(monkeypatch):
    from src.portal.config import PortalConfig

    monkeypatch.setenv("PORTAL_ENABLED", "true")
    monkeypatch.setenv("PORTAL_BASE_URL", "https://zoho.example.com/")
    monkeypatch.setenv("MCP_SECRET_KEY", "a-secret")
    monkeypatch.delenv("PORTAL_SESSION_SECRET", raising=False)
    monkeypatch.delenv("ZOHO_OAUTH_REDIRECT_URI", raising=False)

    config = PortalConfig.from_env()
    assert config.enabled is True
    assert config.base_url == "https://zoho.example.com"
    assert config.zoho_redirect_uri == "https://zoho.example.com/oauth/zoho/callback"
    assert config.oidc_redirect_uri == "https://zoho.example.com/portal/auth/callback"
    assert config.cookie_secure is True
    assert config.session_secret == "a-secret"


# ---------------------------------------------------------------------------
# Server integration
# ---------------------------------------------------------------------------
def test_server_registers_tools_and_portal_disabled():
    import src.server as server

    tool_names = [tool.name for tool in server.mcp._tool_manager.list_tools()]
    assert len(tool_names) >= 70
    assert "zoho_api_request" in tool_names
    assert "get_configuration_status" in tool_names
    # Portal is disabled unless PORTAL_ENABLED is set.
    assert server._build_portal() is None


def test_build_portal_requires_master_key(monkeypatch):
    import src.server as server

    monkeypatch.setenv("PORTAL_ENABLED", "true")
    monkeypatch.delenv("MCP_SECRET_KEY", raising=False)
    with pytest.raises(SystemExit):
        server._build_portal()


def test_mcp_http_dispatches_per_user_connection(tmp_path, monkeypatch):
    """Tool calls over HTTP must use the Zoho connection of the key's owner."""
    pytest.importorskip("httpx")
    from starlette.testclient import TestClient

    import src.server as server

    monkeypatch.setenv("PORTAL_ENABLED", "true")
    monkeypatch.setenv("PORTAL_DEV_LOGIN", "true")
    monkeypatch.setenv("PORTAL_DB_PATH", str(tmp_path / "portal.db"))
    monkeypatch.setenv("PORTAL_BASE_URL", "http://testserver")
    monkeypatch.setenv("MCP_HTTP_JSON_RESPONSE", "true")
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "testserver")
    monkeypatch.delenv("MCP_HTTP_TOKEN", raising=False)

    db = Database(str(tmp_path / "portal.db"))
    db.init_schema()

    def seed(email, client_id):
        user = db.upsert_user("dev", email, email, email.split("@")[0])
        db.create_connection(user["id"], client_id, "secret", "com", "all", "https://h/cb")
        connection = db.get_connection_for_user(user["id"])
        db.store_tokens(
            connection["id"],
            {"access_token": "at", "refresh_token": "rt"},
            time.time() + 3600,
            "ZohoCRM.modules.ALL",
            "https://www.zohoapis.com",
            "https://accounts.zoho.com",
        )
        key = security.generate_api_key()
        db.create_api_key(user["id"], security.hash_api_key(key), security.api_key_prefix(key), None)
        return key

    owner_key = seed("owner@example.com", "client-owner")
    other_key = seed("other@example.com", "client-other")

    app, _host, _port, _path, portal = server._build_http_app()
    assert portal is not None

    with TestClient(app) as client:
        headers = {"Authorization": f"Bearer {owner_key}", "Accept": "application/json"}
        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            },
        )
        assert response.status_code == 200
        session_id = response.headers["mcp-session-id"]

        session_headers = dict(headers)
        session_headers["mcp-session-id"] = session_id
        call = client.post(
            "/mcp",
            headers=session_headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "get_configuration_status", "arguments": {}},
            },
        )
        assert call.status_code == 200
        payload = call.json()["result"]["content"][0]["text"]
        assert '"user": "owner@example.com"' in payload
        assert '"enabled_apps": 1' in payload

        catalog = client.post(
            "/mcp",
            headers=session_headers,
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "list_zoho_apps", "arguments": {}},
            },
        )
        assert catalog.status_code == 200
        catalog_payload = json.loads(catalog.json()["result"]["content"][0]["text"])
        assert catalog_payload["count"] == 46
        assert catalog_payload["enabled_count"] == 1
        vault = next(
            app for app in catalog_payload["apps"] if app["name"] == "Vault"
        )
        assert vault["missing_scopes"] == ["ZohoVault.secrets.ALL"]

        consent = client.post(
            "/mcp",
            headers=session_headers,
            json={
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "get_zoho_authorization_url",
                    "arguments": {"scopes": "all"},
                },
            },
        )
        assert consent.status_code == 200
        consent_payload = json.loads(consent.json()["result"]["content"][0]["text"])
        assert consent_payload["status"] == "success"
        assert "client-owner" in consent_payload["authorization_url"]
        assert "ZohoVault.secrets.ALL" in consent_payload["scopes"]
        assert "client_secret" not in consent_payload["authorization_url"]

        # A second account gets its own connection, never the owner's.
        other_init = client.post(
            "/mcp",
            headers={
                "Authorization": f"Bearer {other_key}",
                "Accept": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": 7,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            },
        )
        assert other_init.status_code == 200
        other_session = other_init.headers["mcp-session-id"]
        assert other_session != session_id
        other_call = client.post(
            "/mcp",
            headers={
                "Authorization": f"Bearer {other_key}",
                "Accept": "application/json",
                "mcp-session-id": other_session,
            },
            json={
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "get_zoho_authorization_url",
                    "arguments": {"scopes": "recommended"},
                },
            },
        )
        assert other_call.status_code == 200
        other_payload = json.loads(other_call.json()["result"]["content"][0]["text"])
        assert "client-other" in other_payload["authorization_url"]
        assert "client-owner" not in other_payload["authorization_url"]

        # Another account cannot reuse this MCP session.
        stolen = dict(session_headers)
        stolen["Authorization"] = f"Bearer {other_key}"
        rejected = client.post(
            "/mcp",
            headers=stolen,
            json={"jsonrpc": "2.0", "id": 3, "method": "tools/list"},
        )
        assert rejected.status_code == 404

        # And unauthenticated requests never reach the transport.
        anonymous = client.post(
            "/mcp",
            headers={"Accept": "application/json"},
            json={"jsonrpc": "2.0", "id": 4, "method": "tools/list"},
        )
        assert anonymous.status_code == 401
