"""
Zoho API Router
Routes API requests to the appropriate Zoho application endpoints.

The router is responsible for:
  * data-centre-aware hostnames;
  * authentication headers (including Desk/org headers);
  * moving Books/Inventory organisation IDs into the documented query param;
  * timeouts, rate limiting, retries and optional read-only mode.
"""

import logging
import os
import re
import time
from collections import deque
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qsl, quote, urlparse, urlsplit

import requests

try:  # Support both ``import src.api_router`` and ``python src/server.py``.
    from .app_registry import AppRegistry, ZohoAppConfig
    from .zoho_auth import DC_HOSTS, ZohoAuth
except ImportError:  # pragma: no cover - script mode
    from app_registry import AppRegistry, ZohoAppConfig
    from zoho_auth import DC_HOSTS, ZohoAuth

logger = logging.getLogger(__name__)

ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# Apps whose API expects ``organization_id`` as a query parameter.  Older
# versions of this server put it in the path; normalise it transparently.
ORG_ID_QUERY_APPS = {"Books", "Inventory", "Invoice", "Expense", "Subscriptions", "Commerce"}

# Zoho Projects v2 uses form encoding for POST bodies.
FORM_ENCODED_APPS = {"Projects"}


class APIRouter:
    """Routes API requests to appropriate Zoho app endpoints."""

    def __init__(self, auth: Optional[ZohoAuth], registry: AppRegistry):
        """
        Initialize router with auth and app registry.

        Args:
            auth: ZohoAuth instance, or None before configuration is complete.
            registry: AppRegistry instance for app configurations.
        """
        self.auth = auth
        self.registry = registry
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "30") or 30)
        self.rate_limit = int(os.getenv("RATE_LIMIT", "100") or 0)
        self.max_retries = max(0, int(os.getenv("ZOHO_MAX_RETRIES", "0") or 0))
        self.read_only = (os.getenv("MCP_READ_ONLY", "") or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self._request_times: deque = deque()
        self._analytics_org_id: Optional[str] = None
        self._org_ids: Dict[str, str] = {}
        self._desk_org_id: Optional[str] = None
        self._desk_org_checked = False

    def update(self, auth: Optional[ZohoAuth], registry: AppRegistry) -> None:
        """Update the auth/registry in place so registered tool closures stay valid."""
        self.auth = auth
        self.registry = registry

    # ------------------------------------------------------------------
    # URL and header helpers
    # ------------------------------------------------------------------
    def _dc_host(self) -> str:
        """Return the product hostname suffix for the current token."""
        if self.auth and hasattr(self.auth, "get_data_center_host"):
            try:
                return self.auth.get_data_center_host()
            except Exception:
                pass

        explicit_dc = (os.getenv("ZOHO_DC") or "").strip().lower()
        if explicit_dc:
            return DC_HOSTS.get(explicit_dc, f"zoho.{explicit_dc}")

        api_domain = (os.getenv("ZOHO_API_DOMAIN") or "https://www.zohoapis.com").rstrip("/")
        host = urlparse(api_domain).hostname or ""
        if host.endswith("zohocloud.ca"):
            return "zohocloud.ca"
        marker = "zohoapis."
        if marker in host:
            dc = host.split(marker, 1)[1]
            return DC_HOSTS.get(dc, f"zoho.{dc}")
        return "zoho.com"

    def _base_url(self, app_config: ZohoAppConfig) -> str:
        """Return the origin (scheme + host) for an application."""
        # Per-app escape hatch for Zoho API changes or a self-hosted proxy.
        override = (os.getenv(f"ZOHO_{app_config.name.upper()}_BASE_URL") or "").strip()
        if override:
            parsed = urlparse(override)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(
                    f"ZOHO_{app_config.name.upper()}_BASE_URL must be an https:// origin"
                )
            allow_custom = (os.getenv("ZOHO_ALLOW_CUSTOM_BASE_URL", "") or "").strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            host = (parsed.hostname or "").lower()
            if not allow_custom and "zoho" not in host and "zohocloud" not in host:
                raise ValueError(
                    f"Refusing non-Zoho host {host!r}; set ZOHO_ALLOW_CUSTOM_BASE_URL=true "
                    "to allow a proxy."
                )
            return f"{parsed.scheme}://{parsed.netloc}"

        if app_config.custom_domain:
            domain = app_config.custom_domain.format(host=self._dc_host())
            return f"https://{domain}"

        if self.auth and hasattr(self.auth, "get_api_domain"):
            try:
                return self.auth.get_api_domain().rstrip("/")
            except Exception:
                pass
        return (os.getenv("ZOHO_API_DOMAIN") or "https://www.zohoapis.com").rstrip("/")

    def _build_url(
        self,
        app_config: ZohoAppConfig,
        endpoint: str,
        additional_path: Optional[str],
    ) -> str:
        """
        Build a complete API URL.

        Args:
            app_config: App configuration.
            endpoint: API endpoint path (without query string).
            additional_path: Additional path segments.
        """
        base_domain = self._base_url(app_config)
        endpoint = (endpoint or "").lstrip("/")
        had_trailing_slash = endpoint.endswith("/")

        parts = [
            app_config.api_path.strip("/"),
            (additional_path or "").strip("/"),
            endpoint.strip("/"),
        ]
        path = "/" + "/".join(part for part in parts if part)
        if had_trailing_slash and not path.endswith("/"):
            path += "/"

        safe_characters = "/-._~:@!$&'()*+,;="
        url = f"{base_domain}{quote(path, safe=safe_characters)}"
        logger.debug("Built URL: %s", url)
        return url

    def get_base_url(self, app_name: str) -> Optional[str]:
        """Return the display base URL for an app (used by discovery tools)."""
        app_config = self.registry.get_app_config(app_name)
        if not app_config:
            return None
        try:
            return f"{self._base_url(app_config)}{app_config.api_path}"
        except Exception:
            return None

    @staticmethod
    def _split_endpoint(endpoint: str) -> Tuple[str, Dict[str, str]]:
        """Split an endpoint into path and query parameters, rejecting absolute URLs."""
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError("endpoint must be a non-empty string")
        if len(endpoint) > 2048:
            raise ValueError("endpoint is too long")
        if any(ord(char) < 32 for char in endpoint):
            raise ValueError("endpoint contains control characters")

        stripped = endpoint.strip()
        if "://" in stripped or stripped.startswith("//"):
            raise ValueError("endpoint must be a relative path, not an absolute URL")

        parsed = urlsplit(stripped)
        if parsed.scheme or parsed.netloc or parsed.fragment:
            raise ValueError("endpoint must be a relative path without a fragment")
        return parsed.path, dict(parse_qsl(parsed.query, keep_blank_values=True))

    @staticmethod
    def _validate_path(value: Optional[str], label: str) -> None:
        """Reject path traversal and absolute URLs in path fragments."""
        if not value:
            return
        if "://" in value or value.startswith("//"):
            raise ValueError(f"{label} must be a relative path")
        decoded = value.replace("\\", "/")
        if ".." in decoded.split("/") or "\x00" in decoded:
            raise ValueError(f"{label} contains an invalid path segment")
        if any(ord(char) < 32 for char in value):
            raise ValueError(f"{label} contains control characters")

    @staticmethod
    def _move_org_id_to_query(
        app_name: str,
        additional_path: Optional[str],
        params: Dict[str, Any],
    ) -> Optional[str]:
        """Convert ``organization/{id}`` into the ``organization_id`` query param."""
        if not additional_path or app_name not in ORG_ID_QUERY_APPS:
            return additional_path
        match = re.fullmatch(r"organizations?/([^/]+)/?", additional_path.strip("/"))
        if match:
            org_id = match.group(1)
            if org_id.lower() not in {"none", "null", ""}:
                params.setdefault("organization_id", org_id)
            return None
        return additional_path

    def _headers_for(self, app_name: str, base_headers: Dict[str, str]) -> Dict[str, str]:
        """Add app-specific headers (Desk org, Analytics org, Creator env)."""
        headers = dict(base_headers)
        headers.setdefault("Accept", "application/json")
        headers["User-Agent"] = os.getenv(
            "ZOHO_USER_AGENT", "zoho-mcp-server/2.0 (+https://github.com/junnaisystems/zoho-crm-mcp)"
        )

        if app_name == "Desk":
            org_id = (os.getenv("ZOHO_DESK_ORG_ID") or "").strip()
            if not org_id:
                org_id = self._discover_desk_org_id(headers) or ""
            if org_id:
                headers["orgId"] = org_id

        if app_name == "Analytics":
            org_id = (
                (os.getenv("ZOHO_ANALYTICS_ORG_ID") or os.getenv("ZANALYTICS_ORGID") or "").strip()
                or self._discover_analytics_org_id(headers)
            )
            if org_id:
                headers["ZANALYTICS-ORGID"] = org_id

        if app_name == "Creator":
            environment = (os.getenv("ZOHO_CREATOR_ENVIRONMENT") or "").strip()
            if environment:
                headers["environment"] = environment

        return headers

    def _discover_analytics_org_id(self, headers: Dict[str, str]) -> Optional[str]:
        """Discover the Analytics org ID from the workspaces endpoint."""
        if self._analytics_org_id:
            return self._analytics_org_id
        app_config = self.registry.get_app_config("Analytics")
        if not app_config:
            return None
        try:
            url = f"{self._base_url(app_config)}{app_config.api_path}/workspaces"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                return None
            payload = response.json()
            data = payload.get("data", {})
            workspaces = list(data.get("ownedWorkspaces", [])) + list(
                data.get("sharedWorkspaces", [])
            )
            for workspace in workspaces:
                if workspace.get("orgId"):
                    self._analytics_org_id = str(workspace["orgId"])
                    return self._analytics_org_id
        except Exception as exc:
            logger.debug("Could not discover Analytics org id: %s", exc)
        return None

    def _discover_desk_org_id(self, headers: Dict[str, str]) -> Optional[str]:
        """Discover the Desk org ID from /organizations when the scope allows it."""
        if self._desk_org_id or self._desk_org_checked:
            return self._desk_org_id
        self._desk_org_checked = True
        app_config = self.registry.get_app_config("Desk")
        if not app_config:
            return None
        try:
            url = f"{self._base_url(app_config)}{app_config.api_path}/organizations"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                return None
            payload = response.json()
            organizations = payload.get("data", payload.get("organizations", []))
            if organizations:
                first = organizations[0]
                org_id = first.get("id") or first.get("orgId") or first.get("organization_id")
                if org_id:
                    self._desk_org_id = str(org_id)
                    return self._desk_org_id
        except Exception as exc:
            logger.debug("Could not discover Desk org id: %s", exc)
        return None

    def _discover_org_id(self, app_name: str, headers: Dict[str, str]) -> Optional[str]:
        """Discover the default organisation ID for Books/Inventory."""
        if app_name in self._org_ids:
            return self._org_ids[app_name]
        app_config = self.registry.get_app_config(app_name)
        if not app_config:
            return None
        try:
            url = f"{self._base_url(app_config)}{app_config.api_path}/organizations"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                return None
            payload = response.json()
            organizations = payload.get("organizations", payload.get("data", []))
            if organizations:
                first = organizations[0]
                org_id = (
                    first.get("organization_id")
                    or first.get("organizationId")
                    or first.get("id")
                )
                if org_id:
                    self._org_ids[app_name] = str(org_id)
                    return self._org_ids[app_name]
        except Exception as exc:
            logger.debug("Could not discover %s org id: %s", app_name, exc)
        return None

    # ------------------------------------------------------------------
    # Request execution
    # ------------------------------------------------------------------
    def _throttle(self) -> None:
        """Sleep if the configured per-minute rate limit has been reached."""
        if self.rate_limit <= 0:
            return
        now = time.monotonic()
        while self._request_times and now - self._request_times[0] >= 60:
            self._request_times.popleft()
        if len(self._request_times) >= self.rate_limit:
            sleep_for = 60 - (now - self._request_times[0])
            if sleep_for > 0:
                logger.warning("Rate limit reached; sleeping %.1fs", sleep_for)
                time.sleep(sleep_for)
        self._request_times.append(time.monotonic())

    def _execute_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Any],
        params: Optional[Dict],
        form_encoded: bool = False,
    ) -> requests.Response:
        """Execute an HTTP request."""
        logger.debug("Making %s request to %s", method, url)
        request_headers = dict(headers)
        if form_encoded:
            request_headers.pop("Content-Type", None)

        kwargs: Dict[str, Any] = {
            "headers": request_headers,
            "params": params,
            "timeout": self.timeout,
        }
        if method == "GET":
            return requests.get(url, **kwargs)
        if method == "DELETE":
            return requests.delete(url, **kwargs)
        if data is not None:
            if form_encoded:
                kwargs["data"] = data
            else:
                kwargs["json"] = data
        if method == "POST":
            return requests.post(url, **kwargs)
        if method == "PUT":
            return requests.put(url, **kwargs)
        if method == "PATCH":
            return requests.patch(url, **kwargs)
        raise ValueError(f"Unsupported HTTP method: {method}")

    def _execute_with_retries(
        self,
        app_name: str,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Any],
        params: Optional[Dict],
        form_encoded: bool,
    ) -> requests.Response:
        """Execute a request with optional 401 refresh and 429/5xx retries."""
        response: Optional[requests.Response] = None
        attempted_refresh = False
        attempts = self.max_retries + 1

        for attempt in range(attempts):
            self._throttle()
            response = self._execute_request(
                method, url, headers, data, params, form_encoded=form_encoded
            )

            if response.status_code == 401 and not attempted_refresh and self.auth:
                attempted_refresh = True
                if getattr(self.auth, "force_refresh", None) and self.auth.force_refresh():
                    headers = self._headers_for(app_name, self.auth.get_headers())
                    continue

            if response.status_code in {429, 500, 502, 503, 504} and attempt < attempts - 1:
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else 2 ** attempt
                except (TypeError, ValueError):
                    delay = 2 ** attempt
                logger.warning(
                    "Zoho %s returned %s; retrying in %.1fs",
                    app_name,
                    response.status_code,
                    min(delay, 30),
                )
                time.sleep(min(delay, 30))
                continue
            break

        assert response is not None
        return response

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def make_request(
        self,
        app_name: str,
        endpoint: str,
        method: str = "GET",
        data: Optional[Any] = None,
        params: Optional[Dict] = None,
        additional_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request to any Zoho app.

        Args:
            app_name: Name of the Zoho app (e.g. "CRM", "Books").
            endpoint: API endpoint path (e.g. "Leads", "invoices").
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            data: Request body data.
            params: Query parameters.
            additional_path: Additional path segments.
        """
        method = (method or "GET").upper()
        if method not in ALLOWED_METHODS:
            return self._handle_error(
                "invalid_method",
                {"app_name": app_name, "message": f"Unsupported HTTP method: {method}"},
            )
        if self.read_only and method != "GET":
            return self._handle_error(
                "read_only",
                {
                    "app_name": app_name,
                    "message": "This server is in read-only mode (MCP_READ_ONLY=true); write operations are blocked.",
                },
            )

        app_config = self.registry.get_app_config(app_name)
        if not app_config:
            return self._handle_error(
                "app_not_found",
                {
                    "app_name": app_name,
                    "message": f"App '{app_name}' not found in registry.",
                },
            )
        try:
            endpoint_path, endpoint_query = self._split_endpoint(endpoint)
            self._validate_path(endpoint_path, "endpoint")
            self._validate_path(additional_path, "additional_path")
        except ValueError as exc:
            return self._handle_error(
                "invalid_request", {"app_name": app_config.name, "message": str(exc)}
            )

        request_params: Dict[str, Any] = dict(endpoint_query)
        if params:
            request_params.update(params)
        additional_path = self._move_org_id_to_query(
            app_config.name, additional_path, request_params
        )

        try:
            url = self._build_url(app_config, endpoint_path, additional_path)
        except Exception as exc:
            return self._handle_error(
                "url_build_error", {"app_name": app_config.name, "error": str(exc)}
            )

        if not self.auth:
            return self._handle_error(
                "configuration",
                {
                    "app_name": app_config.name,
                    "message": (
                        "Zoho credentials are not configured. Set ZOHO_CLIENT_ID, "
                        "ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN."
                    ),
                },
            )

        try:
            headers = self._headers_for(app_config.name, self.auth.get_headers())
        except Exception as exc:
            return self._handle_error(
                "authentication",
                {"message": "Failed to get authentication headers", "error": str(exc)},
            )

        if app_config.name == "Desk" and not headers.get("orgId"):
            return self._handle_error(
                "configuration",
                {
                    "app_name": "Desk",
                    "message": (
                        "Zoho Desk requires an organisation ID. Set ZOHO_DESK_ORG_ID "
                        "to the numeric Desk org ID (Desk > Setup > Developer Space), "
                        "or grant Desk.organizations.READ so it can be discovered."
                    ),
                },
            )

        if app_config.name in {"Books", "Inventory"} and not request_params.get(
            "organization_id"
        ):
            discovered = self._discover_org_id(app_config.name, headers)
            if discovered:
                request_params["organization_id"] = discovered

        try:
            response = self._execute_with_retries(
                app_config.name,
                method,
                url,
                headers,
                data,
                request_params or None,
                form_encoded=app_config.name in FORM_ENCODED_APPS,
            )
            return self._handle_response(response, app_config.name)
        except requests.exceptions.Timeout:
            return self._handle_error(
                "timeout",
                {
                    "app_name": app_config.name,
                    "message": f"Request to {app_config.name} timed out after {self.timeout} seconds",
                },
            )
        except requests.exceptions.RequestException as exc:
            return self._handle_error(
                "network",
                {
                    "app_name": app_config.name,
                    "message": f"Network error occurred: {exc}",
                    "error": str(exc),
                },
            )
        except Exception as exc:
            return self._handle_error(
                "unexpected",
                {
                    "app_name": app_config.name,
                    "message": f"Unexpected error: {exc}",
                    "error": str(exc),
                },
            )

    # ------------------------------------------------------------------
    # Response handling
    # ------------------------------------------------------------------
    def _handle_response(self, response: requests.Response, app_name: str) -> Dict[str, Any]:
        """Standardize response format across all apps."""
        status_code = response.status_code
        request_id = None
        try:
            request_id = response.headers.get("X-Zoho-Request-Id") or response.headers.get(
                "X-Request-Id"
            )
        except Exception:
            request_id = None

        if status_code in {200, 201, 202, 204}:
            result: Dict[str, Any] = {
                "status": "success",
                "status_code": status_code,
                "app": app_name,
            }
            if isinstance(request_id, str) and request_id:
                result["request_id"] = request_id

            if status_code == 204 or not response.content:
                result["data"] = {}
                result["message"] = "Operation completed successfully"
                return result
            try:
                result["data"] = response.json()
            except ValueError:
                result["data"] = {"text": response.text}
            return result

        error_data: Dict[str, Any] = {
            "status_code": status_code,
            "app": app_name,
        }
        if isinstance(request_id, str) and request_id:
            error_data["request_id"] = request_id

        try:
            error_json = response.json()
            error_data["error"] = error_json
            error_data["message"] = self._extract_error_message(error_json)
        except ValueError:
            error_data["error"] = response.text
            error_data["message"] = response.text or f"HTTP {status_code} error"

        if status_code == 401:
            error_data["error_type"] = "authentication"
        elif status_code == 403:
            error_data["error_type"] = "authorization"
        elif status_code == 404:
            error_data["error_type"] = "not_found"
        elif status_code == 429:
            error_data["error_type"] = "rate_limit"
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    error_data["retry_after"] = int(retry_after)
                except (TypeError, ValueError):
                    pass
        elif status_code >= 500:
            error_data["error_type"] = "server_error"
        else:
            error_data["error_type"] = "api_error"

        error_data["status"] = "error"
        return error_data

    def _extract_error_message(self, error_json: Any) -> str:
        """Extract an error message from the various Zoho error formats."""
        if isinstance(error_json, dict):
            if "message" in error_json and isinstance(error_json["message"], str):
                return error_json["message"]
            if "error" in error_json:
                error = error_json["error"]
                if isinstance(error, str):
                    return error
                if isinstance(error, dict) and "message" in error:
                    return error["message"]
            if "errors" in error_json and isinstance(error_json["errors"], list):
                if error_json["errors"]:
                    first_error = error_json["errors"][0]
                    if isinstance(first_error, dict) and "message" in first_error:
                        return first_error["message"]
            if "data" in error_json:
                data = error_json["data"]
                if isinstance(data, list) and data:
                    first_item = data[0]
                    if isinstance(first_item, dict) and "message" in first_item:
                        return first_item["message"]
                if isinstance(data, dict):
                    if isinstance(data.get("errorMessage"), str):
                        return data["errorMessage"]
                    if isinstance(data.get("message"), str):
                        return data["message"]
            if "summary" in error_json and isinstance(error_json["summary"], str):
                return error_json["summary"]
        return str(error_json)

    def _handle_error(self, error_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Centralized error handling."""
        error_messages = {
            "app_disabled": "The requested Zoho app is not enabled. Check your OAuth scopes.",
            "app_not_found": "The requested Zoho app was not found in the registry.",
            "authentication": "Authentication failed. Please re-authenticate with Zoho.",
            "authorization": "Insufficient permissions for this operation. Check your OAuth scopes.",
            "rate_limit": "Rate limit exceeded. Please retry after the specified time.",
            "network": "Network error occurred. Please check your connection.",
            "timeout": "Request timed out. The server took too long to respond.",
            "api_error": "Zoho API returned an error.",
            "url_build_error": "Failed to build API URL.",
            "invalid_method": "Unsupported HTTP method.",
            "invalid_request": "The request path is invalid.",
            "read_only": "Write operations are disabled.",
            "configuration": "The server is not fully configured.",
            "unexpected": "An unexpected error occurred.",
        }
        response = {
            "status": "error",
            "error_type": error_type,
            "message": details.get("message", error_messages.get(error_type, "Unknown error")),
            "details": details,
        }
        if "retry_after" in details:
            response["retry_after"] = details["retry_after"]
        logger.error("Error (%s): %s", error_type, response["message"])
        return response

    def set_timeout(self, timeout: int) -> None:
        """Set request timeout in seconds."""
        self.timeout = int(timeout)
        logger.info("Request timeout set to %s seconds", self.timeout)
