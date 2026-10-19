"""
Zoho People Tools
MCP tools for Zoho People HR operations.

Zoho People exposes form data through
``/people/api/forms/{formLinkName}/getRecords`` and individual records through
``getDataByID``.  ``sIndex`` is 1-based.
"""

from typing import Any, Dict, Optional

import logging

logger = logging.getLogger(__name__)


def register_people_tools(mcp, api_router, app_registry):
    """Register Zoho People tools with the MCP server."""

    logger.info("Registering Zoho People tools")

    @mcp.tool()
    def people_get_employees(page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get employees from Zoho People (1-based paging)."""
        params = {"sIndex": (max(page, 1) - 1) * per_page + 1, "limit": per_page}
        return api_router.make_request(
            "People", "forms/employee/getRecords", "GET", params=params
        )

    @mcp.tool()
    def people_get_employee_by_id(employee_id: str) -> Dict[str, Any]:
        """Get a specific employee record by record ID."""
        return api_router.make_request(
            "People",
            "forms/employee/getDataByID",
            "GET",
            params={"recordId": employee_id},
        )

    @mcp.tool()
    def people_get_attendance(
        employee_id: str, from_date: str, to_date: str
    ) -> Dict[str, Any]:
        """Get attendance records for an employee between two dates."""
        return api_router.make_request(
            "People",
            "forms/attendance/getRecords",
            "GET",
            params={
                "fromDate": from_date,
                "toDate": to_date,
                "searchColumn": "Employee_ID",
                "searchValue": employee_id,
            },
        )

    @mcp.tool()
    def people_get_leave_requests(status: Optional[str] = None) -> Dict[str, Any]:
        """Get leave requests, optionally filtered by approval status."""
        params: Dict[str, Any] = {}
        if status:
            params["searchColumn"] = "Approval_Status"
            params["searchValue"] = status
        return api_router.make_request(
            "People", "forms/leave/getRecords", "GET", params=params or None
        )

    @mcp.tool()
    def people_get_form_records(
        form_name: str,
        page: int = 1,
        per_page: int = 200,
        search_column: Optional[str] = None,
        search_value: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get records from any Zoho People form by its link name."""
        params: Dict[str, Any] = {
            "sIndex": (max(page, 1) - 1) * per_page + 1,
            "limit": per_page,
        }
        if search_column and search_value is not None:
            params["searchColumn"] = search_column
            params["searchValue"] = search_value
        return api_router.make_request(
            "People", f"forms/{form_name}/getRecords", "GET", params=params
        )

    logger.info("Zoho People tools registered successfully")
