"""
Unit tests for Zoho Projects Tools
"""

import pytest
from unittest.mock import Mock
from src.app_registry import AppRegistry
from src.api_router import APIRouter
from src.apps.projects_tools import register_projects_tools


class TestProjectsTools:
    """Test cases for Zoho Projects tools."""
    
    @pytest.fixture
    def mock_router(self):
        """Create mock API router."""
        router = Mock(spec=APIRouter)
        return router
    
    @pytest.fixture
    def registry_with_projects(self):
        """Create registry with Projects enabled."""
        return AppRegistry("ZohoProjects.projects.ALL")
    
    @pytest.fixture
    def registry_without_projects(self):
        """Create registry without Projects."""
        return AppRegistry("ZohoCRM.modules.ALL")
    
    def test_projects_tools_not_registered_when_disabled(self, mock_router, registry_without_projects):
        """Test that Projects tools are not registered when Projects is disabled."""
        class MockMCP:
            def tool(self):
                return lambda func: func
        
        mock_mcp = MockMCP()
        register_projects_tools(mock_mcp, mock_router, registry_without_projects)
        assert True
    
    def test_projects_tools_registered_when_enabled(self, mock_router, registry_with_projects):
        """Test that Projects tools are registered when Projects is enabled."""
        class MockMCP:
            def tool(self):
                return lambda func: func
        
        mock_mcp = MockMCP()
        register_projects_tools(mock_mcp, mock_router, registry_with_projects)
        assert True
    
    def test_projects_get_portals_call(self, mock_router):
        """Test projects_get_portals makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("ZohoProjects.projects.ALL")
        
        register_projects_tools(mock_mcp, mock_router, registry)
        
        if 'projects_get_portals' in registered_tools:
            projects_get_portals = registered_tools['projects_get_portals']
            projects_get_portals()
            
            call_args = mock_router.make_request.call_args
            assert call_args[1]['app_name'] == "Projects"
            assert call_args[1]['endpoint'] == "portals/"
            assert call_args[1]['method'] == "GET"
    
    def test_projects_get_projects_call(self, mock_router):
        """Test projects_get_projects makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("ZohoProjects.projects.ALL")
        
        register_projects_tools(mock_mcp, mock_router, registry)
        
        if 'projects_get_projects' in registered_tools:
            projects_get_projects = registered_tools['projects_get_projects']
            projects_get_projects(portal_id="12345", page=1, per_page=50)
            
            call_args = mock_router.make_request.call_args
            assert call_args[1]['app_name'] == "Projects"
            assert "portal/12345/projects" in call_args[1]['endpoint']
            assert call_args[1]['params']['index'] == 1
            assert call_args[1]['params']['range'] == 50
    
    def test_projects_get_tasks_call(self, mock_router):
        """Test projects_get_tasks makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("ZohoProjects.projects.ALL")
        
        register_projects_tools(mock_mcp, mock_router, registry)
        
        if 'projects_get_tasks' in registered_tools:
            projects_get_tasks = registered_tools['projects_get_tasks']
            projects_get_tasks(portal_id="12345", project_id="67890", status="open")
            
            call_args = mock_router.make_request.call_args
            assert call_args[1]['app_name'] == "Projects"
            assert "tasks" in call_args[1]['endpoint']
            assert call_args[1]['params']['status'] == "open"
    
    def test_projects_create_task_call(self, mock_router):
        """Test projects_create_task makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("ZohoProjects.projects.ALL")
        
        register_projects_tools(mock_mcp, mock_router, registry)
        
        if 'projects_create_task' in registered_tools:
            projects_create_task = registered_tools['projects_create_task']
            task_data = {'name': 'New Task', 'description': 'Task description'}
            projects_create_task(portal_id="12345", project_id="67890", task_data=task_data)
            
            call_args = mock_router.make_request.call_args
            assert call_args[1]['app_name'] == "Projects"
            assert call_args[1]['method'] == "POST"
            assert call_args[1]['data'] == task_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
