"""Zoho Inventory Tools.

``organization_id`` is optional.  When omitted the router discovers the first
organisation and adds the ``organization_id`` query parameter.
"""

from typing import Any, Dict, Optional

import logging

logger = logging.getLogger(__name__)


def _org_path(organization_id: Optional[str]) -> Optional[str]:
    return f"organization/{organization_id}" if organization_id else None


def register_inventory_tools(mcp, api_router, app_registry):
    """Register Zoho Inventory tools with the MCP server."""

    logger.info("Registering Zoho Inventory tools")

    @mcp.tool()
    def inventory_get_items(
        page: int = 1,
        per_page: int = 200,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get items from Zoho Inventory."""
        return api_router.make_request(
            app_name="Inventory",
            endpoint="items",
            method="GET",
            params={"page": page, "per_page": per_page},
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def inventory_get_item_by_id(
        item_id: str, organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific item with stock levels."""
        return api_router.make_request(
            app_name="Inventory",
            endpoint=f"items/{item_id}",
            method="GET",
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def inventory_create_item(
        item_data: Dict[str, Any], organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new item."""
        return api_router.make_request(
            app_name="Inventory",
            endpoint="items",
            method="POST",
            data=item_data,
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def inventory_get_sales_orders(
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get sales orders."""
        return api_router.make_request(
            app_name="Inventory",
            endpoint="salesorders",
            method="GET",
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def inventory_get_warehouses(
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get warehouse information."""
        return api_router.make_request(
            app_name="Inventory",
            endpoint="warehouses",
            method="GET",
            additional_path=_org_path(organization_id),
        )

    @mcp.tool()
    def inventory_get_organizations() -> Dict[str, Any]:
        """Get the organisations available to the connected Zoho Inventory account."""
        return api_router.make_request(
            app_name="Inventory", endpoint="organizations", method="GET"
        )

    logger.info("Zoho Inventory tools registered")
