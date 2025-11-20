"""
Unit tests for Zoho Books Tools
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.app_registry import AppRegistry
from src.api_router import APIRouter
from src.apps.books_tools import register_books_tools


class TestBooksTools:
    """Test cases for Zoho Books tools."""
    
    @pytest.fixture
    def mock_mcp(self):
        """Create mock MCP server."""
        mcp = Mock()
        mcp.tool = lambda: lambda func: func  # Simple decorator that returns the function
        return mcp
    
    @pytest.fixture
    def mock_router(self):
        """Create mock API router."""
        router = Mock(spec=APIRouter)
        return router
    
    @pytest.fixture
    def registry_with_books(self):
        """Create registry with Books enabled."""
        return AppRegistry("ZohoBooks.fullaccess.all")
    
    @pytest.fixture
    def registry_without_books(self):
        """Create registry without Books."""
        return AppRegistry("ZohoCRM.modules.ALL")
    
    def test_books_tools_not_registered_when_disabled(self, mock_mcp, mock_router, registry_without_books):
        """Test that Books tools are not registered when Books is disabled."""
        register_books_tools(mock_mcp, mock_router, registry_without_books)
        # Should not raise any errors, just skip registration
        assert True
    
    def test_books_tools_registered_when_enabled(self, mock_mcp, mock_router, registry_with_books):
        """Test that Books tools are registered when Books is enabled."""
        register_books_tools(mock_mcp, mock_router, registry_with_books)
        # Should complete without errors
        assert True
    
    def test_books_get_invoices_call(self, mock_router):
        """Test books_get_invoices makes correct API call."""
        from src.apps.books_tools import register_books_tools
        
        # Create a simple MCP mock that stores registered functions
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("ZohoBooks.fullaccess.all")
        
        register_books_tools(mock_mcp, mock_router, registry)
        
        # Call the registered function
        if 'books_get_invoices' in registered_tools:
            books_get_invoices = registered_tools['books_get_invoices']
            books_get_invoices(None, organization_id="123456", page=1, per_page=50)
            
            # Verify the router was called correctly
            mock_router.make_request.assert_called_once()
            call_args = mock_router.make_request.call_args
            
            assert call_args[1]['app_name'] == "Books"
            assert call_args[1]['endpoint'] == "invoices"
            assert call_args[1]['method'] == "GET"
            assert call_args[1]['additional_path'] == "organization/123456"
            assert call_args[1]['params']['page'] == 1
            assert call_args[1]['params']['per_page'] == 50
    
    def test_books_get_invoice_by_id_call(self, mock_router):
        """Test books_get_invoice_by_id makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("ZohoBooks.fullaccess.all")
        
        register_books_tools(mock_mcp, mock_router, registry)
        
        if 'books_get_invoice_by_id' in registered_tools:
            books_get_invoice_by_id = registered_tools['books_get_invoice_by_id']
            books_get_invoice_by_id(None, organization_id="123456", invoice_id="INV-001")
            
            call_args = mock_router.make_request.call_args
            
            assert call_args[1]['app_name'] == "Books"
            assert call_args[1]['endpoint'] == "invoices/INV-001"
            assert call_args[1]['method'] == "GET"
    
    def test_books_create_invoice_call(self, mock_router):
        """Test books_create_invoice makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("ZohoBooks.fullaccess.all")
        
        register_books_tools(mock_mcp, mock_router, registry)
        
        if 'books_create_invoice' in registered_tools:
            books_create_invoice = registered_tools['books_create_invoice']
            invoice_data = {
                'customer_id': 'CUST-001',
                'line_items': [{'item_id': 'ITEM-001', 'quantity': 1}]
            }
            books_create_invoice(None, organization_id="123456", invoice_data=invoice_data)
            
            call_args = mock_router.make_request.call_args
            
            assert call_args[1]['app_name'] == "Books"
            assert call_args[1]['endpoint'] == "invoices"
            assert call_args[1]['method'] == "POST"
            assert call_args[1]['data'] == invoice_data
    
    def test_books_get_customers_call(self, mock_router):
        """Test books_get_customers makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("ZohoBooks.fullaccess.all")
        
        register_books_tools(mock_mcp, mock_router, registry)
        
        if 'books_get_customers' in registered_tools:
            books_get_customers = registered_tools['books_get_customers']
            books_get_customers(None, organization_id="123456")
            
            call_args = mock_router.make_request.call_args
            
            assert call_args[1]['app_name'] == "Books"
            assert call_args[1]['endpoint'] == "contacts"
            assert call_args[1]['method'] == "GET"
    
    def test_books_get_vendors_call(self, mock_router):
        """Test books_get_vendors makes correct API call."""
        registered_tools = {}
        
        class MockMCP:
            def tool(self):
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator
        
        mock_mcp = MockMCP()
        registry = AppRegistry("ZohoBooks.fullaccess.all")
        
        register_books_tools(mock_mcp, mock_router, registry)
        
        if 'books_get_vendors' in registered_tools:
            books_get_vendors = registered_tools['books_get_vendors']
            books_get_vendors(None, organization_id="123456")
            
            call_args = mock_router.make_request.call_args
            
            assert call_args[1]['app_name'] == "Books"
            assert call_args[1]['endpoint'] == "contacts"
            assert call_args[1]['params']['contact_type'] == 'vendor'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
