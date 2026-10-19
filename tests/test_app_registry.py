"""
Unit tests for App Registry
"""

import pytest
from src.app_registry import AppRegistry


class TestAppRegistry:
    """Test cases for AppRegistry class."""
    
    def test_initialization_with_empty_scope(self):
        """Test registry initialization with empty scope string."""
        registry = AppRegistry("")
        assert len(registry.scopes) == 0
        assert len(registry.apps) > 0  # Apps should be registered but disabled
        enabled = registry.list_enabled_apps()
        assert len(enabled) == 0
    
    def test_initialization_with_crm_scope(self):
        """Test registry initialization with CRM scope."""
        scope = "ZohoCRM.modules.ALL"
        registry = AppRegistry(scope)
        
        assert registry.is_app_enabled("CRM")
        assert not registry.is_app_enabled("Books")
        
        enabled = registry.list_enabled_apps()
        assert len(enabled) == 1
        assert enabled[0].name == "CRM"
    
    def test_initialization_with_multiple_scopes(self):
        """Test registry initialization with multiple scopes."""
        scope = "ZohoCRM.modules.ALL,ZohoBooks.fullaccess.all,ZohoProjects.projects.ALL"
        registry = AppRegistry(scope)
        
        assert registry.is_app_enabled("CRM")
        assert registry.is_app_enabled("Books")
        assert registry.is_app_enabled("Projects")
        assert not registry.is_app_enabled("Desk")
        
        enabled = registry.list_enabled_apps()
        assert len(enabled) == 3
    
    def test_get_app_config(self):
        """Test getting app configuration."""
        scope = "ZohoCRM.modules.ALL"
        registry = AppRegistry(scope)
        
        crm_config = registry.get_app_config("CRM")
        assert crm_config is not None
        assert crm_config.name == "CRM"
        assert crm_config.api_path == "/crm/v2.1"
        assert crm_config.api_version == "v2.1"
        assert crm_config.category == "Sales"
        assert crm_config.enabled is True
        
        books_config = registry.get_app_config("Books")
        assert books_config is not None
        assert books_config.enabled is False
    
    def test_get_nonexistent_app(self):
        """Test getting configuration for non-existent app."""
        registry = AppRegistry("")
        config = registry.get_app_config("NonExistentApp")
        assert config is None
    
    def test_list_all_apps(self):
        """Test listing all apps."""
        registry = AppRegistry("")
        all_apps = registry.list_all_apps()
        
        # Should have 40+ apps
        assert len(all_apps) >= 37
        
        # Check some expected apps
        app_names = [app.name for app in all_apps]
        assert "CRM" in app_names
        assert "Books" in app_names
        assert "Projects" in app_names
        assert "Desk" in app_names
    
    def test_get_apps_by_category(self):
        """Test getting apps by category."""
        scope = "ZohoCRM.modules.ALL,SalesIQ.portals.ALL"
        registry = AppRegistry(scope)
        
        sales_apps = registry.get_apps_by_category("Sales")
        assert len(sales_apps) == 2
        assert all(app.category == "Sales" for app in sales_apps)
        
        finance_apps = registry.get_apps_by_category("Finance")
        assert len(finance_apps) > 0
        assert all(app.category == "Finance" for app in finance_apps)
    
    def test_get_enabled_categories(self):
        """Test getting enabled categories."""
        scope = "ZohoCRM.modules.ALL,ZohoBooks.fullaccess.all,ZohoPeople.forms.ALL"
        registry = AppRegistry(scope)
        
        categories = registry.get_enabled_categories()
        assert "Sales" in categories  # CRM
        assert "Finance" in categories  # Books
        assert "HR" in categories  # People
        assert "Marketing" not in categories  # No marketing apps enabled
    
    def test_scope_parsing(self):
        """Test scope string parsing."""
        scope = "ZohoCRM.modules.ALL, ZohoBooks.fullaccess.all , ZohoProjects.projects.ALL"
        registry = AppRegistry(scope)
        
        # Should handle spaces correctly
        assert len(registry.scopes) == 3
        assert registry.is_app_enabled("CRM")
        assert registry.is_app_enabled("Books")
        assert registry.is_app_enabled("Projects")

    def test_space_delimited_scopes(self):
        """Zoho returns token scopes separated by spaces, not commas."""
        scope = "ZohoCRM.modules.ALL ZohoBooks.fullaccess.all Desk.tickets.ALL"
        registry = AppRegistry(scope)

        assert len(registry.scopes) == 3
        assert registry.is_app_enabled("CRM")
        assert registry.is_app_enabled("Books")
        assert registry.is_app_enabled("Desk")
    
    def test_partial_scope_matching(self):
        """Test partial scope matching for flexibility."""
        # Some apps might have multiple scope variations
        scope = "ZohoCreator.report.READ,ZohoCreator.report.CREATE"
        registry = AppRegistry(scope)
        
        # Creator should be enabled with any Creator scope
        assert registry.is_app_enabled("Creator")

    def test_missing_scopes(self):
        """Report the scopes a grant still needs for each app."""
        registry = AppRegistry("ZohoCRM.modules.ALL")

        assert registry.missing_scopes("CRM") == []
        assert registry.missing_scopes("Vault") == ["ZohoVault.secrets.ALL"]
        assert registry.missing_scopes("NonExistentApp") == []

    def test_scope_report(self):
        """The scope report includes per-app coverage."""
        registry = AppRegistry("ZohoCRM.modules.ALL")
        report = registry.scope_report()

        assert report["granted_scopes"] == ["ZohoCRM.modules.ALL"]
        assert report["apps"]["CRM"]["enabled"] is True
        assert report["apps"]["Vault"]["enabled"] is False
        assert report["apps"]["Vault"]["missing_scopes"] == [
            "ZohoVault.secrets.ALL"
        ]
    
    def test_app_config_to_dict(self):
        """Test converting app config to dictionary."""
        scope = "ZohoCRM.modules.ALL"
        registry = AppRegistry(scope)
        
        crm_config = registry.get_app_config("CRM")
        config_dict = crm_config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['name'] == "CRM"
        assert config_dict['api_path'] == "/crm/v2.1"
        assert config_dict['enabled'] is True
        assert config_dict['api_version'] == "v2.1"
        assert config_dict['category'] == "Sales"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
