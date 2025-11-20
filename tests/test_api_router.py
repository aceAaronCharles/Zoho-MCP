"""
Unit tests for API Router
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import requests
from src.api_router import APIRouter
from src.app_registry import AppRegistry, ZohoAppConfig
from src.zoho_auth import ZohoAuth


class TestAPIRouter:
    """Test cases for APIRouter class."""
    
    @pytest.fixture
    def mock_auth(self):
        """Create mock ZohoAuth instance."""
        auth = Mock(spec=ZohoAuth)
        auth.get_headers.return_value = {
            'Authorization': 'Zoho-oauthtoken test_token',
            'Content-Type': 'application/json'
        }
        auth.get_api_domain.return_value = 'https://www.zohoapis.com'
        return auth
    
    @pytest.fixture
    def registry_with_crm(self):
        """Create registry with CRM enabled."""
        return AppRegistry("ZohoCRM.modules.ALL")
    
    @pytest.fixture
    def registry_with_books(self):
        """Create registry with Books enabled."""
        return AppRegistry("ZohoBooks.fullaccess.all")
    
    @pytest.fixture
    def router_crm(self, mock_auth, registry_with_crm):
        """Create router with CRM enabled."""
        return APIRouter(mock_auth, registry_with_crm)
    
    @pytest.fixture
    def router_books(self, mock_auth, registry_with_books):
        """Create router with Books enabled."""
        return APIRouter(mock_auth, registry_with_books)
    
    def test_initialization(self, mock_auth, registry_with_crm):
        """Test router initialization."""
        router = APIRouter(mock_auth, registry_with_crm)
        assert router.auth == mock_auth
        assert router.registry == registry_with_crm
        assert router.timeout == 30
    
    def test_build_url_simple(self, router_crm):
        """Test URL building for simple endpoint."""
        app_config = router_crm.registry.get_app_config("CRM")
        url = router_crm._build_url(app_config, "Leads", None)
        
        assert url == "https://www.zohoapis.com/crm/v2/Leads"
    
    def test_build_url_with_additional_path(self, router_books):
        """Test URL building with additional path (like organization_id)."""
        app_config = router_books.registry.get_app_config("Books")
        url = router_books._build_url(app_config, "invoices", "organization/123456")
        
        assert url == "https://www.zohoapis.com/books/v3/organization/123456/invoices"
    
    def test_build_url_strips_leading_slashes(self, router_crm):
        """Test URL building strips leading slashes."""
        app_config = router_crm.registry.get_app_config("CRM")
        url = router_crm._build_url(app_config, "/Leads", None)
        
        assert url == "https://www.zohoapis.com/crm/v2/Leads"
        assert "//" not in url.replace("https://", "")
    
    def test_request_disabled_app(self, router_crm):
        """Test making request to disabled app."""
        result = router_crm.make_request("Books", "invoices")
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'app_disabled'
        assert 'Books' in result['message']
    
    def test_request_nonexistent_app(self, router_crm):
        """Test making request to non-existent app."""
        result = router_crm.make_request("NonExistentApp", "endpoint")
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'app_not_found'
    
    @patch('src.api_router.requests.get')
    def test_successful_get_request(self, mock_get, router_crm):
        """Test successful GET request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'id': '123', 'name': 'Test Lead'}]}
        mock_get.return_value = mock_response
        
        result = router_crm.make_request("CRM", "Leads", method="GET")
        
        assert result['status'] == 'success'
        assert result['status_code'] == 200
        assert result['app'] == 'CRM'
        assert 'data' in result
        assert result['data']['data'][0]['id'] == '123'
    
    @patch('src.api_router.requests.post')
    def test_successful_post_request(self, mock_post, router_crm):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'data': [{'id': '456', 'status': 'created'}]}
        mock_post.return_value = mock_response
        
        data = {'First_Name': 'John', 'Last_Name': 'Doe'}
        result = router_crm.make_request("CRM", "Leads", method="POST", data=data)
        
        assert result['status'] == 'success'
        assert result['status_code'] == 201
        assert result['app'] == 'CRM'
    
    @patch('src.api_router.requests.get')
    def test_authentication_error(self, mock_get, router_crm):
        """Test handling of authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'Invalid authentication'}
        mock_get.return_value = mock_response
        
        result = router_crm.make_request("CRM", "Leads")
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'authentication'
        assert result['status_code'] == 401
    
    @patch('src.api_router.requests.get')
    def test_authorization_error(self, mock_get, router_crm):
        """Test handling of authorization error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {'error': 'Insufficient permissions'}
        mock_get.return_value = mock_response
        
        result = router_crm.make_request("CRM", "Leads")
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'authorization'
        assert result['status_code'] == 403
    
    @patch('src.api_router.requests.get')
    def test_rate_limit_error(self, mock_get, router_crm):
        """Test handling of rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_response.json.return_value = {'error': 'Rate limit exceeded'}
        mock_get.return_value = mock_response
        
        result = router_crm.make_request("CRM", "Leads")
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'rate_limit'
        assert result['retry_after'] == 60
    
    @patch('src.api_router.requests.get')
    def test_timeout_error(self, mock_get, router_crm):
        """Test handling of timeout error."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = router_crm.make_request("CRM", "Leads")
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'timeout'
    
    @patch('src.api_router.requests.get')
    def test_network_error(self, mock_get, router_crm):
        """Test handling of network error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        result = router_crm.make_request("CRM", "Leads")
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'network'
    
    def test_extract_error_message_simple(self, router_crm):
        """Test extracting error message from simple format."""
        error_json = {'message': 'Test error message'}
        message = router_crm._extract_error_message(error_json)
        assert message == 'Test error message'
    
    def test_extract_error_message_nested(self, router_crm):
        """Test extracting error message from nested format."""
        error_json = {'error': {'message': 'Nested error message'}}
        message = router_crm._extract_error_message(error_json)
        assert message == 'Nested error message'
    
    def test_extract_error_message_array(self, router_crm):
        """Test extracting error message from array format."""
        error_json = {'errors': [{'message': 'First error'}]}
        message = router_crm._extract_error_message(error_json)
        assert message == 'First error'
    
    def test_set_timeout(self, router_crm):
        """Test setting custom timeout."""
        router_crm.set_timeout(60)
        assert router_crm.timeout == 60
    
    @patch('src.api_router.requests.delete')
    def test_delete_request(self, mock_delete, router_crm):
        """Test DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b''
        mock_delete.return_value = mock_response
        
        result = router_crm.make_request("CRM", "Leads/123", method="DELETE")
        
        assert result['status'] == 'success'
        assert result['status_code'] == 204
    
    @patch('src.api_router.requests.put')
    def test_put_request(self, mock_put, router_crm):
        """Test PUT request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'id': '123', 'status': 'updated'}]}
        mock_put.return_value = mock_response
        
        data = {'First_Name': 'Jane'}
        result = router_crm.make_request("CRM", "Leads/123", method="PUT", data=data)
        
        assert result['status'] == 'success'
        assert result['status_code'] == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
