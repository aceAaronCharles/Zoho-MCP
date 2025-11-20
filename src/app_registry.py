"""
Zoho App Registry
Manages configuration and availability of Zoho applications based on OAuth scopes.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ZohoAppConfig:
    """Configuration for a Zoho application."""
    name: str
    api_path: str
    required_scopes: List[str]
    enabled: bool
    api_version: str
    category: str
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "api_path": self.api_path,
            "enabled": self.enabled,
            "api_version": self.api_version,
            "category": self.category
        }


# Complete configuration for all 40+ Zoho applications
APP_CONFIGS = {
    # Sales & Marketing
    "CRM": {
        "api_path": "/crm/v2",
        "required_scopes": ["ZohoCRM.modules.ALL"],
        "api_version": "v2",
        "category": "Sales"
    },
    "SalesIQ": {
        "api_path": "/salesiq/v2",
        "required_scopes": ["ZohoSalesIQ.modules.ALL"],
        "api_version": "v2",
        "category": "Sales"
    },
    "Campaigns": {
        "api_path": "/campaigns/v2",
        "required_scopes": ["ZohoCampaigns.campaign.ALL"],
        "api_version": "v2",
        "category": "Marketing"
    },
    "Social": {
        "api_path": "/social/v2",
        "required_scopes": ["ZohoSocial.data.ALL"],
        "api_version": "v2",
        "category": "Marketing"
    },
    "Forms": {
        "api_path": "/forms/v2",
        "required_scopes": ["ZohoForms.form.ALL"],
        "api_version": "v2",
        "category": "Marketing"
    },
    "Survey": {
        "api_path": "/survey/v2",
        "required_scopes": ["ZohoSurvey.surveys.ALL"],
        "api_version": "v2",
        "category": "Marketing"
    },
    
    # Finance & Commerce
    "Books": {
        "api_path": "/books/v3",
        "required_scopes": ["ZohoBooks.fullaccess.all"],
        "api_version": "v3",
        "category": "Finance"
    },
    "Invoice": {
        "api_path": "/invoice/v3",
        "required_scopes": ["ZohoInvoice.fullaccess.all"],
        "api_version": "v3",
        "category": "Finance"
    },
    "Expense": {
        "api_path": "/expense/v1",
        "required_scopes": ["ZohoExpense.fullaccess.all"],
        "api_version": "v1",
        "category": "Finance"
    },
    "Inventory": {
        "api_path": "/inventory/v1",
        "required_scopes": ["ZohoInventory.fullaccess.all"],
        "api_version": "v1",
        "category": "Finance"
    },
    "Subscriptions": {
        "api_path": "/subscriptions/v1",
        "required_scopes": ["ZohoSubscriptions.fullaccess.all"],
        "api_version": "v1",
        "category": "Finance"
    },
    "Commerce": {
        "api_path": "/commerce/v1",
        "required_scopes": ["ZohoCommerce.fullaccess.all"],
        "api_version": "v1",
        "category": "Commerce"
    },
    
    # Customer Service
    "Desk": {
        "api_path": "/desk/v1",
        "required_scopes": ["Desk.tickets.ALL"],
        "api_version": "v1",
        "category": "Service"
    },
    "Assist": {
        "api_path": "/assist/v2",
        "required_scopes": ["ZohoAssist.session.ALL"],
        "api_version": "v2",
        "category": "Service"
    },
    
    # HR & Recruitment
    "People": {
        "api_path": "/people/api",
        "required_scopes": ["ZohoPeople.forms.ALL"],
        "api_version": "api",
        "category": "HR"
    },
    "Recruit": {
        "api_path": "/recruit/v2",
        "required_scopes": ["ZohoRecruit.modules.ALL"],
        "api_version": "v2",
        "category": "HR"
    },
    
    # Project Management & Collaboration
    "Projects": {
        "api_path": "/projects/v3",
        "required_scopes": ["ZohoProjects.projects.ALL"],
        "api_version": "v3",
        "category": "Projects"
    },
    "Sprints": {
        "api_path": "/sprints/v2",
        "required_scopes": ["ZohoSprints.projects.ALL"],
        "api_version": "v2",
        "category": "Projects"
    },
    "BugTracker": {
        "api_path": "/bugtracker/v2",
        "required_scopes": ["ZohoBugTracker.projects.ALL"],
        "api_version": "v2",
        "category": "Projects"
    },
    "Connect": {
        "api_path": "/connect/v2",
        "required_scopes": ["ZohoConnect.network.ALL"],
        "api_version": "v2",
        "category": "Collaboration"
    },
    "Cliq": {
        "api_path": "/cliq/v2",
        "required_scopes": ["ZohoCliq.channels.ALL"],
        "api_version": "v2",
        "category": "Collaboration"
    },
    "Meeting": {
        "api_path": "/meeting/v2",
        "required_scopes": ["ZohoMeeting.meeting.ALL"],
        "api_version": "v2",
        "category": "Collaboration"
    },
    
    # Email & Productivity
    "Mail": {
        "api_path": "/mail/v1",
        "required_scopes": ["ZohoMail.accounts.ALL"],
        "api_version": "v1",
        "category": "Email"
    },
    "WorkDrive": {
        "api_path": "/workdrive/api/v1",
        "required_scopes": ["ZohoWorkDrive.files.ALL"],
        "api_version": "v1",
        "category": "Storage"
    },
    "Writer": {
        "api_path": "/writer/api/v1",
        "required_scopes": ["ZohoWriter.documents.ALL"],
        "api_version": "v1",
        "category": "Productivity"
    },
    "Sheet": {
        "api_path": "/sheet/api/v1",
        "required_scopes": ["ZohoSheet.spreadsheets.ALL"],
        "api_version": "v1",
        "category": "Productivity"
    },
    "Show": {
        "api_path": "/show/api/v1",
        "required_scopes": ["ZohoShow.presentations.ALL"],
        "api_version": "v1",
        "category": "Productivity"
    },
    
    # Analytics & BI
    "Analytics": {
        "api_path": "/restapi/v2",
        "required_scopes": ["ZohoAnalytics.fullaccess.all"],
        "api_version": "v2",
        "category": "Analytics"
    },
    
    # Developer & Custom Apps
    "Creator": {
        "api_path": "/creator/v2",
        "required_scopes": ["ZohoCreator.report.READ"],
        "api_version": "v2",
        "category": "Developer"
    },
    "Flow": {
        "api_path": "/flow/v1",
        "required_scopes": ["ZohoFlow.flows.ALL"],
        "api_version": "v1",
        "category": "Developer"
    },
    "Catalyst": {
        "api_path": "/catalyst/v2",
        "required_scopes": ["ZohoCatalyst.projects.ALL"],
        "api_version": "v2",
        "category": "Developer"
    },
    
    # Operations & Field Service
    "Fleet": {
        "api_path": "/fleet/v1",
        "required_scopes": ["ZohoFleet.modules.ALL"],
        "api_version": "v1",
        "category": "Operations"
    },
    "FSM": {
        "api_path": "/fsm/v1",
        "required_scopes": ["ZohoFSM.modules.ALL"],
        "api_version": "v1",
        "category": "Operations"
    },
    
    # Legal & Compliance
    "Sign": {
        "api_path": "/sign/v1",
        "required_scopes": ["ZohoSign.documents.ALL"],
        "api_version": "v1",
        "category": "Legal"
    },
    "Contracts": {
        "api_path": "/contracts/v1",
        "required_scopes": ["ZohoContracts.contracts.ALL"],
        "api_version": "v1",
        "category": "Legal"
    },
    
    # IoT & Specialized
    "IoT": {
        "api_path": "/iot/v1",
        "required_scopes": ["ZohoIoT.devices.ALL"],
        "api_version": "v1",
        "category": "IoT"
    },
    "Bookings": {
        "api_path": "/bookings/v1",
        "required_scopes": ["ZohoBookings.bookings.ALL"],
        "api_version": "v1",
        "category": "Operations"
    }
}


class AppRegistry:
    """Registry of available Zoho applications."""
    
    def __init__(self, scope_string: str):
        """
        Initialize registry based on OAuth scopes.
        
        Args:
            scope_string: Comma-separated OAuth scope string
        """
        self.scope_string = scope_string
        self.scopes = self._parse_scopes(scope_string)
        self.apps: Dict[str, ZohoAppConfig] = {}
        self._initialize_apps()
        
        logger.info(f"App Registry initialized with {len(self.apps)} total apps")
        enabled_count = len([app for app in self.apps.values() if app.enabled])
        logger.info(f"Enabled apps: {enabled_count}/{len(self.apps)}")
    
    def _parse_scopes(self, scope_string: str) -> List[str]:
        """Parse scope string into list of individual scopes."""
        if not scope_string:
            return []
        return [scope.strip() for scope in scope_string.split(',') if scope.strip()]
    
    def _check_scopes_present(self, required_scopes: List[str]) -> bool:
        """Check if all required scopes are present in the OAuth scopes."""
        for required_scope in required_scopes:
            # Check for exact match or partial match (for flexibility)
            scope_found = False
            for user_scope in self.scopes:
                if required_scope in user_scope or user_scope in required_scope:
                    scope_found = True
                    break
            if not scope_found:
                return False
        return True
    
    def _initialize_apps(self):
        """Initialize all app configurations and determine enabled status."""
        for app_name, config in APP_CONFIGS.items():
            enabled = self._check_scopes_present(config["required_scopes"])
            
            self.apps[app_name] = ZohoAppConfig(
                name=app_name,
                api_path=config["api_path"],
                required_scopes=config["required_scopes"],
                enabled=enabled,
                api_version=config["api_version"],
                category=config["category"]
            )
            
            if enabled:
                logger.debug(f"App '{app_name}' enabled")
    
    def get_app_config(self, app_name: str) -> Optional[ZohoAppConfig]:
        """
        Get configuration for a specific app.
        
        Args:
            app_name: Name of the Zoho app
            
        Returns:
            ZohoAppConfig if app exists, None otherwise
        """
        return self.apps.get(app_name)
    
    def list_enabled_apps(self) -> List[ZohoAppConfig]:
        """
        List all enabled applications.
        
        Returns:
            List of enabled ZohoAppConfig objects
        """
        return [app for app in self.apps.values() if app.enabled]
    
    def list_all_apps(self) -> List[ZohoAppConfig]:
        """
        List all applications (enabled and disabled).
        
        Returns:
            List of all ZohoAppConfig objects
        """
        return list(self.apps.values())
    
    def is_app_enabled(self, app_name: str) -> bool:
        """
        Check if an app is enabled.
        
        Args:
            app_name: Name of the Zoho app
            
        Returns:
            True if app is enabled, False otherwise
        """
        app = self.apps.get(app_name)
        return app.enabled if app else False
    
    def get_apps_by_category(self, category: str) -> List[ZohoAppConfig]:
        """
        Get all apps in a specific category.
        
        Args:
            category: Category name (e.g., 'Sales', 'Finance', 'HR')
            
        Returns:
            List of ZohoAppConfig objects in the category
        """
        return [app for app in self.apps.values() if app.category == category]
    
    def get_enabled_categories(self) -> List[str]:
        """
        Get list of categories that have at least one enabled app.
        
        Returns:
            List of category names
        """
        categories = set()
        for app in self.apps.values():
            if app.enabled:
                categories.add(app.category)
        return sorted(list(categories))
