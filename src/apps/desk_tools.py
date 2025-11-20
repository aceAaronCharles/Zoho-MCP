"""
Zoho Desk Tools
MCP tools for Zoho Desk customer support operations.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def register_desk_tools(mcp, api_router, app_registry):
    """
    Register Zoho Desk tools with MCP server.
    
    Args:
        mcp: FastMCP server instance
        api_router: APIRouter instance
        app_registry: AppRegistry instance
    """
    if not app_registry.is_app_enabled("Desk"):
        logger.info("Zoho Desk is not enabled, skipping Desk tools registration")
        return
    
    logger.info("Registering Zoho Desk tools")
    
    @mcp.tool()
    def desk_get_tickets(
        ctx,
        status: str = None,
        page: int = 1,
        per_page: int = 100
    ) -> Dict[str, Any]:
        """
        Get tickets from Zoho Desk.
        
        Args:
            status: Filter by status (e.g., 'Open', 'On Hold', 'Closed')
            page: Page number (default: 1)
            per_page: Records per page (default: 100)
        
        Returns:
            Dict containing tickets data
        """
        params = {
            'from': (page - 1) * per_page,
            'limit': per_page
        }
        
        if status:
            params['status'] = status
        
        return api_router.make_request(
            app_name="Desk",
            endpoint="tickets",
            method="GET",
            params=params
        )
    
    @mcp.tool()
    def desk_get_ticket_by_id(
        ctx,
        ticket_id: str
    ) -> Dict[str, Any]:
        """
        Get specific ticket details including comments.
        
        Args:
            ticket_id: Ticket ID
        
        Returns:
            Dict containing ticket details
        """
        return api_router.make_request(
            app_name="Desk",
            endpoint=f"tickets/{ticket_id}",
            method="GET"
        )
    
    @mcp.tool()
    def desk_create_ticket(
        ctx,
        ticket_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new ticket in Zoho Desk.
        
        Args:
            ticket_data: Dictionary containing ticket fields (subject, description, contactId, etc.)
        
        Returns:
            Dict containing created ticket information
        """
        return api_router.make_request(
            app_name="Desk",
            endpoint="tickets",
            method="POST",
            data=ticket_data
        )
    
    @mcp.tool()
    def desk_update_ticket(
        ctx,
        ticket_id: str,
        ticket_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing ticket.
        
        Args:
            ticket_id: Ticket ID to update
            ticket_data: Dictionary containing fields to update
        
        Returns:
            Dict containing updated ticket information
        """
        return api_router.make_request(
            app_name="Desk",
            endpoint=f"tickets/{ticket_id}",
            method="PATCH",
            data=ticket_data
        )
    
    @mcp.tool()
    def desk_add_comment(
        ctx,
        ticket_id: str,
        comment: str,
        is_public: bool = True
    ) -> Dict[str, Any]:
        """
        Add a comment to a ticket.
        
        Args:
            ticket_id: Ticket ID
            comment: Comment text
            is_public: Whether comment is public (default: True)
        
        Returns:
            Dict containing comment information
        """
        comment_data = {
            'content': comment,
            'isPublic': is_public
        }
        
        return api_router.make_request(
            app_name="Desk",
            endpoint=f"tickets/{ticket_id}/comments",
            method="POST",
            data=comment_data
        )
    
    @mcp.tool()
    def desk_get_contacts(
        ctx,
        page: int = 1,
        per_page: int = 100
    ) -> Dict[str, Any]:
        """
        Get contacts from Zoho Desk.
        
        Args:
            page: Page number (default: 1)
            per_page: Records per page (default: 100)
        
        Returns:
            Dict containing contacts data
        """
        params = {
            'from': (page - 1) * per_page,
            'limit': per_page
        }
        
        return api_router.make_request(
            app_name="Desk",
            endpoint="contacts",
            method="GET",
            params=params
        )
    
    @mcp.tool()
    def desk_get_ticket_comments(
        ctx,
        ticket_id: str
    ) -> Dict[str, Any]:
        """
        Get all comments for a specific ticket.
        
        Args:
            ticket_id: Ticket ID
        
        Returns:
            Dict containing ticket comments
        """
        return api_router.make_request(
            app_name="Desk",
            endpoint=f"tickets/{ticket_id}/comments",
            method="GET"
        )
    
    logger.info("Zoho Desk tools registered successfully")
