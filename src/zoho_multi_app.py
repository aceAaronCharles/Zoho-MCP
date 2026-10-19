"""
Zoho Multi-Application API Handler
Handles API requests to multiple Zoho products (CRM, Books, Projects, Desk, etc.)
"""

import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ZohoMultiApp:
    """Handler for multiple Zoho application APIs."""
    
    # API base URLs for different Zoho products
    API_BASES = {
        'crm': '/crm/v2',
        'books': '/books/v3',
        'projects': '/restapi',
        'desk': '/api/v1',
        'people': '/people/api',
        'recruit': '/recruit/v2',
        'inventory': '/inventory/v1',
        'analytics': '/restapi/v2',
        'creator': '/api/v2',
        'mail': '/api/accounts',
        'meeting': '/meeting/v1/api',
        'campaigns': '/campaigns/v1'
    }
    
    # Different domain patterns for Zoho products
    DOMAIN_PATTERNS = {
        'crm': '{base_domain}',  # e.g., https://www.zohoapis.com
        'books': 'https://books.zoho.com',
        'projects': 'https://projectsapi.zoho.com',
        'desk': 'https://desk.zoho.com',
        'people': 'https://people.zoho.com',
        'recruit': '{base_domain}',
        'inventory': 'https://inventory.zoho.com',
        'analytics': 'https://analyticsapi.zoho.com',
        'creator': 'https://creator.zoho.com',
        'mail': 'https://mail.zoho.com',
        'meeting': 'https://meeting.zoho.com',
        'campaigns': 'https://campaigns.zoho.com'
    }
    
    def __init__(self, auth_handler, base_domain: str = 'https://www.zohoapis.com'):
        """
        Initialize multi-app handler.
        
        Args:
            auth_handler: ZohoAuth instance for authentication
            base_domain: Base API domain (changes based on data center)
        """
        self.auth = auth_handler
        self.base_domain = base_domain
        
    def get_api_url(self, app: str, endpoint: str, organization_id: Optional[str] = None) -> str:
        """
        Construct API URL for a specific Zoho app.
        
        Args:
            app: Zoho application name (crm, books, projects, etc.)
            endpoint: API endpoint path
            organization_id: Required for some apps like Books
            
        Returns:
            Complete API URL
        """
        app = app.lower()
        
        if app not in self.API_BASES:
            raise ValueError(f"Unsupported Zoho app: {app}. Supported: {list(self.API_BASES.keys())}")
        
        # Get domain pattern
        domain_pattern = self.DOMAIN_PATTERNS.get(app, '{base_domain}')
        domain = domain_pattern.format(base_domain=self.base_domain)
        
        # Get API base path
        api_base = self.API_BASES[app]
        
        # Clean endpoint
        endpoint = endpoint.lstrip('/')
        
        # Construct URL
        if organization_id and app in ['books', 'inventory']:
            return f"{domain}{api_base}/{endpoint}?organization_id={organization_id}"
        else:
            return f"{domain}{api_base}/{endpoint}"
    
    def make_request(
        self,
        app: str,
        endpoint: str,
        method: str = 'GET',
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        organization_id: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make authenticated API request to any Zoho application.
        
        Args:
            app: Zoho application (crm, books, projects, etc.)
            endpoint: API endpoint
            method: HTTP method (GET, POST, PUT, DELETE)
            data: Request body data
            params: Query parameters
            organization_id: Required for Books, Inventory
            timeout: Request timeout in seconds
            
        Returns:
            Response data dictionary
        """
        try:
            # Get headers from auth handler
            headers = self.auth.get_headers()
            
            # Construct URL
            url = self.get_api_url(app, endpoint, organization_id)
            
            logger.info(f"{method} request to {app}: {url}")
            
            # Make request
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, params=params, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, params=params, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle response
            if response.status_code in [200, 201, 202, 204]:
                try:
                    return {
                        'status': 'success',
                        'status_code': response.status_code,
                        'data': response.json() if response.text else {}
                    }
                except ValueError:
                    return {
                        'status': 'success',
                        'status_code': response.status_code,
                        'data': {'message': 'Success'}
                    }
            else:
                return {
                    'status': 'error',
                    'status_code': response.status_code,
                    'message': response.text,
                    'error': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
        
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'message': 'Request timed out',
                'error': 'timeout'
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'message': f'Request failed: {str(e)}',
                'error': str(e)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}',
                'error': str(e)
            }
    
    # ============================================================================
    # CRM METHODS
    # ============================================================================
    
    def crm_get_modules(self) -> Dict[str, Any]:
        """Get all CRM modules."""
        return self.make_request('crm', 'settings/modules')
    
    def crm_get_records(self, module: str, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get records from a CRM module."""
        params = {'page': page, 'per_page': per_page}
        return self.make_request('crm', module, params=params)
    
    def crm_create_record(self, module: str, record_data: Dict) -> Dict[str, Any]:
        """Create a CRM record."""
        return self.make_request('crm', module, method='POST', data={'data': [record_data]})
    
    # ============================================================================
    # BOOKS (ACCOUNTING) METHODS
    # ============================================================================
    
    def books_get_organizations(self) -> Dict[str, Any]:
        """Get Zoho Books organizations."""
        return self.make_request('books', 'organizations')
    
    def books_get_invoices(self, organization_id: str, page: int = 1) -> Dict[str, Any]:
        """Get invoices from Books."""
        params = {'page': page}
        return self.make_request('books', 'invoices', params=params, organization_id=organization_id)
    
    def books_get_customers(self, organization_id: str) -> Dict[str, Any]:
        """Get customers from Books."""
        return self.make_request('books', 'contacts', organization_id=organization_id)
    
    def books_create_invoice(self, organization_id: str, invoice_data: Dict) -> Dict[str, Any]:
        """Create an invoice in Books."""
        return self.make_request('books', 'invoices', method='POST', data=invoice_data, organization_id=organization_id)
    
    # ============================================================================
    # PROJECTS METHODS
    # ============================================================================
    
    def projects_get_portals(self) -> Dict[str, Any]:
        """Get all project portals."""
        return self.make_request('projects', 'portal')
    
    def projects_get_projects(self, portal_id: str) -> Dict[str, Any]:
        """Get projects from a portal."""
        return self.make_request('projects', f'portal/{portal_id}/projects')
    
    def projects_get_tasks(self, portal_id: str, project_id: str) -> Dict[str, Any]:
        """Get tasks from a project."""
        return self.make_request('projects', f'portal/{portal_id}/projects/{project_id}/tasks')
    
    def projects_create_task(self, portal_id: str, project_id: str, task_data: Dict) -> Dict[str, Any]:
        """Create a task in a project."""
        return self.make_request('projects', f'portal/{portal_id}/projects/{project_id}/tasks', method='POST', data=task_data)
    
    # ============================================================================
    # DESK (SUPPORT) METHODS
    # ============================================================================
    
    def desk_get_tickets(self, org_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get support tickets."""
        params = {'limit': limit}
        headers = self.auth.get_headers()
        headers['orgId'] = org_id
        return self.make_request('desk', 'tickets', params=params)
    
    def desk_get_contacts(self, org_id: str) -> Dict[str, Any]:
        """Get support contacts."""
        return self.make_request('desk', 'contacts')
    
    def desk_create_ticket(self, org_id: str, ticket_data: Dict) -> Dict[str, Any]:
        """Create a support ticket."""
        return self.make_request('desk', 'tickets', method='POST', data=ticket_data)
    
    # ============================================================================
    # ANALYTICS METHODS
    # ============================================================================
    
    def analytics_get_workspaces(self) -> Dict[str, Any]:
        """Get Analytics workspaces."""
        return self.make_request('analytics', 'workspaces')
    
    def analytics_get_views(self, workspace_id: str) -> Dict[str, Any]:
        """Get views in a workspace."""
        return self.make_request('analytics', f'workspaces/{workspace_id}/views')
    
    # ============================================================================
    # PEOPLE (HR) METHODS
    # ============================================================================
    
    def people_get_employees(self) -> Dict[str, Any]:
        """Get employee list."""
        return self.make_request('people', 'forms/employee/getRecords')
    
    def people_get_leave_records(self) -> Dict[str, Any]:
        """Get leave records."""
        return self.make_request('people', 'leave/getLeaveRecords')
    
    # ============================================================================
    # INVENTORY METHODS
    # ============================================================================
    
    def inventory_get_items(self, organization_id: str) -> Dict[str, Any]:
        """Get inventory items."""
        return self.make_request('inventory', 'items', organization_id=organization_id)
    
    def inventory_get_sales_orders(self, organization_id: str) -> Dict[str, Any]:
        """Get sales orders."""
        return self.make_request('inventory', 'salesorders', organization_id=organization_id)
    
    # ============================================================================
    # RECRUIT METHODS
    # ============================================================================
    
    def recruit_get_candidates(self) -> Dict[str, Any]:
        """Get candidates."""
        return self.make_request('recruit', 'Candidates')
    
    def recruit_get_job_openings(self) -> Dict[str, Any]:
        """Get job openings."""
        return self.make_request('recruit', 'JobOpenings')
