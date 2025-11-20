"""
Unit tests for Zoho Desk Tools
"""

import pytest
from unittest.mock import Mock
from src.app_registry import AppRegistry
from src.api_router import APIRouter
from src.apps.desk_tools import register_desk_tools


class TestDeskTools:
    """Test cases for Zoho Desk tools."""
    
    @pytest.fixture
    def mock_router(self):
        """Create mock API router."""
        router = Mock(spec=APIRouter)
        return router
    
    @pytest.fixture
    def registry_with_desk(self):
        """Create registry with Desk enabled."""
        return AppRegistry("Desk.tickets.ALL")
    
    def test_desk_get_tickets_call(self, mock_router):
        """Test desk_get_tickets makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("Desk.tickets.ALL")
        
        register_desk_tools(mock_mcp, mock_router, registry)
        
        if 'desk_get_tickets' in registered_tools:
            desk_get_tickets = registered_tools['desk_get_tickets']
            desk_get_tickets(None, status="Open", page=1, per_page=50)
            
            call_args = mock_router.make_request.call_args
            assert call_args[1]['app_name'] == "Desk"
            assert call_args[1]['endpoint'] == "tickets"
            assert call_args[1]['params']['status'] == "Open"
            assert call_args[1]['params']['limit'] == 50
    
    def test_desk_create_ticket_call(self, mock_router):
        """Test desk_create_ticket makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("Desk.tickets.ALL")
        
        register_desk_tools(mock_mcp, mock_router, registry)
        
        if 'desk_create_ticket' in registered_tools:
            desk_create_ticket = registered_tools['desk_create_ticket']
            ticket_data = {'subject': 'Test Ticket', 'description': 'Test description'}
            desk_create_ticket(None, ticket_data=ticket_data)
            
            call_args = mock_router.make_request.call_args
            assert call_args[1]['app_name'] == "Desk"
            assert call_args[1]['method'] == "POST"
            assert call_args[1]['data'] == ticket_data
    
    def test_desk_add_comment_call(self, mock_router):
        """Test desk_add_comment makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("Desk.tickets.ALL")
        
        register_desk_tools(mock_mcp, mock_router, registry)
        
        if 'desk_add_comment' in registered_tools:
            desk_add_comment = registered_tools['desk_add_comment']
            desk_add_comment(None, ticket_id="12345", comment="Test comment", is_public=True)
            
            call_args = mock_router.make_request.call_args
            assert call_args[1]['app_name'] == "Desk"
            assert "comments" in call_args[1]['endpoint']
            assert call_args[1]['data']['content'] == "Test comment"
            assert call_args[1]['data']['isPublic'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
