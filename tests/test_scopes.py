"""Tests for the scope presets and the app catalog."""

from urllib.parse import parse_qs, urlparse

from src.app_registry import AppRegistry
from src.scopes import (
    EVERYTHING_SCOPES,
    FULL_SCOPES,
    RECOMMENDED_SCOPES,
    UNVERIFIED_SCOPES,
    expand_scopes,
    is_all_scopes,
    resolve_scopes,
)
from src.zoho_apps import (
    APP_CONFIGS,
    UNVERIFIED_APP_NAMES,
    VERIFIED_APP_NAMES,
)
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


def test_all_preset_excludes_unverified_scopes():
    # A single unknown scope fails the entire consent, so ``all`` only ships
    # scopes confirmed against Zoho's docs.
    assert "ZohoTeamInbox.channels.ALL" not in FULL_SCOPES
    assert "ZohoTeamInbox.channels.ALL" in UNVERIFIED_SCOPES
    assert "WorkDrive.files.ALL" in FULL_SCOPES
    assert "ZohoSalesIQ.modules.ALL" not in FULL_SCOPES
    assert "SalesIQ.portals.ALL" in FULL_SCOPES
    assert "ZohoMarketingAutomation.campaign.ALL" in FULL_SCOPES
    assert "PageSense.experiments.READ" in FULL_SCOPES


def test_everything_preset_includes_unverified_scopes():
    scopes = resolve_scopes("everything")
    for scope in UNVERIFIED_SCOPES:
        assert scope in scopes
    assert "ZohoCRM.modules.ALL" in scopes
    assert len(EVERYTHING_SCOPES) == len(FULL_SCOPES) + len(UNVERIFIED_SCOPES)


def test_include_unverified_env_appends(monkeypatch):
    monkeypatch.setenv("ZOHO_SCOPE_INCLUDE_UNVERIFIED", "true")
    scopes = resolve_scopes("all")
    assert "ZohoTeamInbox.channels.ALL" in scopes


def test_app_verification_flags_partition_the_catalog():
    assert set(VERIFIED_APP_NAMES).isdisjoint(UNVERIFIED_APP_NAMES)
    assert "CRM" in VERIFIED_APP_NAMES
    assert "TeamInbox" in UNVERIFIED_APP_NAMES
    assert len(VERIFIED_APP_NAMES) + len(UNVERIFIED_APP_NAMES) == len(APP_CONFIGS)


def test_known_wrong_scopes_are_gone():
    for stale in [
        "ZohoSalesIQ.modules.ALL",
        "ZohoWorkDrive.files.ALL",
        "ZohoSheet.spreadsheets.ALL",
        "ZohoBookings.bookings.ALL",
        "ZohoAssist.session.ALL",
        "ZohoMarketingHub.campaigns.ALL",
        "ZohoPageSense.projects.ALL",
        "ZohoSocial.data.ALL",
        "ZohoConnect.network.ALL",
        "ZohoMeeting.recording.ALL",
    ]:
        assert stale not in FULL_SCOPES


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
        "ZohoVault.secrets.ALL, ZohoCalendar.event.ALL",
    )
    scopes = resolve_scopes("all")
    assert "ZohoVault.secrets.ALL" not in scopes
    assert "ZohoCalendar.event.ALL" not in scopes
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
