"""
Zoho People Tools
MCP tools for Zoho People HR operations.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def register_people_tools(mcp, api_router, app_registry):
    """Register Zoho People tools with MCP server."""
    if not app_registry.is_app_enabled("People"):
        logger.info("Zoho People is not enabled, skipping People tools registration")
        return
    
    logger.info("Registering Zoho People tools")
    
    @mcp.tool()
    def people_get_employees(ctx, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get employees from Zoho People."""
        params = {'sIndex': page - 1, 'limit': per_page}
        return api_router.make_request("People", "forms/employee/records", "GET", params=params)
    
    @mcp.tool()
    def people_get_employee_by_id(ctx, employee_id: str) -> Dict[str, Any]:
        """Get specific employee details."""
        return api_router.make_request("People", f"forms/employee/records/{employee_id}", "GET")
    
    @mcp.tool()
    def people_get_attendance(ctx, employee_id: str, from_date: str, to_date: str) -> Dict[str, Any]:
        """Get attendance data for an employee."""
        params = {'fromDate': from_date, 'toDate': to_date}
        return api_router.make_request("People", f"attendance/{employee_id}", "GET", params=params)
    
    @mcp.tool()
    def people_get_leave_requests(ctx, status: str = None) -> Dict[str, Any]:
        """Get leave requests."""
        params = {'status': status} if status else None
        return api_router.make_request("People", "leave", "GET", params=params)
    
    @mcp.tool()
    def people_get_forms(ctx) -> Dict[str, Any]:
        """Get custom forms data."""
        return api_router.make_request("People", "forms", "GET")
    
    logger.info("Zoho People tools registered successfully")
