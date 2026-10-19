"""Startup guards for the streamable-HTTP transport.

The transport must never silently serve an unauthenticated ``/mcp`` endpoint.
These tests pin the three cases:

* loopback, no credentials  -> allowed (local dev) but warned about;
* non-loopback, no creds    -> refused at startup;
* ``MCP_REQUIRE_AUTH=true`` -> refused when nothing can satisfy it.
"""

import pytest


@pytest.fixture
def server(monkeypatch, tmp_path):
    monkeypatch.setenv("PORTAL_DB_PATH", str(tmp_path / "portal.db"))
    for name in ("PORTAL_ENABLED", "MCP_HTTP_TOKEN", "MCP_REQUIRE_AUTH"):
        monkeypatch.delenv(name, raising=False)

    import src.server as server_module

    return server_module


def test_loopback_without_auth_is_allowed(server, monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    app, host, port, path, portal = server._build_http_app()
    assert app is not None
    assert host == "127.0.0.1"
    assert portal is None


def test_non_loopback_without_auth_is_refused(server, monkeypatch):
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    with pytest.raises(SystemExit, match="non-loopback"):
        server._build_http_app()


def test_non_loopback_with_shared_token_is_allowed(server, monkeypatch):
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_HTTP_TOKEN", "s3cret")
    _app, host, _port, _path, _portal = server._build_http_app()
    assert host == "0.0.0.0"


def test_require_auth_without_credentials_fails_closed(server, monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_REQUIRE_AUTH", "true")
    with pytest.raises(SystemExit, match="MCP_REQUIRE_AUTH"):
        server._build_http_app()
