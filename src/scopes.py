"""
Zoho OAuth scope helpers.

Scope presets:

``all``
    Every scope for apps whose names were verified against Zoho's published API
    documentation.  This is the default because Zoho rejects the whole consent
    request with ``invalid_scope`` if a single scope is unknown, so shipping
    unverified guesses in the default set would break onboarding.

``recommended``
    The small, end-to-end validated core set (the reference token used while
    developing the server).

``everything``
    ``all`` plus the unverified, best-effort scopes.  Use this only if you have
    confirmed the extra scopes are accepted by your Zoho client; otherwise Zoho
    returns ``invalid_scope``.

Set ``ZOHO_SCOPE_INCLUDE_UNVERIFIED=true`` to append the unverified scopes to
``all`` without switching presets.

To trim a preset without writing the whole list, set ``ZOHO_SCOPE_EXCLUDE`` to
one or more comma/space separated scopes::

    ZOHO_SCOPE=all
    ZOHO_SCOPE_EXCLUDE=ZohoVault.secrets.ALL,ZohoCalendar.event.ALL
"""

import os
from typing import Dict, List

try:  # Support both ``import src.scopes`` and ``python src/server.py``.
    from .zoho_apps import APP_CONFIGS, app_is_verified
except ImportError:  # pragma: no cover - script mode
    from zoho_apps import APP_CONFIGS, app_is_verified


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

# Verified scopes that are not expressed by a single app's ``required_scopes``.
VERIFIED_EXTRA_SCOPES: List[str] = [
    "ZohoPeople.employee.ALL",
    "ZohoPeople.timetracker.ALL",
    "ZohoMail.messages.ALL",
    "ZohoMail.folders.ALL",
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


def _catalog_scopes(*, verified: bool) -> List[str]:
    """Return consent scopes for catalog apps with the given verification."""
    scopes: List[str] = []
    for config in APP_CONFIGS.values():
        if app_is_verified(config) != verified:
            continue
        for scope in config["required_scopes"]:
            # ``ZohoCreator`` is an app-level shorthand used for matching, not
            # a scope that should be sent on the consent URL.
            if scope.strip().lower() == "zohocreator":
                continue
            scopes.append(scope)
    return scopes


# Verified scopes: safe to put on a consent URL.
FULL_SCOPES: List[str] = _dedupe(
    _catalog_scopes(verified=True) + KNOWN_SCOPES + VERIFIED_EXTRA_SCOPES
)

# Unverified scopes: best effort; a wrong name fails the whole consent request.
UNVERIFIED_SCOPES: List[str] = _dedupe(_catalog_scopes(verified=False))

# ``everything`` is *all* + the unverified additions.
EVERYTHING_SCOPES: List[str] = _dedupe(FULL_SCOPES + UNVERIFIED_SCOPES)

# A smaller, validated set for users who hit a Zoho ``invalid_scope`` error.
RECOMMENDED_SCOPES: List[str] = _dedupe(KNOWN_SCOPES)

SCOPE_PRESETS: Dict[str, List[str]] = {
    "all": FULL_SCOPES,
    "recommended": RECOMMENDED_SCOPES,
    "everything": EVERYTHING_SCOPES,
}

_ALL_ALIASES = {"all", "*", "full", "fullaccess"}


def _excluded_scopes() -> set:
    raw = (os.getenv("ZOHO_SCOPE_EXCLUDE") or "").replace(",", " ")
    return {scope.strip().lower() for scope in raw.split() if scope.strip()}


def _include_unverified() -> bool:
    return (os.getenv("ZOHO_SCOPE_INCLUDE_UNVERIFIED") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def is_all_scopes(scope_string: str) -> bool:
    """Return True when *scope_string* requests a full-access preset."""
    value = (scope_string or "").strip().lower()
    return value in _ALL_ALIASES or value == "everything"


def resolve_scopes(scope_string: str) -> List[str]:
    """Resolve a preset, or parse an explicit comma/space separated list."""
    value = (scope_string or "").strip()
    if not value:
        return []

    key = value.lower()
    if key == "everything":
        scopes = list(EVERYTHING_SCOPES)
    elif key in _ALL_ALIASES:
        scopes = list(FULL_SCOPES)
        if _include_unverified():
            scopes = _dedupe(scopes + UNVERIFIED_SCOPES)
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

    ``all``/``*`` expands to :data:`FULL_SCOPES`, ``recommended`` expands to
    :data:`RECOMMENDED_SCOPES`, ``everything`` expands to
    :data:`EVERYTHING_SCOPES`; any other value is treated as an explicit list.
    """
    return ",".join(resolve_scopes(scope_string))
