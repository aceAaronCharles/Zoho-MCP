"""
Zoho MCP Server
A comprehensive Model Context Protocol server for Zoho apps.

The server always registers its tools, even before credentials are configured,
so an MCP client can discover them and receive actionable setup errors.  Only
three credentials are needed for headless use:

    ZOHO_CLIENT_ID
    ZOHO_CLIENT_SECRET
    ZOHO_REFRESH_TOKEN

Set ``ZOHO_SCOPE=all`` (the default) to expose every supported app.  Zoho
still enforces the scopes that were actually granted to the refresh token.
"""

import logging
import os
import sys
from functools import wraps
from typing import Any, Dict, List, Optional

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # pragma: no cover - older MCP releases
    from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv

try:  # Support both ``python -m src.server`` and ``python src/server.py``.
    from .api_router import APIRouter
    from .app_registry import AppRegistry
    from .apps.analytics_tools import register_analytics_tools
    from .apps.books_tools import register_books_tools
    from .apps.creator_tools import register_creator_tools
    from .apps.desk_tools import register_desk_tools
    from .apps.inventory_tools import register_inventory_tools
    from .apps.people_tools import register_people_tools
    from .apps.projects_tools import register_projects_tools
    from .apps.recruit_tools import register_recruit_tools
    from .runtime import (
        RouterProxy,
        get_active_context,
        reset_active_context,
        set_active_context,
    )
    from .scopes import expand_scopes
    from .zoho_auth import ZohoAuth, accounts_domain_for, build_authorization_url
except ImportError:  # pragma: no cover - script mode
    from api_router import APIRouter
    from app_registry import AppRegistry
    from apps.analytics_tools import register_analytics_tools
    from apps.books_tools import register_books_tools
    from apps.creator_tools import register_creator_tools
    from apps.desk_tools import register_desk_tools
    from apps.inventory_tools import register_inventory_tools
    from apps.people_tools import register_people_tools
    from apps.projects_tools import register_projects_tools
    from apps.recruit_tools import register_recruit_tools
    from runtime import (
        RouterProxy,
        get_active_context,
        reset_active_context,
        set_active_context,
    )
    from scopes import expand_scopes
    from zoho_auth import ZohoAuth, accounts_domain_for, build_authorization_url

# Load environment variables
load_dotenv()


def _configure_logging() -> None:
    """Configure logging to stderr (stdout is reserved for MCP stdio)."""
    level = getattr(logging, (os.getenv("LOG_LEVEL") or "INFO").upper(), logging.INFO)
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stderr)]

    log_file_path = (os.getenv("LOG_FILE_PATH") or "").strip()
    if log_file_path:
        try:
            log_dir = os.path.dirname(log_file_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            handlers.append(logging.FileHandler(log_file_path))
        except Exception as exc:  # pragma: no cover - depends on filesystem
            print(f"Warning: could not open log file {log_file_path}: {exc}", file=sys.stderr)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )


_configure_logging()
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "Zoho"),
    version=os.getenv("MCP_SERVER_VERSION", "2.0.0"),
    instructions=(
        "Zoho integration server. Use list_zoho_apps to discover apps, "
        "zoho_api_request for any Zoho REST endpoint, and the app-specific "
        "tools for common operations. Write access can be disabled with "
        "MCP_READ_ONLY=true."
    ),
)

# Global instances.  The registry/router exist before credentials so every
# tool can be registered and discovered; auth is filled in lazily.
#
# ``api_router`` is a proxy: in hosted multi-tenant mode the HTTP middleware
# installs the authenticated user's router in a context variable, and the proxy
# transparently dispatches tool calls to it.  Without a context (stdio mode) it
# falls back to the process-wide default connection.
auth: Optional[ZohoAuth] = None
app_registry: AppRegistry = AppRegistry(expand_scopes(os.getenv("ZOHO_SCOPE", "all")))
_default_router: APIRouter = APIRouter(None, app_registry)
api_router: RouterProxy = RouterProxy(_default_router)
_config_error: Optional[str] = None
_initialized = False
_tools_registered = False


def _active_registry() -> AppRegistry:
    """Return the registry for the current request, or the global default."""
    context = get_active_context()
    if context is not None and context.registry is not None:
        return context.registry
    return app_registry


def _missing_credentials_message() -> str:
    return (
        "Zoho credentials are not configured. Set ZOHO_CLIENT_ID, "
        "ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN (or place a token file at "
        "TOKEN_FILE_PATH). See .env.example and README.md for setup."
    )


