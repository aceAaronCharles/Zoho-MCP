"""
Zoho Books Tools
MCP tools for Zoho Books financial operations.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def register_books_tools(mcp, api_router, app_registry):
    """
    Register Zoho Books tools with MCP server.
    
    Args:
        mcp: FastMCP server instance
        api_router: APIRouter instance
        app_registry: AppRegistry instance
    """
    if not app_registry.is_app_enabled("Books"):
        logger.info("Zoho Books is not enabled, skipping Books tools registration")
        return
    
    logger.info("Registering Zoho Books tools")
    
    @mcp.tool()
    def books_get_invoices(
        ctx,
        organization_id: str,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """
        Get invoices from Zoho Books.
        
        Args:
            organization_id: Zoho Books organization ID
            page: Page number (default: 1)
            per_page: Records per page (default: 200)
        
        Returns:
            Dict containing invoices data
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        return api_router.make_request(
            app_name="Books",
            endpoint="invoices",
            method="GET",
            params=params,
            additional_path=f"organization/{organization_id}"
        )
    
    @mcp.tool()
    def books_get_invoice_by_id(
        ctx,
        organization_id: str,
        invoice_id: str
    ) -> Dict[str, Any]:
        """
        Get a specific invoice by ID from Zoho Books.
        
        Args:
            organization_id: Zoho Books organization ID
            invoice_id: Invoice ID
        
        Returns:
            Dict containing invoice details
        """
        return api_router.make_request(
            app_name="Books",
            endpoint=f"invoices/{invoice_id}",
            method="GET",
            additional_path=f"organization/{organization_id}"
        )
    
    @mcp.tool()
    def books_create_invoice(
        ctx,
        organization_id: str,
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new invoice in Zoho Books.
        
        Args:
            organization_id: Zoho Books organization ID
            invoice_data: Dictionary containing invoice fields (customer_id, line_items, etc.)
        
        Returns:
            Dict containing created invoice information
        """
        return api_router.make_request(
            app_name="Books",
            endpoint="invoices",
            method="POST",
            data=invoice_data,
            additional_path=f"organization/{organization_id}"
        )
    
    @mcp.tool()
    def books_update_invoice(
        ctx,
        organization_id: str,
        invoice_id: str,
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing invoice in Zoho Books.
        
        Args:
            organization_id: Zoho Books organization ID
            invoice_id: Invoice ID to update
            invoice_data: Dictionary containing fields to update
        
        Returns:
            Dict containing updated invoice information
        """
        return api_router.make_request(
            app_name="Books",
            endpoint=f"invoices/{invoice_id}",
            method="PUT",
            data=invoice_data,
            additional_path=f"organization/{organization_id}"
        )
    
    @mcp.tool()
    def books_get_customers(
        ctx,
        organization_id: str,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """
        Get customers from Zoho Books.
        
        Args:
            organization_id: Zoho Books organization ID
            page: Page number (default: 1)
            per_page: Records per page (default: 200)
        
        Returns:
            Dict containing customers data
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        return api_router.make_request(
            app_name="Books",
            endpoint="contacts",
            method="GET",
            params=params,
            additional_path=f"organization/{organization_id}"
        )
    
    @mcp.tool()
    def books_get_vendors(
        ctx,
        organization_id: str,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """
        Get vendors from Zoho Books.
        
        Args:
            organization_id: Zoho Books organization ID
            page: Page number (default: 1)
            per_page: Records per page (default: 200)
        
        Returns:
            Dict containing vendors data
        """
        params = {
            'page': page,
            'per_page': per_page,
            'contact_type': 'vendor'
        }
        
        return api_router.make_request(
            app_name="Books",
            endpoint="contacts",
            method="GET",
            params=params,
            additional_path=f"organization/{organization_id}"
        )
    
    @mcp.tool()
    def books_get_bills(
        ctx,
        organization_id: str,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """
        Get bills from Zoho Books.
        
        Args:
            organization_id: Zoho Books organization ID
            page: Page number (default: 1)
            per_page: Records per page (default: 200)
        
        Returns:
            Dict containing bills data
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        return api_router.make_request(
            app_name="Books",
            endpoint="bills",
            method="GET",
            params=params,
            additional_path=f"organization/{organization_id}"
        )
    
    @mcp.tool()
    def books_get_expenses(
        ctx,
        organization_id: str,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """
        Get expenses from Zoho Books.
        
        Args:
            organization_id: Zoho Books organization ID
            page: Page number (default: 1)
            per_page: Records per page (default: 200)
        
        Returns:
            Dict containing expenses data
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        return api_router.make_request(
            app_name="Books",
            endpoint="expenses",
            method="GET",
            params=params,
            additional_path=f"organization/{organization_id}"
        )
    
    logger.info("Zoho Books tools registered successfully")
