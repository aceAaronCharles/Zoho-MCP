"""Zoho Analytics Tools.

Zoho Analytics requires the ``ZANALYTICS-ORGID`` header for data endpoints.
The router discovers it from the workspaces endpoint when it is not set in
``ZOHO_ANALYTICS_ORG_ID``.

Analytics does not allow synchronous export for every view, so SQL queries use
the documented asynchronous bulk-export flow and poll until the job completes.
"""

import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def register_analytics_tools(mcp, api_router, app_registry):
    """Register Zoho Analytics tools with the MCP server."""

    logger.info("Registering Zoho Analytics tools")

    @mcp.tool()
    def analytics_get_workspaces() -> Dict[str, Any]:
        """Get available workspaces."""
        return api_router.make_request("Analytics", "workspaces", "GET")

    @mcp.tool()
    def analytics_get_reports(workspace_id: str) -> Dict[str, Any]:
        """Get reports/views from a workspace."""
        return api_router.make_request(
            "Analytics", f"workspaces/{workspace_id}/views", "GET"
        )

    @mcp.tool()
    def analytics_get_report_data(
        workspace_id: str,
        view_id: str,
        from_index: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get JSON data for a report/view."""
        config: Dict[str, Any] = {"responseFormat": "json"}
        if from_index is not None:
            config["from"] = from_index
        if limit is not None:
            config["limit"] = limit
        return api_router.make_request(
            "Analytics",
            f"workspaces/{workspace_id}/views/{view_id}/data",
            "GET",
            params={"CONFIG": json.dumps(config)},
        )

    @mcp.tool()
    def analytics_execute_sql(
        workspace_id: str, sql_query: str, timeout_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Execute a SQL query using Zoho Analytics' asynchronous bulk export.

        The call submits an export job, polls it, then downloads the JSON
        result.  Large queries may need a longer ``timeout_seconds``.
        """
        config = {"sqlQuery": sql_query, "responseFormat": "json"}
        submitted = api_router.make_request(
            "Analytics",
            f"bulk/workspaces/{workspace_id}/data",
            "GET",
            params={"CONFIG": json.dumps(config)},
        )
        if submitted.get("status") != "success":
            return submitted

        payload = submitted.get("data") or {}
        job_id = (payload.get("data") or {}).get("jobId")
        if not job_id:
            return {
                "status": "error",
                "error_type": "api_error",
                "message": "Zoho Analytics did not return a job ID for the query.",
                "response": submitted,
            }

        deadline = time.time() + max(5, int(timeout_seconds))
        job_status = None
        while time.time() < deadline:
            info = api_router.make_request(
                "Analytics",
                f"bulk/workspaces/{workspace_id}/exportjobs/{job_id}",
                "GET",
            )
            if info.get("status") != "success":
                return info
            job_data = (info.get("data") or {}).get("data") or {}
            job_status = job_data.get("jobStatus")
            if job_status == "JOB COMPLETED":
                result = api_router.make_request(
                    "Analytics",
                    f"bulk/workspaces/{workspace_id}/exportjobs/{job_id}/data",
                    "GET",
                )
                if result.get("status") == "success":
                    result["job_id"] = job_id
                    result["workspace_id"] = workspace_id
                return result
            if job_status in {"JOB FAILED", "JOB CANCELLED"}:
                return {
                    "status": "error",
                    "error_type": "api_error",
                    "message": f"Zoho Analytics export job ended with status {job_status}.",
                    "job_id": job_id,
                    "job": job_data,
                }
            time.sleep(2)

        return {
            "status": "error",
            "error_type": "timeout",
            "message": (
                f"Zoho Analytics export job {job_id} did not finish within "
                f"{timeout_seconds} seconds. Increase timeout_seconds or poll the job later."
            ),
            "job_id": job_id,
            "job_status": job_status,
        }

    @mcp.tool()
    def analytics_get_dashboards(workspace_id: str) -> Dict[str, Any]:
        """Get dashboards from a workspace."""
        return api_router.make_request(
            "Analytics", f"workspaces/{workspace_id}/dashboards", "GET"
        )

    logger.info("Zoho Analytics tools registered")