def init_system(force: bool = False) -> bool:
    """Initialize authentication and refresh the app registry."""
    global auth, _config_error, _initialized

    if _initialized and not force:
        return auth is not None
    _initialized = True

    client_id = (os.getenv("ZOHO_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("ZOHO_CLIENT_SECRET") or "").strip()
    if not client_id or not client_secret:
        _config_error = _missing_credentials_message()
        logger.warning(_config_error)
        return False

    scope_env = (os.getenv("ZOHO_SCOPE") or "all").strip()
    try:
        new_auth = ZohoAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=os.getenv("ZOHO_REDIRECT_URI", "http://localhost:8080/callback"),
            scope=expand_scopes(scope_env),
            token_file_path=os.getenv("TOKEN_FILE_PATH", ".zoho_tokens.json"),
            api_domain=os.getenv("ZOHO_API_DOMAIN") or None,
            accounts_domain=os.getenv("ZOHO_ACCOUNTS_DOMAIN") or None,
            refresh_token=os.getenv("ZOHO_REFRESH_TOKEN") or None,
        )

        # Prefer the scopes actually granted to the token.  A refresh token
        # created outside this machine has no local token file, in which case
        # ZOHO_SCOPE (default: all) is used.
        granted = new_auth.get_granted_scopes()
        app_registry.reload(granted or expand_scopes(scope_env) or "all")
        api_router.update(new_auth, app_registry)
        auth = new_auth
        _config_error = None

        enabled = app_registry.list_enabled_apps()
        logger.info(
            "Zoho server ready: %d/%d apps enabled; data centre %s",
            len(enabled),
            len(app_registry.list_all_apps()),
            new_auth.get_data_center(),
        )
        return True
    except Exception as exc:
        _config_error = f"Failed to initialise Zoho authentication: {exc}"
        logger.error(_config_error)
        return False


def require_auth(func):
    """Decorator to ensure credentials are configured before API calls.

    When a per-user connection is active (hosted multi-tenant mode) the global
    credentials are not required; the request-scoped router already carries the
    authenticated user's connection.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if get_active_context() is None:
            if auth is None:
                init_system()
            if auth is None:
                return {
                    "status": "error",
                    "error_type": "configuration",
                    "message": _config_error or _missing_credentials_message(),
                    "setup": {
                        "required_env": [
                            "ZOHO_CLIENT_ID",
                            "ZOHO_CLIENT_SECRET",
                            "ZOHO_REFRESH_TOKEN",
                        ],
                        "optional_env": ["ZOHO_SCOPE=all", "ZOHO_DC=com"],
                        "tool": "get_configuration_status",
                    },
                }
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            logger.exception("Error in %s", func.__name__)
            return {
                "status": "error",
                "error_type": "unexpected",
                "message": f"Error in {func.__name__}: {exc}",
            }

    return wrapper


def make_api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Make an authenticated API request to Zoho CRM.

    Kept for backward compatibility; new tools should use
    ``api_router.make_request()`` directly.
    """
    return api_router.make_request(
        app_name="CRM",
        endpoint=endpoint,
        method=method,
        data=data,
        params=params,
    )


# System Management Tools

@mcp.tool()
def list_enabled_apps() -> Dict[str, Any]:
    """
    List the Zoho applications enabled for the current token.

    Returns:
        Dict containing enabled apps, grouped by category.
    """
    try:
        registry = _active_registry()
        enabled_apps = registry.list_enabled_apps()
        apps_by_category: Dict[str, List[Dict[str, Any]]] = {}
        for app in enabled_apps:
            apps_by_category.setdefault(app.category, []).append(
                {
                    "name": app.name,
                    "api_version": app.api_version,
                    "api_path": app.api_path,
                    "base_url": api_router.get_base_url(app.name),
                }
            )

        return {
            "status": "success",
            "total_enabled": len(enabled_apps),
            "total_configured": len(registry.list_all_apps()),
            "categories": list(apps_by_category.keys()),
            "apps_by_category": apps_by_category,
        }
    except Exception as exc:
        logger.error("Error listing enabled apps: %s", exc)
        return {"status": "error", "message": f"Failed to list enabled apps: {exc}"}


@mcp.tool()
def list_zoho_apps() -> Dict[str, Any]:
    """
    List every Zoho app the server knows about, including disabled apps.

    Use the returned app names with ``zoho_api_request``.  ``enabled`` means
    the current token appears to have the required scope; Zoho still performs
    the final authorisation check.  ``missing_scopes`` shows what to grant;
    call ``get_zoho_authorization_url`` to obtain a consent link.
    """
    registry = _active_registry()
    apps = []
    for app in registry.list_all_apps():
        apps.append(
            {
                "name": app.name,
                "category": app.category,
                "api_version": app.api_version,
                "api_path": app.api_path,
                "base_url": api_router.get_base_url(app.name),
                "enabled": app.enabled,
                "required_scopes": app.required_scopes,
                "missing_scopes": registry.missing_scopes(app.name),
            }
        )
    enabled_count = len([app for app in apps if app["enabled"]])
    return {
        "status": "success",
        "count": len(apps),
        "enabled_count": enabled_count,
        "granted_scopes": list(registry.scopes),
        "scope_presets": {
            "all": "every app this server knows about",
            "recommended": "validated core set for the apps with dedicated tools",
        },
        "apps": apps,
        "usage": "Call zoho_api_request(app_name='Books', endpoint='invoices', params={'organization_id': '...'})",
        "note": (
            "enabled shows whether the local scope heuristic matched. Apps marked "
            "disabled may still work when the token actually has the scope; Zoho "
            "performs the final authorisation check. To enable more apps, call "
            "get_zoho_authorization_url(scopes='all') and approve the consent, or "
            "re-authorize through the connection portal."
        ),
    }


@mcp.tool()
@require_auth
def get_zoho_authorization_url(
    scopes: str = "all",
    redirect_uri: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return a Zoho consent URL that grants additional API scopes.

    Use this when ``list_zoho_apps`` reports ``missing_scopes``.  The returned
    URL includes the client ID (never the secret); open it in a browser and
    approve access.  Hosted deployments should instead use the connection
    portal, which handles the OAuth callback automatically.

    Args:
        scopes: ``all``, ``recommended``, or an explicit comma/space list.
        redirect_uri: Override the callback registered in the Zoho API client.

    Returns:
        Dict with ``authorization_url``, the resolved scopes and instructions.
    """
    context = get_active_context()
    client_id = ""
    accounts_domain = ""
    effective_redirect = redirect_uri or ""
    current_scope = ""

    if context is not None:
        connection = context.connection or {}
        router_auth = getattr(context.router, "auth", None)
        client_id = connection.get("client_id") or getattr(router_auth, "client_id", "")
        dc = connection.get("dc") or "com"
        accounts_domain = (
            getattr(router_auth, "accounts_domain", None)
            or connection.get("accounts_domain")
            or accounts_domain_for(dc)
        )
        effective_redirect = effective_redirect or connection.get("redirect_uri", "")
        current_scope = connection.get("scopes") or "all"
    else:
        if auth is None:
            init_system()
        if auth is None:
            return {
                "status": "error",
                "error_type": "configuration",
                "message": _config_error or _missing_credentials_message(),
            }
        client_id = auth.client_id
        accounts_domain = auth.accounts_domain or accounts_domain_for(
            auth.get_data_center()
        )
        effective_redirect = effective_redirect or auth.redirect_uri
        current_scope = os.getenv("ZOHO_SCOPE", "all")

    requested = (scopes or "").strip() or current_scope
    resolved = expand_scopes(requested)
    if not resolved:
        return {
            "status": "error",
            "error_type": "invalid_request",
            "message": "No scopes resolved from the request.",
        }
    if not client_id or not effective_redirect:
        return {
            "status": "error",
            "error_type": "configuration",
            "message": "A Zoho client ID and redirect URI are required to build the consent URL.",
        }

    url = build_authorization_url(
        accounts_domain, client_id, effective_redirect, resolved
    )
    return {
        "status": "success",
        "authorization_url": url,
        "scope_preset": requested.lower()
        if requested.lower() in {"all", "recommended"}
        else "custom",
        "scopes": resolved.split(","),
        "redirect_uri": effective_redirect,
        "instructions": (
            "Open authorization_url and approve access. The connection portal "
            f"({os.getenv('PORTAL_BASE_URL', 'http://localhost:8000')}/portal) "
            "handles the callback automatically. For a local server, run "
            "authenticate_zoho(scopes='all', force=True) instead."
        ),
    }


@mcp.tool()
def get_configuration_status() -> Dict[str, Any]:
    """
    Report which configuration values are present without revealing secrets.

    Use this tool first when a Zoho call fails with a configuration error.
    """
    token_path = os.getenv("TOKEN_FILE_PATH", ".zoho_tokens.json")
    token_file_exists = bool(token_path and os.path.exists(token_path))
    registry = _active_registry()
    context = get_active_context()
    result: Dict[str, Any] = {
        "status": "success",
        "configured": auth is not None or context is not None,
        "configuration_error": _config_error,
        "credentials": {
            "ZOHO_CLIENT_ID": bool(os.getenv("ZOHO_CLIENT_ID")),
            "ZOHO_CLIENT_SECRET": bool(os.getenv("ZOHO_CLIENT_SECRET")),
            "ZOHO_REFRESH_TOKEN": bool(os.getenv("ZOHO_REFRESH_TOKEN")),
            "token_file": token_file_exists,
            "token_file_path": token_path,
        },
        "settings": {
            "ZOHO_SCOPE": os.getenv("ZOHO_SCOPE", "all"),
            "ZOHO_SCOPE_EXCLUDE": os.getenv("ZOHO_SCOPE_EXCLUDE", ""),
            "ZOHO_DC": os.getenv("ZOHO_DC", ""),
            "ZOHO_API_DOMAIN": os.getenv("ZOHO_API_DOMAIN", ""),
            "MCP_TRANSPORT": os.getenv("MCP_TRANSPORT", "stdio"),
            "MCP_READ_ONLY": os.getenv("MCP_READ_ONLY", "false"),
            "enabled_apps": len(registry.list_enabled_apps()),
            "total_apps": len(registry.list_all_apps()),
            "apps_missing_scopes": sum(
                1
                for app in registry.list_all_apps()
                if registry.missing_scopes(app.name)
            ),
            "scope_presets": ["all", "recommended"],
        },
        "next_steps": []
        if (auth is not None or context is not None)
        else ["Set ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN"],
    }
    if context is not None and context.connection:
        result["active_connection"] = {
            "source": "portal",
            "user": (context.user or {}).get("email"),
            "data_centre": context.connection.get("dc"),
            "status": context.connection.get("status"),
        }
    return result


@mcp.tool()
@require_auth
def zoho_api_request(
    app_name: str,
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    additional_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call any Zoho REST endpoint (generic passthrough).

    This is the tool to use when an app-specific tool does not exist.  It
    supports every Zoho app in the catalog and all standard HTTP methods.

    Args:
        app_name: App name from ``list_zoho_apps`` (e.g. "CRM", "Books").
        endpoint: Relative endpoint, e.g. "Leads", "invoices", "tickets".
        method: GET, POST, PUT, PATCH or DELETE.
        params: Query parameters (e.g. {"organization_id": "123"}).
        data: JSON request body.
        additional_path: Optional extra path segments.

    Examples:
        zoho_api_request("Books", "invoices", "GET", {"organization_id": "123"})
        zoho_api_request("Desk", "tickets", "GET", {"limit": 10})
        zoho_api_request("CRM", "Leads", "POST", data={"data": [{"Last_Name": "Doe"}]})
    """
    method = (method or "GET").upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        return {"status": "error", "error_type": "invalid_method", "message": f"Unsupported method: {method}"}
    if not endpoint or not isinstance(endpoint, str):
        return {"status": "error", "error_type": "invalid_request", "message": "endpoint is required"}
    if len(endpoint) > 2048:
        return {"status": "error", "error_type": "invalid_request", "message": "endpoint is too long"}
    if "://" in endpoint or endpoint.strip().startswith("//"):
        return {
            "status": "error",
            "error_type": "invalid_request",
            "message": "endpoint must be a relative Zoho path, not an absolute URL",
        }
    if any(ord(char) < 32 for char in endpoint):
        return {"status": "error", "error_type": "invalid_request", "message": "endpoint contains control characters"}

    return api_router.make_request(
        app_name=app_name,
        endpoint=endpoint,
        method=method,
        data=data,
        params=params,
        additional_path=additional_path,
    )


# Authentication Tools

@mcp.tool()
@require_auth
def authenticate_zoho(
    scopes: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Authenticate with Zoho, optionally requesting additional API scopes.

    Opens a browser window for the OAuth consent flow when needed.  Use
    ``scopes="all"`` (or ``"recommended"``) together with ``force=True`` to
    re-consent and grant more permissions; the server then reloads the app
    registry.  Hosted deployments should use the connection portal instead.

    Args:
        scopes: Scope preset (``all``, ``recommended``) or an explicit list.
        force: Re-run the browser consent flow even if the token is valid.

    Returns:
        Dict containing authentication status and user information
    """
    try:
        if get_active_context() is not None:
            if force or scopes:
                return {
                    "status": "error",
                    "error_type": "portal_managed",
                    "message": (
                        "This Zoho connection is managed by the connection "
                        "portal. Open the portal and use 'Re-authorize' to "
                        "grant additional scopes."
                    ),
                }
            # Hosted multi-tenant mode: the connection is managed by the
            # portal, so verify it with a cheap call instead of touching the
            # process-wide credentials.
            result = make_api_request("users", params={"type": "CurrentUser"})
            if result.get("status") == "success":
                user_data = (result.get("data") or {}).get("users", [{}])[0]
                return {
                    "status": "success",
                    "source": "portal",
                    "message": "Connected through the Zoho connection portal",
                    "user": {
                        "name": user_data.get("full_name"),
                        "email": user_data.get("email"),
                        "role": user_data.get("role", {}).get("name"),
                        "organization": user_data.get("org", {}).get("company_name"),
                    },
                }
            return result

        if auth is None:
            init_system(force=True)
        if auth is None:
            return {
                "status": "error",
                "error_type": "configuration",
                "message": _config_error or _missing_credentials_message(),
            }

        if force or scopes:
            expanded = expand_scopes(scopes or os.getenv("ZOHO_SCOPE", "all"))
            if not expanded:
                return {
                    "status": "error",
                    "error_type": "invalid_request",
                    "message": "No scopes resolved from the request.",
                }
            consent_auth = ZohoAuth(
                client_id=auth.client_id,
                client_secret=auth.client_secret,
                redirect_uri=auth.redirect_uri,
                scope=expanded,
                token_file_path=auth.token_file_path,
                api_domain=auth.api_domain,
                accounts_domain=auth.accounts_domain
                or accounts_domain_for(auth.get_data_center()),
                refresh_token=auth.refresh_token,
            )
            logger.info("Starting consent flow for %d scopes", len(expanded.split(",")))
            if not consent_auth.authorize_interactive():
                return {
                    "status": "error",
                    "error_type": "authentication",
                    "message": (
                        "The browser consent flow did not complete. For a "
                        "hosted deployment use the connection portal instead."
                    ),
                }
            init_system(force=True)

        token = auth.get_valid_access_token()
        if not token:
            # The user explicitly asked to authenticate, so allow the browser
            # flow even when the server normally avoids interactive auth.
            if auth.authorize_interactive():
                token = auth.get_valid_access_token()
        if not token:
            return {
                "status": "error",
                "error_type": "authentication",
                "message": (
                    "Authentication failed. Set ZOHO_REFRESH_TOKEN for headless "
                    "use, or complete the browser flow."
                ),
            }

        # Test the token with a cheap CRM call.
        result = make_api_request("users", params={"type": "CurrentUser"})

        if result['status'] == 'success':
            user_data = result['data'].get('users', [{}])[0]
            response = {
                'status': 'success',
                'message': 'Successfully authenticated with Zoho',
                'user': {
                    'name': user_data.get('full_name'),
                    'email': user_data.get('email'),
                    'role': user_data.get('role', {}).get('name'),
                    'organization': user_data.get('org', {}).get('company_name')
                },
                'enabled_apps': len(_active_registry().list_enabled_apps()),
                'total_apps': len(_active_registry().list_all_apps()),
            }
            if os.getenv("ZOHO_REFRESH_TOKEN"):
                response["warning"] = (
                    "ZOHO_REFRESH_TOKEN is set in the environment and takes "
                    "precedence over the token file. Update it with the refresh "
                    f"token from {auth.token_file_path} so the new grant is used."
                )
            return response
        else:
            return result
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return {
            'status': 'error',
            'message': f'Authentication error: {str(e)}'
        }

@mcp.tool()
@require_auth
def revoke_authentication() -> Dict[str, Any]:
    """
    Revoke Zoho CRM authentication and clear stored tokens.
    
    Returns:
        Dict containing revocation status
    """
    try:
        if get_active_context() is not None:
            return {
                "status": "error",
                "error_type": "portal_managed",
                "message": (
                    "This Zoho connection is managed by the connection portal. "
                    "Re-authorize or disconnect it from the portal instead."
                ),
            }
        success = auth.revoke_tokens()
        if success:
            return {
                'status': 'success',
                'message': 'Authentication revoked successfully'
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to revoke authentication'
            }
    except Exception as e:
        logger.error(f"Token revocation error: {e}")
        return {
            'status': 'error',
            'message': f'Error revoking authentication: {str(e)}'
        }

# Module and Metadata Tools

@mcp.tool()
@require_auth
def get_modules() -> Dict[str, Any]:
    """
    Get all available modules in Zoho CRM.
    
    Returns:
        Dict containing list of available modules and their metadata
    """
    result = make_api_request('settings/modules')
    
    if result['status'] == 'success':
        modules = result['data'].get('modules', [])
        return {
            'status': 'success',
            'count': len(modules),
            'modules': [
                {
                    'api_name': module.get('api_name'),
                    'singular_label': module.get('singular_label'),
                    'plural_label': module.get('plural_label'),
                    'module_name': module.get('module_name'),
                    'creatable': module.get('creatable'),
                    'editable': module.get('editable'),
                    'deletable': module.get('deletable'),
                    'viewable': module.get('viewable')
                }
                for module in modules
            ]
        }
    
    return result

@mcp.tool()
@require_auth
def get_module_fields(module_name: str) -> Dict[str, Any]:
    """
    Get field information for a specific module.
    
    Args:
        module_name: Name of the module (e.g., 'Leads', 'Contacts', 'Deals')
    
    Returns:
        Dict containing field information for the module
    """
    result = make_api_request(f'settings/fields?module={module_name}')
    
    if result['status'] == 'success':
        fields = result['data'].get('fields', [])
        return {
            'status': 'success',
            'module': module_name,
            'count': len(fields),
            'fields': [
                {
                    'api_name': field.get('api_name'),
                    'field_label': field.get('field_label'),
                    'data_type': field.get('data_type'),
                    'required': field.get('required'),
                    'read_only': field.get('read_only'),
                    'visible': field.get('visible'),
                    'length': field.get('length'),
                    'pick_list_values': field.get('pick_list_values', []) if field.get('data_type') == 'picklist' else None
                }
                for field in fields
            ]
        }
    
    return result

# Record Management Tools

@mcp.tool()
@require_auth
def get_records(module_name: str, page: int = 1, per_page: int = 200, sort_order: str = 'desc', sort_by: str = 'Modified_Time') -> Dict[str, Any]:
    """
    Get records from a specific module.
    
    Args:
        module_name: Name of the module (e.g., 'Leads', 'Contacts', 'Deals')
        page: Page number (default: 1)
        per_page: Records per page (default: 200, max: 200)
        sort_order: Sort order 'asc' or 'desc' (default: 'desc')
        sort_by: Field to sort by (default: 'Modified_Time')
    
    Returns:
        Dict containing records from the module
    """
    params = {
        'page': page,
        'per_page': min(per_page, 200),
        'sort_order': sort_order,
        'sort_by': sort_by
    }
    
    result = make_api_request(module_name, params=params)
    
    if result['status'] == 'success':
        data = result['data']
        records = data.get('data', [])
        info = data.get('info', {})
        
        return {
            'status': 'success',
            'module': module_name,
            'count': len(records),
            'page_info': {
                'page': info.get('page', page),
                'per_page': info.get('per_page', per_page),
                'count': info.get('count', len(records)),
                'more_records': info.get('more_records', False)
            },
            'records': records
        }
    
    return result

@mcp.tool()
@require_auth
def get_record_by_id(module_name: str, record_id: str) -> Dict[str, Any]:
    """
    Get a specific record by its ID.
    
    Args:
        module_name: Name of the module (e.g., 'Leads', 'Contacts', 'Deals')
        record_id: ID of the record to retrieve
    
    Returns:
        Dict containing the record data
    """
    result = make_api_request(f'{module_name}/{record_id}')
    
    if result['status'] == 'success':
        records = result['data'].get('data', [])
        return {
            'status': 'success',
            'module': module_name,
            'record_id': record_id,
            'record': records[0] if records else None
        }
    
    return result

@mcp.tool()
@require_auth
def search_records(module_name: str, criteria: str, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
    """
    Search for records in a specific module using criteria.
    
    Args:
        module_name: Name of the module (e.g., 'Leads', 'Contacts', 'Deals')
        criteria: Search criteria (e.g., '(Email:equals:john@example.com)')
        page: Page number (default: 1)
        per_page: Records per page (default: 200, max: 200)
    
    Returns:
        Dict containing matching records
    """
    params = {
        'criteria': criteria,
        'page': page,
        'per_page': min(per_page, 200)
    }
    
    result = make_api_request(f'{module_name}/search', params=params)
    
    if result['status'] == 'success':
        data = result['data']
        records = data.get('data', [])
        info = data.get('info', {})
        
        return {
            'status': 'success',
            'module': module_name,
            'criteria': criteria,
            'count': len(records),
            'page_info': {
                'page': info.get('page', page),
                'per_page': info.get('per_page', per_page),
                'count': info.get('count', len(records)),
                'more_records': info.get('more_records', False)
            },
            'records': records
        }
    
    return result

@mcp.tool()
@require_auth
def create_record(module_name: str, record_data: Dict[str, Any], trigger_workflow: bool = True) -> Dict[str, Any]:
    """
    Create a new record in a specific module.
    
    Args:
        module_name: Name of the module (e.g., 'Leads', 'Contacts', 'Deals')
        record_data: Dictionary containing the record fields and values
        trigger_workflow: Whether to trigger workflows (default: True)
    
    Returns:
        Dict containing the created record information
    """
    data = {'data': [record_data]}
    params = {}
    
    if trigger_workflow:
        params['trigger'] = 'workflow'
    
    result = make_api_request(module_name, method='POST', data=data, params=params)
    
    if result['status'] == 'success':
        created_records = result['data'].get('data', [])
        return {
            'status': 'success',
            'module': module_name,
            'message': 'Record created successfully',
            'created_record': created_records[0] if created_records else None
        }
    
    return result

@mcp.tool()
@require_auth
def update_record(module_name: str, record_id: str, record_data: Dict[str, Any], trigger_workflow: bool = True) -> Dict[str, Any]:
    """
    Update an existing record in a specific module.
    
    Args:
        module_name: Name of the module (e.g., 'Leads', 'Contacts', 'Deals')
        record_id: ID of the record to update
        record_data: Dictionary containing the fields to update and their new values
        trigger_workflow: Whether to trigger workflows (default: True)
    
    Returns:
        Dict containing the update result
    """
    # Add the record ID to the data
    record_data['id'] = record_id
    
    data = {'data': [record_data]}
    params = {}
    
    if trigger_workflow:
        params['trigger'] = 'workflow'
    
    result = make_api_request(f'{module_name}/{record_id}', method='PUT', data=data, params=params)
    
    if result['status'] == 'success':
        updated_records = result['data'].get('data', [])
        return {
            'status': 'success',
            'module': module_name,
            'record_id': record_id,
            'message': 'Record updated successfully',
            'updated_record': updated_records[0] if updated_records else None
        }
    
    return result

@mcp.tool()
@require_auth
def delete_record(module_name: str, record_id: str) -> Dict[str, Any]:
    """
    Delete a record from a specific module.
    
    Args:
        module_name: Name of the module (e.g., 'Leads', 'Contacts', 'Deals')
        record_id: ID of the record to delete
    
    Returns:
        Dict containing the deletion result
    """
    result = make_api_request(f'{module_name}/{record_id}', method='DELETE')
    
    if result['status'] == 'success':
        deleted_records = result['data'].get('data', [])
        return {
            'status': 'success',
            'module': module_name,
            'record_id': record_id,
            'message': 'Record deleted successfully',
            'deleted_record': deleted_records[0] if deleted_records else None
        }
    
    return result

@mcp.tool()
@require_auth
def bulk_create_records(module_name: str, records_data: List[Dict[str, Any]], trigger_workflow: bool = True) -> Dict[str, Any]:
    """
    Create multiple records in a specific module (bulk operation).
    
    Args:
        module_name: Name of the module (e.g., 'Leads', 'Contacts', 'Deals')
        records_data: List of dictionaries containing record data (max 100 records)
        trigger_workflow: Whether to trigger workflows (default: True)
    
    Returns:
        Dict containing the bulk creation results
    """
    if len(records_data) > 100:
        return {
            'status': 'error',
            'message': 'Maximum 100 records allowed per bulk operation'
        }
    
    data = {'data': records_data}
    params = {}
    
    if trigger_workflow:
        params['trigger'] = 'workflow'
    
    result = make_api_request(module_name, method='POST', data=data, params=params)
    
    if result['status'] == 'success':
        created_records = result['data'].get('data', [])
        return {
            'status': 'success',
            'module': module_name,
            'message': f'{len(created_records)} records created successfully',
            'created_records': created_records
        }
    
    return result

# Relationship and Association Tools

@mcp.tool()
@require_auth
def get_related_records(module_name: str, record_id: str, related_module: str, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
    """
    Get related records for a specific record.
    
    Args:
        module_name: Name of the parent module (e.g., 'Accounts')
        record_id: ID of the parent record
        related_module: Name of the related module (e.g., 'Contacts', 'Deals')
        page: Page number (default: 1)
        per_page: Records per page (default: 200, max: 200)
    
    Returns:
        Dict containing related records
    """
    params = {
        'page': page,
        'per_page': min(per_page, 200)
    }
    
    result = make_api_request(f'{module_name}/{record_id}/{related_module}', params=params)
    
    if result['status'] == 'success':
        data = result['data']
        records = data.get('data', [])
        info = data.get('info', {})
        
        return {
            'status': 'success',
            'module': module_name,
            'record_id': record_id,
            'related_module': related_module,
            'count': len(records),
            'page_info': {
                'page': info.get('page', page),
                'per_page': info.get('per_page', per_page),
                'count': info.get('count', len(records)),
                'more_records': info.get('more_records', False)
            },
            'related_records': records
        }
    
    return result

# Dashboard and Analytics Tools

@mcp.tool()
@require_auth
def get_organization_info() -> Dict[str, Any]:
    """
    Get information about the Zoho CRM organization.
    
    Returns:
        Dict containing organization information
    """
    result = make_api_request('org')
    
    if result['status'] == 'success':
        org_data = result['data'].get('org', [{}])[0]
        return {
            'status': 'success',
            'organization': {
                'company_name': org_data.get('company_name'),
                'org_id': org_data.get('id'),
                'primary_email': org_data.get('primary_email'),
                'website': org_data.get('website'),
                'phone': org_data.get('phone'),
                'country': org_data.get('country'),
                'time_zone': org_data.get('time_zone'),
                'currency': org_data.get('currency'),
                'mc_status': org_data.get('mc_status'),
                'gapps_enabled': org_data.get('gapps_enabled')
            }
        }
    
    return result

@mcp.tool()
@require_auth
def get_users(type_filter: str = 'AllUsers') -> Dict[str, Any]:
    """
    Get information about CRM users.
    
    Args:
        type_filter: Type of users to retrieve ('AllUsers', 'ActiveUsers', 'DeactiveUsers', 'ConfirmedUsers', 'NotConfirmedUsers', 'DeletedUsers', 'ActiveConfirmedUsers', 'AdminUsers', 'ActiveConfirmedAdmins')
    
    Returns:
        Dict containing user information
    """
    params = {'type': type_filter}
    result = make_api_request('users', params=params)
    
    if result['status'] == 'success':
        users = result['data'].get('users', [])
        return {
            'status': 'success',
            'type_filter': type_filter,
            'count': len(users),
            'users': [
                {
                    'id': user.get('id'),
                    'full_name': user.get('full_name'),
                    'email': user.get('email'),
                    'role': user.get('role', {}).get('name'),
                    'profile': user.get('profile', {}).get('name'),
                    'status': user.get('status'),
                    'created_time': user.get('created_time'),
                    'modified_time': user.get('modified_time')
                }
                for user in users
            ]
        }
    
    return result

# Utility Tools

@mcp.tool()
@require_auth
def convert_lead(lead_id: str, convert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a lead to Account, Contact, and optionally Deal.
    
    Args:
        lead_id: ID of the lead to convert
        convert_data: Dictionary containing conversion data with keys:
                     - overwrite: boolean (optional)
                     - notify_lead_owner: boolean (optional) 
                     - notify_new_entity_owner: boolean (optional)
                     - Accounts: dict with account data (optional)
                     - Contacts: dict with contact data (optional)
                     - Deals: dict with deal data (optional)
    
    Returns:
        Dict containing the conversion result
    """
    data = {'data': [convert_data]}
    
    result = make_api_request(f'Leads/{lead_id}/actions/convert', method='POST', data=data)
    
    if result['status'] == 'success':
        conversion_data = result['data'].get('data', [{}])[0]
        return {
            'status': 'success',
            'lead_id': lead_id,
            'message': 'Lead converted successfully',
            'conversion_result': conversion_data
        }
    
    return result

@mcp.tool() 
@require_auth
def get_record_count(module_name: str, criteria: str = None) -> Dict[str, Any]:
    """
    Get the count of records in a module, optionally with search criteria.
    
    Args:
        module_name: Name of the module (e.g., 'Leads', 'Contacts', 'Deals')
        criteria: Optional search criteria to filter records
    
    Returns:
        Dict containing the record count
    """
    endpoint = f'{module_name}/actions/count'
    params = {}
    
    if criteria:
        params['criteria'] = criteria
    
    result = make_api_request(endpoint, params=params)
    
    if result['status'] == 'success':
        count_data = result['data']
        return {
            'status': 'success',
            'module': module_name,
            'criteria': criteria,
            'count': count_data.get('count', 0)
        }
    
    return result

# ---------------------------------------------------------------------------
# Tool registration and entry points
# ---------------------------------------------------------------------------

def _register_tools() -> None:
    """Register every tool exactly once, even before credentials exist."""
    global _tools_registered
    if _tools_registered:
        return
    for register in (
        register_books_tools,
        register_projects_tools,
        register_desk_tools,
        register_people_tools,
        register_recruit_tools,
        register_inventory_tools,
        register_analytics_tools,
        register_creator_tools,
    ):
        try:
            register(mcp, api_router, app_registry)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to register %s: %s", register.__name__, exc)
    _tools_registered = True
    logger.info("All Zoho MCP tools registered")


def _build_portal():
    """Create the multi-tenant connection portal when enabled."""
    try:
        from .portal import crypto as portal_crypto
        from .portal.app import Portal
        from .portal.config import PortalConfig
        from .portal.connections import ConnectionManager
        from .portal.db import Database
        from .portal.oidc import OIDCClient
    except ImportError:  # pragma: no cover - script mode
        from portal import crypto as portal_crypto
        from portal.app import Portal
        from portal.config import PortalConfig
        from portal.connections import ConnectionManager
        from portal.db import Database
        from portal.oidc import OIDCClient

    config = PortalConfig.from_env()
    if not config.enabled:
        return None

    if not portal_crypto.is_configured():
        raise SystemExit(
            "PORTAL_ENABLED=true requires MCP_SECRET_KEY to encrypt stored Zoho "
            "credentials. Generate one with: "
            "python -c \"import secrets;print(secrets.token_urlsafe(48))\""
        )
    if not config.session_secret:
        raise SystemExit("The portal needs PORTAL_SESSION_SECRET or MCP_SECRET_KEY.")

    store = Database(config.db_path)
    store.init_schema()
    manager = ConnectionManager(store)

    oidc = None
    if config.oidc_configured():
        oidc = OIDCClient(
            issuer=config.oidc_issuer,
            client_id=config.oidc_client_id,
            client_secret=config.oidc_client_secret,
            redirect_uri=config.oidc_redirect_uri,
            scopes=config.oidc_scopes,
        )
    elif not config.allow_dev_login:
        raise SystemExit(
            "The portal needs an identity provider (PORTAL_OIDC_ISSUER, "
            "PORTAL_OIDC_CLIENT_ID, PORTAL_OIDC_CLIENT_SECRET) or "
            "PORTAL_DEV_LOGIN=true for local testing."
        )

    logger.info(
        "Connection portal enabled at %s (identity provider: %s)",
        config.base_url,
        config.oidc_provider_name if oidc else "dev-login",
    )
    return Portal(config, store, manager, oidc)


def _transport_security():
    """Build DNS-rebinding protection settings from the environment.

    ``MCP_ALLOWED_HOSTS`` / ``MCP_ALLOWED_ORIGINS`` are comma-separated lists
    (``host:port`` patterns accept ``:*``).  When neither is set the SDK's
    default applies (protection on for loopback binds, off otherwise).
    """
    hosts = [h.strip() for h in (os.getenv("MCP_ALLOWED_HOSTS") or "").split(",") if h.strip()]
    origins = [
        o.strip() for o in (os.getenv("MCP_ALLOWED_ORIGINS") or "").split(",") if o.strip()
    ]
    if not hosts and not origins:
        return None
    try:
        from mcp.server.transport_security import TransportSecuritySettings
    except ImportError:  # pragma: no cover - older SDK without the class
        logger.warning("MCP_ALLOWED_HOSTS is set but this MCP version has no transport security settings")
        return None
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def _build_http_app():
    """Build the combined Starlette app (MCP transport + optional portal).

    Returns ``(app, host, port, path, portal)``.  Kept separate from
    :func:`_run_http` so the app can be exercised without binding a socket.
    """
    import hmac

    from starlette.responses import JSONResponse
    from starlette.routing import Route

    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    path = os.getenv("MCP_HTTP_PATH", "/mcp")
    json_response = (os.getenv("MCP_HTTP_JSON_RESPONSE", "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    app = mcp.streamable_http_app(
        streamable_http_path=path,
        host=host,
        json_response=json_response,
        transport_security=_transport_security(),
    )

    portal = _build_portal()

    async def health(_request):
        payload = {"status": "ok", "server": os.getenv("MCP_SERVER_NAME", "Zoho")}
        if portal is not None:
            payload["portal"] = f"{portal.config.base_url}/portal"
        return JSONResponse(payload)

    app.router.routes.append(Route("/health", health))

    if portal is not None:
        for route in portal.routes():
            app.router.routes.append(route)

    try:
        from .portal.app import BearerError
    except ImportError:  # pragma: no cover - script mode
        from portal.app import BearerError

    token = (os.getenv("MCP_HTTP_TOKEN") or "").strip()
    mcp_prefix = path.rstrip("/")

    def _is_mcp_path(request_path: str) -> bool:
        if mcp_prefix in ("", "/"):
            return request_path == "/"
        return request_path == mcp_prefix or request_path.startswith(mcp_prefix + "/")

    def _signature_matches(presented: str, expected: str) -> bool:
        try:
            return hmac.compare_digest(presented, expected)
        except TypeError:  # non-ASCII input
            return False

    def _bind_principal(scope, presented, principal: str):
        """Attach an MCP-authenticated principal so sessions bind to the caller.

        The streamable-HTTP manager refuses to serve an existing session to a
        different credential, so giving it the caller's identity stops one
        client from reusing a session created by another account.  Older SDK
        builds without these types simply skip the binding.
        """
        try:
            from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
            from mcp.server.auth.provider import AccessToken
        except ImportError:  # pragma: no cover - older SDK
            return scope
        access = AccessToken(
            token=presented, client_id=principal, scopes=[], subject=principal
        )
        bound = dict(scope)
        bound["user"] = AuthenticatedUser(access)
        return bound

    class MCPAuthMiddleware:
        """Resolve the caller's Zoho connection for the MCP endpoint."""

        def __init__(self, inner_app):
            self.inner_app = inner_app

        async def _reject(self, scope, receive, send, message: str, status: int):
            response = JSONResponse({"error": message}, status_code=status)
            await response(scope, receive, send)

        async def __call__(self, scope, receive, send):
            if scope.get("type") != "http":
                await self.inner_app(scope, receive, send)
                return
            request_path = scope.get("path", "")
            if not _is_mcp_path(request_path):
                # Portal pages and health check use their own controls.
                await self.inner_app(scope, receive, send)
                return

            headers = {
                key.decode("latin-1").lower(): value.decode("latin-1")
                for key, value in scope.get("headers", [])
            }
            authorization = headers.get("authorization", "")
            if not authorization.lower().startswith("bearer "):
                await self._reject(scope, receive, send, "unauthorized", 401)
                return
            presented = authorization[7:].strip()

            # A configured shared token maps to the process-wide env connection.
            if token and _signature_matches(presented, token):
                await self.inner_app(
                    _bind_principal(scope, presented, "shared-token"), receive, send
                )
                return
            if portal is None:
                await self._reject(scope, receive, send, "unauthorized", 401)
                return

            try:
                context = portal.resolve_bearer(presented)
            except BearerError as exc:
                await self._reject(scope, receive, send, exc.message, exc.status_code)
                return

            principal = f"portal-user-{(context.user or {}).get('id')}"
            ctx_token = set_active_context(context)
            try:
                await self.inner_app(
                    _bind_principal(scope, presented, principal), receive, send
                )
            finally:
                reset_active_context(ctx_token)

    if portal is not None or token:
        app.add_middleware(MCPAuthMiddleware)
    elif host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit(
            "Refusing to bind the HTTP transport to a non-loopback address without "
            "MCP_HTTP_TOKEN or the connection portal. Set MCP_HTTP_TOKEN, enable "
            "PORTAL_ENABLED=true, or bind to 127.0.0.1 behind a proxy."
        )

    return app, host, port, path, portal


def _run_http() -> None:
    """Run the streamable HTTP transport."""
    import uvicorn

    app, host, port, path, _portal = _build_http_app()
    logger.info("Starting streamable HTTP transport on %s:%s%s", host, port, path)
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=(os.getenv("LOG_LEVEL") or "info").lower(),
    )


def main() -> None:
    """Console entry point."""
    _register_tools()
    init_system()

    transport = (os.getenv("MCP_TRANSPORT") or "stdio").strip().lower()
    if transport in {"http", "streamable-http", "streamable_http"}:
        _run_http()
    elif transport in {"sse"}:
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


# Register tools and load credentials on import.  Failures are non-fatal so a
# client can still discover tools and call get_configuration_status.
_register_tools()
try:
    init_system()
except Exception as exc:  # pragma: no cover - defensive
    logger.error("Failed to initialise Zoho system: %s", exc)


if __name__ == "__main__":
    main()