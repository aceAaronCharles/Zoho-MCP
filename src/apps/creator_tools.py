"""Zoho Creator Tools.

The documented Creator v2 API is hosted on the Zoho API domain:

    https://www.zohoapis.com/creator/v2/data/{owner}/{app}/report/{report}
    https://www.zohoapis.com/creator/v2/meta/{owner}/{app}/forms

``owner`` is the Creator workspace/account owner name.  It is discovered from
``meta/applications`` when not supplied.  A caller can also pass
``application_name="owner/app"``.
"""

from typing import Any, Dict, Optional

import logging

logger = logging.getLogger(__name__)


def register_creator_tools(mcp, api_router, app_registry):
    """Register Zoho Creator tools with the MCP server."""

    logger.info("Registering Zoho Creator tools")

    def _resolve_owner(
        application_name: str, account_owner: Optional[str]
    ):
        """Return (owner, application, error) for a Creator application."""
        if account_owner:
            return account_owner, application_name, None
        if "/" in application_name:
            owner, app = application_name.split("/", 1)
            return owner, app, None

        result = api_router.make_request("Creator", "meta/applications", "GET")
        if result.get("status") != "success":
            return None, application_name, result
        applications = (result.get("data") or {}).get("applications", [])
        for app in applications:
            if application_name in {
                app.get("link_name"),
                app.get("application_name"),
            }:
                owner = app.get("workspace_name") or app.get("account_owner")
                if owner:
                    return owner, app.get("link_name", application_name), None
        return (
            None,
            application_name,
            {
                "status": "error",
                "error_type": "not_found",
                "message": (
                    f"Creator application '{application_name}' was not found. "
                    "Pass account_owner or application_name='owner/app'."
                ),
            },
        )

    @mcp.tool()
    def creator_get_applications() -> Dict[str, Any]:
        """Get available Creator applications (includes their workspace/owner)."""
        return api_router.make_request("Creator", "meta/applications", "GET")

    @mcp.tool()
    def creator_get_forms(
        application_name: str, account_owner: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get forms from a Creator application."""
        owner, app, error = _resolve_owner(application_name, account_owner)
        if error:
            return error
        return api_router.make_request(
            "Creator", f"meta/{owner}/{app}/forms", "GET"
        )

    @mcp.tool()
    def creator_get_form_metadata(
        application_name: str,
        form_name: str,
        account_owner: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get field metadata for a Creator form."""
        owner, app, error = _resolve_owner(application_name, account_owner)
        if error:
            return error
        return api_router.make_request(
            "Creator", f"meta/{owner}/{app}/form/{form_name}/fields", "GET"
        )

    @mcp.tool()
    def creator_get_reports(
        application_name: str, account_owner: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get the reports of a Creator application (use their link_name with creator_get_records)."""
        owner, app, error = _resolve_owner(application_name, account_owner)
        if error:
            return error
        return api_router.make_request(
            "Creator", f"meta/{owner}/{app}/reports", "GET"
        )

    @mcp.tool()
    def creator_get_records(
        application_name: str,
        report_name: str,
        account_owner: Optional[str] = None,
        from_index: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get records from a Creator report (report_name is a report link_name)."""
        owner, app, error = _resolve_owner(application_name, account_owner)
        if error:
            return error
        params: Dict[str, Any] = {}
        if from_index is not None:
            params["from"] = from_index
        if limit is not None:
            params["limit"] = limit
        return api_router.make_request(
            "Creator",
            f"data/{owner}/{app}/report/{report_name}",
            "GET",
            params=params or None,
        )

    @mcp.tool()
    def creator_create_record(
        application_name: str,
        form_name: str,
        record_data: Dict[str, Any],
        account_owner: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a record in a Creator form."""
        owner, app, error = _resolve_owner(application_name, account_owner)
        if error:
            return error
        return api_router.make_request(
            "Creator",
            f"data/{owner}/{app}/form/{form_name}",
            "POST",
            data={"data": record_data},
        )

    @mcp.tool()
    def creator_update_record(
        application_name: str,
        report_name: str,
        record_id: str,
        record_data: Dict[str, Any],
        account_owner: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a record in a Creator report."""
        owner, app, error = _resolve_owner(application_name, account_owner)
        if error:
            return error
        return api_router.make_request(
            "Creator",
            f"data/{owner}/{app}/report/{report_name}/{record_id}",
            "PATCH",
            data={"data": record_data},
        )

    logger.info("Zoho Creator tools registered")
