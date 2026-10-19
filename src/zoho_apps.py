"""
Catalog of Zoho applications known to this server.

This module is the single source of truth for app metadata.  It is imported by
both :mod:`src.app_registry` (to decide which apps are enabled) and
:mod:`src.scopes` (to build the ``all`` OAuth scope preset), so adding an app
here automatically makes it available to both.

``custom_domain`` may contain ``{host}``, which is replaced with the data
centre suffix for the token (``zoho.com``, ``zoho.eu``, ``zohocloud.ca``, ...).
Apps without a custom domain use the token's API domain (for example
``https://www.zohoapis.com``).

Every app can be reached through the generic ``zoho_api_request`` tool.  Apps
with dedicated tools simply add convenience wrappers on top of the same
router.  If a Zoho endpoint changes, set ``ZOHO_<APP>_BASE_URL`` to override
the origin without editing this file.

``required_scopes`` are the scopes needed to reach the app.  ``scopes_verified``
records whether those scope names were confirmed against Zoho's published API
documentation.  Unverified apps are still reachable (send the scopes
explicitly, or set ``ZOHO_SCOPE_INCLUDE_UNVERIFIED=true``), but they are left
out of the default ``all`` consent preset so a single guessed scope cannot make
the whole consent request fail with ``invalid_scope``.
"""

