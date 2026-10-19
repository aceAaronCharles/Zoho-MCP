"""Tests for the scope presets and the app catalog."""

from urllib.parse import parse_qs, urlparse

from src.app_registry import AppRegistry
from src.scopes import (
    FULL_SCOPES,
    RECOMMENDED_SCOPES,
    expand_scopes,
    is_all_scopes,
    resolve_scopes,
)
from src.zoho_apps import APP_CONFIGS
from src.zoho_auth import accounts_domain_for, build_authorization_url


def test_catalog_covers_the_zoho_suite():
    assert len(APP_CONFIGS) >= 45
    for name in [
        "CRM",
        "Books",
        "Inventory",
        "Projects",
        "Desk",
        "People",
        "Recruit",
        "Analytics",
        "Creator",
        "Mail",
        "Calendar",
        "WorkDrive",
        "Sign",
        "Bookings",
    ]:
        assert name in APP_CONFIGS


def test_all_preset_enables_every_catalog_app():
    registry = AppRegistry("all")
    assert len(registry.list_enabled_apps()) == len(APP_CONFIGS)
    assert all(app.enabled for app in registry.list_all_apps())


def test_full_scopes_have_no_duplicates():
    keys = [scope.lower() for scope in FULL_SCOPES]
    assert len(keys) == len(set(keys))


def test_creator_shorthand_is_not_sent_to_zoho():
    # ``ZohoCreator`` is only a matching shorthand; the consent URL uses the
    # granular scopes instead.
    assert "ZohoCreator" not in FULL_SCOPES
    assert any(scope.startswith("ZohoCreator.") for scope in FULL_SCOPES)


def test_recommended_preset_is_the_validated_set():
    assert len(RECOMMENDED_SCOPES) == 23
    assert expand_scopes("recommended") == ",".join(RECOMMENDED_SCOPES)
    assert "ZohoVault.secrets.ALL" not in RECOMMENDED_SCOPES


def test_explicit_scope_list_accepts_commas_and_spaces():
    scopes = resolve_scopes(
        "ZohoCRM.modules.ALL, ZohoBooks.fullaccess.all Desk.tickets.ALL"
    )
    assert scopes == [
        "ZohoCRM.modules.ALL",
        "ZohoBooks.fullaccess.all",
        "Desk.tickets.ALL",
    ]


def test_scope_exclusion(monkeypatch):
    monkeypatch.setenv(
        "ZOHO_SCOPE_EXCLUDE",
        "ZohoVault.secrets.ALL, ZohoTeamInbox.channels.ALL",
    )
    scopes = resolve_scopes("all")
    assert "ZohoVault.secrets.ALL" not in scopes
    assert "ZohoTeamInbox.channels.ALL" not in scopes
    assert "ZohoCRM.modules.ALL" in scopes


def test_is_all_scopes():
    for value in ["all", "ALL", "*", "full", "fullaccess"]:
        assert is_all_scopes(value)
    assert not is_all_scopes("recommended")


def test_accounts_domain_for_data_centres():
    assert accounts_domain_for("com") == "https://accounts.zoho.com"
    assert accounts_domain_for("eu") == "https://accounts.zoho.eu"
    assert accounts_domain_for("ca") == "https://accounts.zohocloud.ca"


def test_build_authorization_url_includes_oauth_parameters():
    url = build_authorization_url(
        "https://accounts.zoho.eu/",
        "client-id",
        "https://example.com/oauth/zoho/callback",
        "ZohoCRM.modules.ALL,ZohoBooks.fullaccess.all",
    )
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.zoho.eu"
    assert parsed.path == "/oauth/v2/auth"

    params = parse_qs(parsed.query)
    assert params["client_id"] == ["client-id"]
    assert params["response_type"] == ["code"]
    assert params["access_type"] == ["offline"]
    assert params["prompt"] == ["consent"]
    assert params["redirect_uri"] == ["https://example.com/oauth/zoho/callback"]
    assert params["scope"] == [
        "ZohoCRM.modules.ALL,ZohoBooks.fullaccess.all"
    ]
