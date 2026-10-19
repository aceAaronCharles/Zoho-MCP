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
        "api_path": "/api/v2",
        "required_scopes": ["ZohoSalesIQ.modules.ALL"],
        "api_version": "v2",
        "category": "Sales",
        "custom_domain": "salesiq.{host}",
    },
    "Bookings": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoBookings.bookings.ALL"],
        "api_version": "v1",
        "category": "Operations",
        "custom_domain": "bookings.{host}",
    },
    "Campaigns": {
        "api_path": "/api/v1.1",
        "required_scopes": ["ZohoCampaigns.campaign.ALL"],
        "api_version": "v1.1",
        "category": "Marketing",
        "custom_domain": "campaigns.{host}",
    },
    "Social": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoSocial.data.ALL"],
        "api_version": "v1",
        "category": "Marketing",
        "custom_domain": "social.{host}",
    },
    "Forms": {
        "api_path": "/api/v2",
        "required_scopes": ["ZohoForms.form.ALL"],
        "api_version": "v2",
        "category": "Marketing",
        "custom_domain": "forms.{host}",
    },
    "Survey": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoSurvey.surveys.ALL"],
        "api_version": "v1",
        "category": "Marketing",
        "custom_domain": "survey.{host}",
    },
    "MarketingHub": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoMarketingHub.campaigns.ALL"],
        "api_version": "v1",
        "category": "Marketing",
        "custom_domain": "marketinghub.{host}",
    },
    "PageSense": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoPageSense.projects.ALL"],
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
        "api_path": "/api/v2",
        "required_scopes": ["ZohoAssist.session.ALL"],
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
    },
    "BugTracker": {
        "api_path": "/api/v2",
        "required_scopes": ["ZohoBugTracker.projects.ALL"],
        "api_version": "v2",
        "category": "Projects",
        "custom_domain": "bugtracker.{host}",
    },
    "Practice": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoPractice.clients.ALL"],
        "api_version": "v1",
        "category": "Projects",
        "custom_domain": "practice.{host}",
    },
    # ------------------------------------------------------------------
    # Collaboration
    # ------------------------------------------------------------------
    "Connect": {
        "api_path": "/api/v2",
        "required_scopes": ["ZohoConnect.network.ALL"],
        "api_version": "v2",
        "category": "Collaboration",
        "custom_domain": "connect.{host}",
    },
    "Cliq": {
        "api_path": "/api/v2",
        "required_scopes": ["ZohoCliq.channels.ALL"],
        "api_version": "v2",
        "category": "Collaboration",
        "custom_domain": "cliq.{host}",
    },
    "Meeting": {
        "api_path": "/api/v2",
        "required_scopes": ["ZohoMeeting.meeting.ALL"],
        "api_version": "v2",
        "category": "Collaboration",
        "custom_domain": "meeting.{host}",
    },
    "Calendar": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoCalendar.calendar.ALL"],
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
    },
    "WorkDrive": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoWorkDrive.files.ALL"],
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
    },
    "Sheet": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoSheet.spreadsheets.ALL"],
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
    },
    "Learn": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoLearn.courses.ALL"],
        "api_version": "v1",
        "category": "Productivity",
        "custom_domain": "learn.{host}",
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
    },
    "FSM": {
        "api_path": "/api/v1",
        "required_scopes": ["ZohoFSM.modules.ALL"],
        "api_version": "v1",
        "category": "Operations",
        "custom_domain": "fsm.{host}",
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
        "required_scopes": ["ZohoDirectory.users.ALL"],
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
    },
}
