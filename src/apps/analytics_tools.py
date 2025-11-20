"""Zoho Analytics Tools"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def register_analytics_tools(mcp, api_router, app_registry):
    if not app_registry.is_app_enabled("Analytics"):
        return
    logger.info("Registering Zoho Analytics tools")
    
    @mcp.tool()
    def analytics_get_workspaces(ctx) -> Dict[str, Any]:
        """Get available workspaces."""
        return api_router.make_request("Analytics", "workspaces", "GET")
    
    @mcp.tool()
    def analytics_get_reports(ctx, workspace_id: str) -> Dict[str, Any]:
        """Get reports from workspace."""
        return api_router.make_request("Analytics", f"workspaces/{workspace_id}/views", "GET")
    
    @mcp.tool()
    def analytics_get_report_data(ctx, workspace_id: str, view_id: str) -> Dict[str, Any]:
        """Get report data."""
        return api_router.make_request("Analytics", f"workspaces/{workspace_id}/views/{view_id}/data", "GET")
    
    @mcp.tool()
    def analytics_execute_sql(ctx, workspace_id: str, sql_query: str) -> Dict[str, Any]:
        """Execute custom SQL query."""
        data = {'sql': sql_query}
        return api_router.make_request("Analytics", f"workspaces/{workspace_id}/sqlquery", "POST", data=data)
    
    @mcp.tool()
    def analytics_get_dashboards(ctx, workspace_id: str) -> Dict[str, Any]:
        """Get dashboards."""
        return api_router.make_request("Analytics", f"workspaces/{workspace_id}/dashboards", "GET")
    
    logger.info("Zoho Analytics tools registered")
