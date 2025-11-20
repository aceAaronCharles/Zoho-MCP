"""
Zoho API Router
Routes API requests to appropriate Zoho application endpoints.
"""

import requests
import logging
from typing import Dict, Any, Optional
from app_registry import AppRegistry, ZohoAppConfig
from zoho_auth import ZohoAuth

logger = logging.getLogger(__name__)


class APIRouter:
    """Routes API requests to appropriate Zoho app endpoints."""
    
    def __init__(self, auth: ZohoAuth, registry: AppRegistry):
        """
        Initialize router with auth and app registry.
        
        Args:
            auth: ZohoAuth instance for authentication
            registry: AppRegistry instance for app configurations
        """
        self.auth = auth
        self.registry = registry
        self.timeout = 30  # Default timeout in seconds
    
    def make_request(
        self,
        app_name: str,
        endpoint: str,
        method: str = 'GET',
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        additional_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated API request to any Zoho app.
        
        Args:
            app_name: Name of the Zoho app (e.g., "CRM", "Books")
            endpoint: API endpoint path (e.g., "Leads", "invoices")
            method: HTTP method (GET, POST, PUT, DELETE)
            data: Request body data
            params: Query parameters
            additional_path: Additional path segments (e.g., organization_id for Books)
        
        Returns:
            Standardized response dictionary
        """
        # Check if app is enabled
        if not self.registry.is_app_enabled(app_name):
            return self._handle_error(
                "app_disabled",
                {
                    "app_name": app_name,
                    "message": f"The {app_name} app is not enabled. Check your OAuth scopes."
                }
            )
        
        # Get app configuration
        app_config = self.registry.get_app_config(app_name)
        if not app_config:
            return self._handle_error(
                "app_not_found",
                {
                    "app_name": app_name,
                    "message": f"App '{app_name}' not found in registry."
                }
            )
        
        # Build URL
        try:
            url = self._build_url(app_config, endpoint, additional_path)
        except Exception as e:
            return self._handle_error(
                "url_build_error",
                {
                    "app_name": app_name,
                    "error": str(e)
                }
            )
        
        # Get authentication headers
        try:
            headers = self.auth.get_headers()
        except Exception as e:
            return self._handle_error(
                "authentication",
                {
                    "message": "Failed to get authentication headers",
                    "error": str(e)
                }
            )
        
        # Make the request
        try:
            response = self._execute_request(method, url, headers, data, params)
            return self._handle_response(response, app_name)
        except requests.exceptions.Timeout:
            return self._handle_error(
                "timeout",
                {
                    "app_name": app_name,
                    "message": f"Request to {app_name} timed out after {self.timeout} seconds"
                }
            )
        except requests.exceptions.RequestException as e:
            return self._handle_error(
                "network",
                {
                    "app_name": app_name,
                    "message": f"Network error occurred: {str(e)}",
                    "error": str(e)
                }
            )
        except Exception as e:
            return self._handle_error(
                "unexpected",
                {
                    "app_name": app_name,
                    "message": f"Unexpected error: {str(e)}",
                    "error": str(e)
                }
            )
    
    def _build_url(
        self,
        app_config: ZohoAppConfig,
        endpoint: str,
        additional_path: Optional[str]
    ) -> str:
        """
        Build complete API URL.
        
        Args:
            app_config: App configuration
            endpoint: API endpoint
            additional_path: Additional path segments
        
        Returns:
            Complete URL string
        """
        api_domain = self.auth.get_api_domain()
        
        # Remove leading slash from endpoint if present
        endpoint = endpoint.lstrip('/')
        
        # Build base URL
        if additional_path:
            # For apps that need additional path (like Books with organization_id)
            additional_path = additional_path.lstrip('/')
            url = f"{api_domain}{app_config.api_path}/{additional_path}/{endpoint}"
        else:
            url = f"{api_domain}{app_config.api_path}/{endpoint}"
        
        logger.debug(f"Built URL: {url}")
        return url
    
    def _execute_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict],
        params: Optional[Dict]
    ) -> requests.Response:
        """
        Execute HTTP request.
        
        Args:
            method: HTTP method
            url: Complete URL
            headers: Request headers
            data: Request body
            params: Query parameters
        
        Returns:
            Response object
        """
        logger.debug(f"Making {method} request to {url}")
        
        if method == 'GET':
            return requests.get(url, headers=headers, params=params, timeout=self.timeout)
        elif method == 'POST':
            return requests.post(url, headers=headers, json=data, params=params, timeout=self.timeout)
        elif method == 'PUT':
            return requests.put(url, headers=headers, json=data, params=params, timeout=self.timeout)
        elif method == 'DELETE':
            return requests.delete(url, headers=headers, params=params, timeout=self.timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    def _handle_response(self, response: requests.Response, app_name: str) -> Dict[str, Any]:
        """
        Standardize response format across all apps.
        
        Args:
            response: HTTP response object
            app_name: Name of the Zoho app
        
        Returns:
            Standardized response dictionary
        """
        status_code = response.status_code
        
        # Success responses
        if status_code in [200, 201, 202, 204]:
            try:
                # Handle empty responses (like DELETE operations)
                if status_code == 204 or not response.content:
                    return {
                        'status': 'success',
                        'status_code': status_code,
                        'app': app_name,
                        'data': {},
                        'message': 'Operation completed successfully'
                    }
                
                data = response.json()
                return {
                    'status': 'success',
                    'status_code': status_code,
                    'app': app_name,
                    'data': data
                }
            except ValueError:
                # Response is not JSON
                return {
                    'status': 'success',
                    'status_code': status_code,
                    'app': app_name,
                    'data': {'text': response.text}
                }
        
        # Error responses
        error_data = {
            'status_code': status_code,
            'app': app_name
        }
        
        # Try to parse error response
        try:
            error_json = response.json()
            error_data['error'] = error_json
            error_data['message'] = self._extract_error_message(error_json)
        except ValueError:
            error_data['error'] = response.text
            error_data['message'] = response.text or f"HTTP {status_code} error"
        
        # Categorize error type
        if status_code == 401:
            error_data['error_type'] = 'authentication'
        elif status_code == 403:
            error_data['error_type'] = 'authorization'
        elif status_code == 404:
            error_data['error_type'] = 'not_found'
        elif status_code == 429:
            error_data['error_type'] = 'rate_limit'
            # Try to extract retry-after header
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                error_data['retry_after'] = int(retry_after)
        elif status_code >= 500:
            error_data['error_type'] = 'server_error'
        else:
            error_data['error_type'] = 'api_error'
        
        error_data['status'] = 'error'
        return error_data
    
    def _extract_error_message(self, error_json: Any) -> str:
        """
        Extract error message from various Zoho API error formats.
        
        Args:
            error_json: Error response JSON
        
        Returns:
            Error message string
        """
        # Different Zoho apps have different error formats
        if isinstance(error_json, dict):
            # Common patterns
            if 'message' in error_json:
                return error_json['message']
            if 'error' in error_json:
                error = error_json['error']
                if isinstance(error, str):
                    return error
                if isinstance(error, dict) and 'message' in error:
                    return error['message']
            if 'errors' in error_json and isinstance(error_json['errors'], list):
                if error_json['errors']:
                    first_error = error_json['errors'][0]
                    if isinstance(first_error, dict) and 'message' in first_error:
                        return first_error['message']
            if 'data' in error_json:
                data = error_json['data']
                if isinstance(data, list) and data:
                    first_item = data[0]
                    if isinstance(first_item, dict) and 'message' in first_item:
                        return first_item['message']
        
        return str(error_json)
    
    def _handle_error(self, error_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Centralized error handling.
        
        Args:
            error_type: Type of error
            details: Error details
        
        Returns:
            Standardized error response
        """
        error_messages = {
            "app_disabled": "The requested Zoho app is not enabled. Check your OAuth scopes in .env file.",
            "app_not_found": "The requested Zoho app was not found in the registry.",
            "authentication": "Authentication failed. Please re-authenticate with Zoho.",
            "authorization": "Insufficient permissions for this operation. Check your OAuth scopes.",
            "rate_limit": "Rate limit exceeded. Please retry after the specified time.",
            "network": "Network error occurred. Please check your connection.",
            "timeout": "Request timed out. The server took too long to respond.",
            "api_error": "Zoho API returned an error.",
            "url_build_error": "Failed to build API URL.",
            "unexpected": "An unexpected error occurred."
        }
        
        base_message = error_messages.get(error_type, "Unknown error")
        
        response = {
            "status": "error",
            "error_type": error_type,
            "message": details.get('message', base_message),
            "details": details
        }
        
        # Add retry_after if present
        if 'retry_after' in details:
            response['retry_after'] = details['retry_after']
        
        logger.error(f"Error ({error_type}): {response['message']}")
        
        return response
    
    def set_timeout(self, timeout: int):
        """
        Set request timeout.
        
        Args:
            timeout: Timeout in seconds
        """
        self.timeout = timeout
        logger.info(f"Request timeout set to {timeout} seconds")
