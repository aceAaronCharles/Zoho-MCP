"""
Zoho Projects Tools
MCP tools for Zoho Projects project management operations.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def register_projects_tools(mcp, api_router, app_registry):
    """
    Register Zoho Projects tools with MCP server.
    
    Args:
        mcp: FastMCP server instance
        api_router: APIRouter instance
        app_registry: AppRegistry instance
    """
    if not app_registry.is_app_enabled("Projects"):
        logger.info("Zoho Projects is not enabled, skipping Projects tools registration")
        return
    
    logger.info("Registering Zoho Projects tools")
    
    @mcp.tool()
    def projects_get_portals(ctx) -> Dict[str, Any]:
        """
        Get all portals from Zoho Projects.
        
        Returns:
            Dict containing portals data
        """
        return api_router.make_request(
            app_name="Projects",
            endpoint="portals",
            method="GET"
        )
    
    @mcp.tool()
    def projects_get_projects(
        ctx,
        portal_id: str,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """
        Get projects from a specific portal.
        
        Args:
            portal_id: Portal ID
            page: Page number (default: 1)
            per_page: Records per page (default: 200)
        
        Returns:
            Dict containing projects data
        """
        params = {
            'index': page,
            'range': per_page
        }
        
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects",
            method="GET",
            params=params
        )
    
    @mcp.tool()
    def projects_get_project_by_id(
        ctx,
        portal_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Get specific project details.
        
        Args:
            portal_id: Portal ID
            project_id: Project ID
        
        Returns:
            Dict containing project details
        """
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}",
            method="GET"
        )
    
    @mcp.tool()
    def projects_get_tasks(
        ctx,
        portal_id: str,
        project_id: str,
        page: int = 1,
        per_page: int = 200,
        status: str = None
    ) -> Dict[str, Any]:
        """
        Get tasks from a specific project.
        
        Args:
            portal_id: Portal ID
            project_id: Project ID
            page: Page number (default: 1)
            per_page: Records per page (default: 200)
            status: Filter by status (optional)
        
        Returns:
            Dict containing tasks data
        """
        params = {
            'index': page,
            'range': per_page
        }
        
        if status:
            params['status'] = status
        
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/tasks",
            method="GET",
            params=params
        )
    
    @mcp.tool()
    def projects_create_task(
        ctx,
        portal_id: str,
        project_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new task in a project.
        
        Args:
            portal_id: Portal ID
            project_id: Project ID
            task_data: Dictionary containing task fields (name, description, etc.)
        
        Returns:
            Dict containing created task information
        """
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/tasks",
            method="POST",
            data=task_data
        )
    
    @mcp.tool()
    def projects_update_task(
        ctx,
        portal_id: str,
        project_id: str,
        task_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing task.
        
        Args:
            portal_id: Portal ID
            project_id: Project ID
            task_id: Task ID to update
            task_data: Dictionary containing fields to update
        
        Returns:
            Dict containing updated task information
        """
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/tasks/{task_id}",
            method="POST",
            data=task_data
        )
    
    @mcp.tool()
    def projects_get_milestones(
        ctx,
        portal_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Get milestones from a specific project.
        
        Args:
            portal_id: Portal ID
            project_id: Project ID
        
        Returns:
            Dict containing milestones data
        """
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/milestones",
            method="GET"
        )
    
    @mcp.tool()
    def projects_get_timesheets(
        ctx,
        portal_id: str,
        project_id: str,
        user_id: str = None,
        date: str = None
    ) -> Dict[str, Any]:
        """
        Get timesheets from a specific project.
        
        Args:
            portal_id: Portal ID
            project_id: Project ID
            user_id: Filter by user ID (optional)
            date: Filter by date in YYYY-MM-DD format (optional)
        
        Returns:
            Dict containing timesheets data
        """
        params = {}
        
        if user_id:
            params['users_list'] = user_id
        if date:
            params['date'] = date
        
        return api_router.make_request(
            app_name="Projects",
            endpoint=f"portal/{portal_id}/projects/{project_id}/logs",
            method="GET",
            params=params if params else None
        )
    
    logger.info("Zoho Projects tools registered successfully")
