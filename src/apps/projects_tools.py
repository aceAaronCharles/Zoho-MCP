"""
Zoho Projects Tools
MCP tools for Zoho Projects project management operations.

Zoho Projects v2 requires trailing slashes on collection endpoints and uses
``index`` (page) / ``range`` (page size) for pagination. POST bodies are
form-encoded by the router.
"""

from typing import Any, Dict, Optional

import logging

logger = logging.getLogger(__name__)


def register_projects_tools(mcp, api_router, app_registry):
    """Register Zoho Projects tools with the MCP server."""

    logger.info("Registering Zoho Projects tools")

    @mcp.tool()
    def projects_get_portals() -> Dict[str, Any]:
        """Get all portals from Zoho Projects."""
        return api_router.make_request(app_name="Projects", endpoint="portals/", method="GET")

    @mcp.tool()
    def projects_get_projects(
        portal_id: str, page: int = 1, per_page: int = 200
    ) -> Dict[str, Any]:
        """Get projects from a specific portal."""
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/",
            method="GET",
            params={"index": page, "range": per_page},
        )

    @mcp.tool()
    def projects_get_project_by_id(portal_id: str, project_id: str) -> Dict[str, Any]:
        """Get specific project details."""
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/",
            method="GET",
        )

    @mcp.tool()
    def projects_get_tasks(
        portal_id: str,
        project_id: str,
        page: int = 1,
        per_page: int = 200,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get tasks from a specific project."""
        params: Dict[str, Any] = {"index": page, "range": per_page}
        if status:
            params["status"] = status
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/tasks/",
            method="GET",
            params=params,
        )

    @mcp.tool()
    def projects_create_task(
        portal_id: str, project_id: str, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new task in a project (task_data: name, description, ...)."""
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/tasks/",
            method="POST",
            data=task_data,
        )

    @mcp.tool()
    def projects_update_task(
        portal_id: str,
        project_id: str,
        task_id: str,
        task_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an existing task."""
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/tasks/{task_id}/",
            method="POST",
            data=task_data,
        )

    @mcp.tool()
    def projects_get_milestones(portal_id: str, project_id: str) -> Dict[str, Any]:
        """Get milestones from a specific project."""
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/milestones/",
            method="GET",
        )

    @mcp.tool()
    def projects_get_timesheets(
        portal_id: str,
        project_id: str,
        user_id: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get timesheets from a specific project."""
        params: Dict[str, Any] = {}
        if user_id:
            params["users_list"] = user_id
        if date:
            params["date"] = date
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/logs/",
            method="GET",
            params=params or None,
        )

    logger.info("Zoho Projects tools registered successfully")
