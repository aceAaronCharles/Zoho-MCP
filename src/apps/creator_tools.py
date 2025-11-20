"""Zoho Creator Tools"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def register_creator_tools(mcp, api_router, app_registry):
    if not app_registry.is_app_enabled("Creator"):
        return
    logger.info("Registering Zoho Creator tools")
    
    @mcp.tool()
    def creator_get_applications(ctx) -> Dict[str, Any]:
        """Get available Creator applications."""
        return api_router.make_request("Creator", "applications", "GET")
    
    @mcp.tool()
    def creator_get_forms(ctx, application_name: str) -> Dict[str, Any]:
        """Get forms from application."""
        return api_router.make_request("Creator", f"{application_name}/forms", "GET")
    
    @mcp.tool()
    def creator_get_form_metadata(ctx, application_name: str, form_name: str) -> Dict[str, Any]:
        """Get form field information."""
        return api_router.make_request("Creator", f"{application_name}/form/{form_name}", "GET")
    
    @mcp.tool()
    def creator_get_records(ctx, application_name: str, report_name: str) -> Dict[str, Any]:
        """Get records from Creator report."""
        return api_router.make_request("Creator", f"{application_name}/report/{report_name}", "GET")
    
    @mcp.tool()
    def creator_create_record(ctx, application_name: str, form_name: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create record in Creator application."""
        return api_router.make_request("Creator", f"{application_name}/form/{form_name}", "POST", data=record_data)
    
    logger.info("Zoho Creator tools registered")