APP_CONFIGS = {
    # ------------------------------------------------------------------
    # Sales & Marketing
    # ------------------------------------------------------------------
    "CRM": {
        "api_path": "/crm/v2.1",
        "required_scopes": ["ZohoCRM.modules.ALL"],
        "api_version": "v2.1",
        "category": "Sales",
    },
    "SalesIQ": {
        # Service name is ``SalesIQ`` (not ``ZohoSalesIQ``); module names come
        # from the SalesIQ REST API scope table.
        "api_path": "/api/v2",
        "required_scopes": [
            "SalesIQ.portals.ALL",
            "SalesIQ.operators.ALL",
            "SalesIQ.conversations.ALL",
            "SalesIQ.Apps.ALL",
        ],
        "api_version": "v2",
        "category": "Sales",
        "custom_domain": "salesiq.{host}",
    },
    "Bookings": {
        # Zoho Bookings documents a single ``ZohoBookings.data.CREATE`` scope
        # that grants the supported booking actions.
        "api_path": "/api/v1",
        "required_scopes": ["ZohoBookings.data.CREATE"],
        "api_version": "v1",
        "category": "Operations",
        "custom_domain": "bookings.{host}",
    },
    "Campaigns": {
        "api_path": "/api/v1.1",
        "required_scopes": [
            "ZohoCampaigns.campaign.ALL",
            "ZohoCampaigns.contact.ALL",
        ],
        "api_version": "v1.1",
        "category": "Marketing",
        "custom_domain": "campaigns.{host}",
    },
    "Social": {
        # Zoho Social publishes four scopes; there is no ``ZohoSocial.data``.
        "api_path": "/api/v1",
        "required_scopes": [
            "ZohoSocial.Organization.READ",
            "ZohoSocial.Integration.READ",
            "ZohoSocial.Publish.ALL",
            "ZohoSocial.Media.ALL",
        ],
        "api_version": "v1",
        "category": "Marketing",
        "custom_domain": "social.{host}",
    },
    "Forms": {
        "api_path": "/api/v2",
        "required_scopes": ["ZohoForms.forms.ALL"],
        "api_version": "v2",
        "category": "Marketing",
        "custom_domain": "forms.{host}",
        "scopes_verified": False,
    },
    "Survey": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoSurvey.survey.ALL"],
        "api_version": "v1",
        "category": "Marketing",
        "custom_domain": "survey.{host}",
        "scopes_verified": False,
    },
    "MarketingHub": {
        # MarketingHub is the new name for Marketing Automation; the OAuth
        # service name is still ``ZohoMarketingAutomation``.
        "api_path": "/api/v1",
        "required_scopes": [
            "ZohoMarketingAutomation.campaign.ALL",
            "ZohoMarketingAutomation.lead.ALL",
        ],
        "api_version": "v1",
        "category": "Marketing",
        "custom_domain": "marketinghub.{host}",
    },
    "PageSense": {
        # Zoho PageSense uses the bare ``PageSense`` service name and
        # per-feature operation scopes.
        "api_path": "/api/v1",
        "required_scopes": [
            "PageSense.experiments.CREATE",
            "PageSense.experiments.READ",
            "PageSense.experiments.UPDATE",
            "PageSense.goals.CREATE",
            "PageSense.goals.READ",
            "PageSense.goals.UPDATE",
            "PageSense.goals.DELETE",
            "PageSense.audience.READ",
            "PageSense.audience.UPDATE",
            "PageSense.reports.all",
            "PageSense.customevents.CREATE",
            "PageSense.customevents.READ",
        ],
        "api_version": "v1",
        "category": "Marketing",
        "custom_domain": "pagesense.{host}",
    },
    # ------------------------------------------------------------------
    # Finance & Commerce
    # ------------------------------------------------------------------
    "Books": {
        "api_path": "/books/v3",
        "required_scopes": ["ZohoBooks.fullaccess.all"],
        "api_version": "v3",
        "category": "Finance",
    },
    "Invoice": {
        "api_path": "/invoice/v3",
        "required_scopes": ["ZohoInvoice.fullaccess.all"],
        "api_version": "v3",
        "category": "Finance",
    },
    "Expense": {
        "api_path": "/expense/v1",
        "required_scopes": ["ZohoExpense.fullaccess.all"],
        "api_version": "v1",
        "category": "Finance",
    },
    "Inventory": {
        "api_path": "/inventory/v1",
        "required_scopes": ["ZohoInventory.fullaccess.all"],
        "api_version": "v1",
        "category": "Finance",
    },
    "Subscriptions": {
        "api_path": "/subscriptions/v1",
        "required_scopes": ["ZohoSubscriptions.fullaccess.all"],
        "api_version": "v1",
        "category": "Finance",
    },
    "Commerce": {
        "api_path": "/commerce/v1",
        "required_scopes": ["ZohoCommerce.fullaccess.all"],
        "api_version": "v1",
        "category": "Commerce",
        "scopes_verified": False,
    },
    # ------------------------------------------------------------------
    # Customer Service
    # ------------------------------------------------------------------
    "Desk": {
        "api_path": "/api/v1",
        "required_scopes": ["Desk.tickets.ALL"],
        "api_version": "v1",
        "category": "Service",
        "custom_domain": "desk.{host}",
    },
    "Assist": {
        # Zoho Assist modules are ``sessionapi``, ``userapi``,
        # ``reportapi`` and ``unattended.*``.
        "api_path": "/api/v2",
        "required_scopes": [
            "ZohoAssist.sessionapi.CREATE",
            "ZohoAssist.userapi.READ",
            "ZohoAssist.reportapi.READ",
            "ZohoAssist.unattended.device.CREATE",
            "ZohoAssist.unattended.group.READ",
            "ZohoAssist.unattended.computer.READ",
        ],
        "api_version": "v2",
        "category": "Service",
        "custom_domain": "assist.{host}",
    },
    # ------------------------------------------------------------------
    # HR & Recruitment
    # ------------------------------------------------------------------
    "People": {
        "api_path": "/people/api",
        "required_scopes": ["ZohoPeople.forms.ALL"],
        "api_version": "api",
        "category": "HR",
        "custom_domain": "people.{host}",
    },
    "Recruit": {
        "api_path": "/recruit/v2",
        "required_scopes": ["ZohoRecruit.modules.ALL"],
        "api_version": "v2",
        "category": "HR",
        "custom_domain": "recruit.{host}",
    },
    "Payroll": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoPayroll.fullaccess.all"],
        "api_version": "v1",
        "category": "HR",
        "custom_domain": "payroll.{host}",
        "scopes_verified": False,
    },
    # ------------------------------------------------------------------
    # Project Management
    # ------------------------------------------------------------------
    "Projects": {
        "api_path": "/restapi",
        "required_scopes": ["ZohoProjects.projects.ALL"],
        "api_version": "v2",
        "category": "Projects",
        "custom_domain": "projectsapi.{host}",
    },
    "Sprints": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoSprints.projects.ALL"],
        "api_version": "v1",
        "category": "Projects",
        "custom_domain": "sprints.{host}",
        "scopes_verified": False,
    },
    "BugTracker": {
        "api_path": "/api/v2",
        "required_scopes": ["ZohoBugTracker.projects.ALL"],
        "api_version": "v2",
        "category": "Projects",
        "custom_domain": "bugtracker.{host}",
        "scopes_verified": False,
    },
    "Practice": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoPractice.clients.ALL"],
        "api_version": "v1",
        "category": "Projects",
        "custom_domain": "practice.{host}",
        "scopes_verified": False,
    },
    # ------------------------------------------------------------------
    # Collaboration
    # ------------------------------------------------------------------
    "Connect": {
        # Zoho Connect's public API scopes use the ``ZohoPulse`` service name.
        "api_path": "/api/v2",
        "required_scopes": ["ZohoPulse.feedList.ALL"],
        "api_version": "v2",
        "category": "Collaboration",
        "custom_domain": "connect.{host}",
        "scopes_verified": False,
    },
    "Cliq": {
        "api_path": "/api/v2",
        "required_scopes": [
            "ZohoCliq.Channels.ALL",
            "ZohoCliq.Messages.ALL",
            "ZohoCliq.Chats.ALL",
        ],
        "api_version": "v2",
        "category": "Collaboration",
        "custom_domain": "cliq.{host}",
    },
    "Meeting": {
        "api_path": "/api/v2",
        "required_scopes": [
            "ZohoMeeting.meeting.ALL",
            "ZohoMeeting.webinar.ALL",
            "ZohoMeeting.manageOrg.READ",
        ],
        "api_version": "v2",
        "category": "Collaboration",
        "custom_domain": "meeting.{host}",
    },
    "Calendar": {
        "api_path": "/api/v1",
        "required_scopes": [
            "ZohoCalendar.calendar.ALL",
            "ZohoCalendar.event.ALL",
            "ZohoCalendar.search.READ",
        ],
        "api_version": "v1",
        "category": "Collaboration",
        "custom_domain": "calendar.{host}",
    },
    # ------------------------------------------------------------------
    # Email, Storage & Productivity
    # ------------------------------------------------------------------
    "Mail": {
        "api_path": "/api",
        "required_scopes": ["ZohoMail.accounts.ALL"],
        "api_version": "v1",
        "category": "Email",
        "custom_domain": "mail.{host}",
    },
    "TeamInbox": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoTeamInbox.channels.ALL"],
        "api_version": "v1",
        "category": "Email",
        "custom_domain": "teaminbox.{host}",
        "scopes_verified": False,
    },
    "WorkDrive": {
        # Service name is ``WorkDrive`` (not ``ZohoWorkDrive``).
        "api_path": "/api/v1",
        "required_scopes": [
            "WorkDrive.files.ALL",
            "WorkDrive.team.ALL",
            "WorkDrive.teamfolders.ALL",
            "WorkDrive.groups.ALL",
            "WorkDrive.links.ALL",
        ],
        "api_version": "v1",
        "category": "Storage",
        "custom_domain": "workdrive.{host}",
    },
    "Writer": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoWriter.documents.ALL"],
        "api_version": "v1",
        "category": "Productivity",
        "custom_domain": "writer.{host}",
        "scopes_verified": False,
    },
    "Sheet": {
        # Zoho Sheet exposes a ``dataAPI`` scope with READ/UPDATE.
        "api_path": "/api/v1",
        "required_scopes": [
            "ZohoSheet.dataAPI.READ",
            "ZohoSheet.dataAPI.UPDATE",
        ],
        "api_version": "v1",
        "category": "Productivity",
        "custom_domain": "sheet.{host}",
    },
    "Show": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoShow.presentations.ALL"],
        "api_version": "v1",
        "category": "Productivity",
        "custom_domain": "show.{host}",
        "scopes_verified": False,
    },
    "Learn": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoLearn.courses.ALL"],
        "api_version": "v1",
        "category": "Productivity",
        "custom_domain": "learn.{host}",
        "scopes_verified": False,
    },
    # ------------------------------------------------------------------
    # Analytics, Developer & Automation
    # ------------------------------------------------------------------
    "Analytics": {
        "api_path": "/restapi/v2",
        "required_scopes": ["ZohoAnalytics.fullaccess.all"],
        "api_version": "v2",
        "category": "Analytics",
        "custom_domain": "analyticsapi.{host}",
    },
    "Creator": {
        "api_path": "/creator/v2",
        # ``ZohoCreator`` is an app-level shorthand matched against the
        # granular Creator scopes; it is not sent on the consent URL.
        "required_scopes": ["ZohoCreator"],
        "api_version": "v2",
        "category": "Developer",
    },
    "Flow": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoFlow.flows.ALL"],
        "api_version": "v1",
        "category": "Developer",
        "custom_domain": "flow.{host}",
        "scopes_verified": False,
    },
    "Catalyst": {
        "api_path": "/baas/v1",
        "required_scopes": ["ZohoCatalyst.projects.ALL"],
        "api_version": "v1",
        "category": "Developer",
        "custom_domain": "api.catalyst.{host}",
    },
    # ------------------------------------------------------------------
    # Operations & Field Service
    # ------------------------------------------------------------------
    "Fleet": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoFleet.modules.ALL"],
        "api_version": "v1",
        "category": "Operations",
        "custom_domain": "fleet.{host}",
        "scopes_verified": False,
    },
    "FSM": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoFSM.modules.ALL"],
        "api_version": "v1",
        "category": "Operations",
        "custom_domain": "fsm.{host}",
        "scopes_verified": False,
    },
    # ------------------------------------------------------------------
    # Legal, Security & Admin
    # ------------------------------------------------------------------
    "Sign": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoSign.documents.ALL"],
        "api_version": "v1",
        "category": "Legal",
        "custom_domain": "sign.{host}",
    },
    "Contracts": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoContracts.contracts.ALL"],
        "api_version": "v1",
        "category": "Legal",
        "custom_domain": "contracts.{host}",
        "scopes_verified": False,
    },
    "Vault": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoVault.secrets.ALL"],
        "api_version": "v1",
        "category": "Security",
        "custom_domain": "vault.{host}",
    },
    "Directory": {
        "api_path": "/api/v1",
        "required_scopes": [
            "ZohoDirectory.users.ALL",
            "ZohoDirectory.groups.ALL",
        ],
        "api_version": "v1",
        "category": "Admin",
        "custom_domain": "directory.{host}",
    },
    # ------------------------------------------------------------------
    # IoT & Specialized
    # ------------------------------------------------------------------
    "IoT": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoIoT.devices.ALL"],
        "api_version": "v1",
        "category": "IoT",
        "custom_domain": "iot.{host}",
        "scopes_verified": False,
    },
}


def app_is_verified(config: dict) -> bool:
    """Return True when an app's scope names are confirmed against Zoho docs."""
    return bool(config.get("scopes_verified", True))


# Scope names may only be sent to Zoho for apps whose names are verified.
VERIFIED_APP_NAMES = [
    name for name, config in APP_CONFIGS.items() if app_is_verified(config)
]
UNVERIFIED_APP_NAMES = [
    name for name, config in APP_CONFIGS.items() if not app_is_verified(config)
]
