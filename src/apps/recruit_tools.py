"""Zoho Recruit Tools"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def register_recruit_tools(mcp, api_router, app_registry):
    if not app_registry.is_app_enabled("Recruit"):
        return
    logger.info("Registering Zoho Recruit tools")
    
    @mcp.tool()
    def recruit_get_candidates(ctx, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get candidates from Zoho Recruit."""
        params = {'page': page, 'per_page': per_page}
        return api_router.make_request("Recruit", "Candidates", "GET", params=params)
    
    @mcp.tool()
    def recruit_get_candidate_by_id(ctx, candidate_id: str) -> Dict[str, Any]:
        """Get specific candidate details."""
        return api_router.make_request("Recruit", f"Candidates/{candidate_id}", "GET")
    
    @mcp.tool()
    def recruit_search_candidates(ctx, criteria: str) -> Dict[str, Any]:
        """Search candidates by criteria."""
        params = {'criteria': criteria}
        return api_router.make_request("Recruit", "Candidates/search", "GET", params=params)
    
    @mcp.tool()
    def recruit_get_job_openings(ctx) -> Dict[str, Any]:
        """Get job openings."""
        return api_router.make_request("Recruit", "JobOpenings", "GET")
    
    @mcp.tool()
    def recruit_update_candidate_status(ctx, candidate_id: str, status: str) -> Dict[str, Any]:
        """Update candidate status."""
        data = {'Status': status}
        return api_router.make_request("Recruit", f"Candidates/{candidate_id}", "PUT", data=data)
    
    logger.info("Zoho Recruit tools registered")
