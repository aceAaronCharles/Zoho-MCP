"""
Zoho OAuth scope helpers.

``ZOHO_SCOPE=all`` is a convenience preset that expands to every scope this
server knows about.  ``ZOHO_SCOPE=recommended`` expands to the smaller set that
has been validated end to end.  Zoho still requires each API to be authorised
for the client, and a refresh token can only ever contain scopes that were
granted when it was created.

To trim a preset without writing the whole list, set ``ZOHO_SCOPE_EXCLUDE`` to
one or more comma/space separated scopes::

    ZOHO_SCOPE=all
    ZOHO_SCOPE_EXCLUDE=ZohoVault.secrets.ALL,ZohoTeamInbox.channels.ALL
"""

import os
from typing import Dict, List

try:  # Support both ``import src.scopes`` and ``python src/server.py``.
    from .zoho_apps import APP_CONFIGS
except ImportError:  # pragma: no cover - script mode
    from zoho_apps import APP_CONFIGS


# Scopes present in the reference token used while developing the server.
# ``recommended`` uses exactly this set: it is known to be accepted by Zoho and
# covers the apps with dedicated tools.
KNOWN_SCOPES: List[str] = [
    "ZohoCRM.modules.ALL",
    "ZohoCRM.settings.ALL",
    "ZohoCRM.users.ALL",
    "ZohoBooks.fullaccess.all",
    "ZohoInventory.fullaccess.all",
    "ZohoAnalytics.fullaccess.all",
    "ZohoProjects.portals.ALL",
    "ZohoProjects.projects.ALL",
    "ZohoProjects.tasks.ALL",
    "Desk.tickets.ALL",
    "Desk.contacts.ALL",
    "Desk.settings.ALL",
    "ZohoPeople.forms.ALL",
    "ZohoPeople.attendance.ALL",
    "ZohoPeople.leave.ALL",
    "ZohoRecruit.modules.ALL",
    "ZohoCreator.data.ALL",
    "ZohoCreator.meta.READ",
    "ZohoCreator.report.READ",
    "ZohoCreator.report.CREATE",
    "ZohoCreator.report.UPDATE",
    "ZohoMail.accounts.ALL",
    "ZohoMeeting.meeting.ALL",
]

# Additional scopes used by apps that do not have dedicated tools yet.  The
# generic ``zoho_api_request`` tool can use them once the refresh token has
# been granted the matching permission.
EXTRA_SCOPES: List[str] = [
    "ZohoSalesIQ.modules.ALL",
    "ZohoCampaigns.campaign.ALL",
    "ZohoSocial.data.ALL",
    "ZohoForms.form.ALL",
    "ZohoSurvey.surveys.ALL",
    "ZohoInvoice.fullaccess.all",
    "ZohoExpense.fullaccess.all",
    "ZohoSubscriptions.fullaccess.all",
    "ZohoCommerce.fullaccess.all",
    "ZohoAssist.session.ALL",
    "ZohoSprints.projects.ALL",
    "ZohoBugTracker.projects.ALL",
    "ZohoConnect.network.ALL",
    "ZohoCliq.channels.ALL",
    "ZohoCliq.messages.ALL",
    "ZohoMeeting.recording.ALL",
    "ZohoMail.messages.ALL",
    "ZohoMail.folders.ALL",
    "ZohoWorkDrive.files.ALL",
    "ZohoWorkDrive.team.ALL",
    "ZohoWorkDrive.workspace.ALL",
    "ZohoWorkDrive.users.ALL",
    "ZohoWriter.documents.ALL",
    "ZohoSheet.spreadsheets.ALL",
    "ZohoShow.presentations.ALL",
    "ZohoFlow.flows.ALL",
    "ZohoCatalyst.projects.ALL",
    "ZohoFleet.modules.ALL",
    "ZohoFSM.modules.ALL",
    "ZohoSign.documents.ALL",
    "ZohoContracts.contracts.ALL",
    "ZohoIoT.devices.ALL",
    "ZohoBookings.bookings.ALL",
    "ZohoCalendar.calendar.ALL",
    "ZohoVault.secrets.ALL",
    "ZohoDirectory.users.ALL",
    "ZohoLearn.courses.ALL",
    "ZohoPractice.clients.ALL",
    "ZohoPayroll.fullaccess.all",
    "ZohoTeamInbox.channels.ALL",
    "ZohoMarketingHub.campaigns.ALL",
    "ZohoPageSense.projects.ALL",
]


def _dedupe(scopes: List[str]) -> List[str]:
    """Return scopes in order without case-insensitive duplicates."""
    seen = set()
    result: List[str] = []
    for scope in scopes:
        scope = scope.strip()
        if not scope:
            continue
        key = scope.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(scope)
    return result


def _catalog_scopes() -> List[str]:
    """Return the scopes needed to reach every app in the catalog."""
    scopes: List[str] = []
    for config in APP_CONFIGS.values():
        for scope in config["required_scopes"]:
            # ``ZohoCreator`` is an app-level shorthand used for matching, not
            # a scope that should be sent on the consent URL.
            if scope.strip().lower() == "zohocreator":
                continue
            scopes.append(scope)
    return scopes


# Every scope this server knows about, derived from the app catalog so the two
# can never drift apart.
FULL_SCOPES: List[str] = _dedupe(
    _catalog_scopes() + KNOWN_SCOPES + EXTRA_SCOPES
)

# A smaller, validated set for users who hit a Zoho ``invalid_scope`` error.
RECOMMENDED_SCOPES: List[str] = _dedupe(KNOWN_SCOPES)

SCOPE_PRESETS: Dict[str, List[str]] = {
    "all": FULL_SCOPES,
    "recommended": RECOMMENDED_SCOPES,
}


def _excluded_scopes() -> set:
    raw = (os.getenv("ZOHO_SCOPE_EXCLUDE") or "").replace(",", " ")
    return {scope.strip().lower() for scope in raw.split() if scope.strip()}


def is_all_scopes(scope_string: str) -> bool:
    """Return True when *scope_string* requests the full-access preset."""
    value = (scope_string or "").strip().lower()
    return value in {"all", "*", "full", "fullaccess"}


def resolve_scopes(scope_string: str) -> List[str]:
    """Resolve a preset, or parse an explicit comma/space separated list."""
    value = (scope_string or "").strip()
    if not value:
        return []

    key = value.lower()
    if key in {"all", "*", "full", "fullaccess"}:
        scopes = list(FULL_SCOPES)
    elif key == "recommended":
        scopes = list(RECOMMENDED_SCOPES)
    else:
        normalized = value.replace(",", " ")
        scopes = _dedupe(normalized.split())

    excluded = _excluded_scopes()
    if excluded:
        scopes = [scope for scope in scopes if scope.lower() not in excluded]
    return scopes


def expand_scopes(scope_string: str) -> str:
    """
    Expand a scope preset into a comma-separated scope list.

    ``all``/``*`` expands to :data:`FULL_SCOPES`; ``recommended`` expands to
    :data:`RECOMMENDED_SCOPES`; any other value is treated as an explicit list.
    """
    return ",".join(resolve_scopes(scope_string))
