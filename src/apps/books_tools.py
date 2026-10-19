"""
Zoho Books Tools
MCP tools for Zoho Books financial operations.

``organization_id`` is optional.  When omitted the router discovers the first
organisation from ``GET /books/v3/organizations`` and adds it as the
``organization_id`` query parameter (the Books API does not accept it in the
path).
"""

from typing import Any, Dict, Optional

import logging

logger = logging.getLogger(__name__)


def _org_path(organization_id: Optional[str]) -> Optional[str]:
    """Return the legacy path fragment, or None to trigger auto-discovery."""
    return f"organization/{organization_id}" if organization_id else None


def register_books_tools(mcp, api_router, app_registry):
    """Register Zoho Books tools with the MCP server."""

    logger.info("Registering Zoho Books tools")

    @mcp.tool()
    def books_get_invoices(
        page: int = 1,
        per_page: int = 200,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get invoices from Zoho Books."""
        return api_router.make_request(
            app_name="Books",
            endpoint="invoices",
            method="GET",
            params={"page": page, "per_page": per_page},
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def books_get_invoice_by_id(
        invoice_id: str, organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific invoice by ID."""
        return api_router.make_request(
            app_name="Books",
            endpoint=f"invoices/{invoice_id}",
            method="GET",
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def books_create_invoice(
        invoice_data: Dict[str, Any], organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new invoice (invoice_data: customer_id, line_items, ...)."""
        return api_router.make_request(
            app_name="Books",
            endpoint="invoices",
            method="POST",
            data=invoice_data,
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def books_update_invoice(
        invoice_id: str,
        invoice_data: Dict[str, Any],
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing invoice."""
        return api_router.make_request(
            app_name="Books",
            endpoint=f"invoices/{invoice_id}",
            method="PUT",
            data=invoice_data,
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def books_get_customers(
        page: int = 1,
        per_page: int = 200,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get customers from Zoho Books."""
        return api_router.make_request(
            app_name="Books",
            endpoint="contacts",
            method="GET",
            params={"page": page, "per_page": per_page},
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def books_get_vendors(
        page: int = 1,
        per_page: int = 200,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get vendors from Zoho Books."""
        return api_router.make_request(
            app_name="Books",
            endpoint="contacts",
            method="GET",
            params={"page": page, "per_page": per_page, "contact_type": "vendor"},
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def books_get_bills(
        page: int = 1,
        per_page: int = 200,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get bills from Zoho Books."""
        return api_router.make_request(
            app_name="Books",
            endpoint="bills",
            method="GET",
            params={"page": page, "per_page": per_page},
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def books_get_expenses(
        page: int = 1,
        per_page: int = 200,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get expenses from Zoho Books."""
        return api_router.make_request(
            app_name="Books",
            endpoint="expenses",
            method="GET",
            params={"page": page, "per_page": per_page},
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def books_get_organizations() -> Dict[str, Any]:
        """Get the organisations available to the connected Zoho Books account."""
        return api_router.make_request(
            app_name="Books", endpoint="organizations", method="GET"
        )

    logger.info("Zoho Books tools registered successfully")
