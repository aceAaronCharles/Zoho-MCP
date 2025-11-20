"""Zoho Inventory Tools"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def register_inventory_tools(mcp, api_router, app_registry):
    if not app_registry.is_app_enabled("Inventory"):
        return
    logger.info("Registering Zoho Inventory tools")
    
    @mcp.tool()
    def inventory_get_items(ctx, organization_id: str, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get items from Zoho Inventory."""
        params = {'page': page, 'per_page': per_page}
        return api_router.make_request("Inventory", "items", "GET", params=params, additional_path=f"organization/{organization_id}")
    
    @mcp.tool()
    def inventory_get_item_by_id(ctx, organization_id: str, item_id: str) -> Dict[str, Any]:
        """Get specific item with stock levels."""
        return api_router.make_request("Inventory", f"items/{item_id}", "GET", additional_path=f"organization/{organization_id}")
    
    @mcp.tool()
    def inventory_create_item(ctx, organization_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new item."""
        return api_router.make_request("Inventory", "items", "POST", data=item_data, additional_path=f"organization/{organization_id}")
    
    @mcp.tool()
    def inventory_get_sales_orders(ctx, organization_id: str) -> Dict[str, Any]:
        """Get sales orders."""
        return api_router.make_request("Inventory", "salesorders", "GET", additional_path=f"organization/{organization_id}")
    
    @mcp.tool()
    def inventory_get_warehouses(ctx, organization_id: str) -> Dict[str, Any]:
        """Get warehouse information."""
        return api_router.make_request("Inventory", "warehouses", "GET", additional_path=f"organization/{organization_id}")
    
    logger.info("Zoho Inventory tools registered")
