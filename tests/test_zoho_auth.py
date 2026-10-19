"""Tests for the refresh-token auth handler's token persistence."""

import json
import os
import time

from src.zoho_auth import ZohoAuth


def _auth(**kwargs):
    return ZohoAuth(
        client_id="client",
        client_secret="secret",
        redirect_uri="http://localhost:8080/callback",
        scope="all",
        **kwargs,
    )


def test_save_tokens_updates_memory_without_a_file():
    auth = _auth(token_file_path=None, refresh_token="refresh")
    before = time.time()
    auth._save_tokens({"access_token": "access", "expires_in": 1800})
    assert auth.access_token == "access"
    assert auth.refresh_token == "refresh"
    assert auth.token_expires_at >= before + 1700
    assert auth.token_expires_at <= time.time() + 1800


def test_save_tokens_writes_private_file(tmp_path):
    path = tmp_path / "nested" / ".zoho_tokens.json"
    auth = _auth(token_file_path=str(path), refresh_token="refresh")
    auth._save_tokens(
        {"access_token": "access", "expires_in": 3600, "api_domain": "https://www.zohoapis.eu"}
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["access_token"] == "access"
    assert data["refresh_token"] == "refresh"
    assert data["api_domain"] == "https://www.zohoapis.eu"
    assert oct(os.stat(path).st_mode & 0o777) == "0o600"
    assert auth.access_token == "access"


def test_save_tokens_survives_an_unwritable_path(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    auth = _auth(token_file_path=str(blocker / "tokens.json"), refresh_token="refresh")

    # Must not raise: the token stays available in memory.
    auth._save_tokens({"access_token": "access", "expires_in": 60})
    assert auth.access_token == "access"
    assert auth.refresh_token == "refresh"
