"""Zoho Recruit Tools"""

from typing import Any, Dict

import logging

logger = logging.getLogger(__name__)


def register_recruit_tools(mcp, api_router, app_registry):
    """Register Zoho Recruit tools with the MCP server."""

    logger.info("Registering Zoho Recruit tools")

    @mcp.tool()
    def recruit_get_candidates(page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get candidates from Zoho Recruit."""
        return api_router.make_request(
            "Recruit", "Candidates", "GET", params={"page": page, "per_page": per_page}
        )

    @mcp.tool()
    def recruit_get_candidate_by_id(candidate_id: str) -> Dict[str, Any]:
        """Get specific candidate details."""
        return api_router.make_request("Recruit", f"Candidates/{candidate_id}", "GET")

    @mcp.tool()
    def recruit_search_candidates(criteria: str) -> Dict[str, Any]:
        """Search candidates using Zoho Recruit criteria syntax."""
        return api_router.make_request(
            "Recruit", "Candidates/search", "GET", params={"criteria": criteria}
        )

    @mcp.tool()
    def recruit_get_job_openings() -> Dict[str, Any]:
        """Get job openings."""
        return api_router.make_request("Recruit", "Job_Openings", "GET")

    @mcp.tool()
    def recruit_update_candidate_status(candidate_id: str, status: str) -> Dict[str, Any]:
        """Update a candidate's status."""
        data = {"data": [{"id": candidate_id, "Status": status}]}
        return api_router.make_request("Recruit", "Candidates", "PUT", data=data)

    @mcp.tool()
    def recruit_create_candidate(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a candidate (candidate_data: Last_Name, Email, ...)."""
        return api_router.make_request(
            "Recruit", "Candidates", "POST", data={"data": [candidate_data]}
        )

    logger.info("Zoho Recruit tools registered")
