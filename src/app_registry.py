"""
Zoho App Registry
Manages configuration and availability of Zoho applications based on OAuth scopes.

The app catalog lives in :mod:`src.zoho_apps`; this module decides which apps
are enabled for the current grant.  Each application declares the hostname
template (``custom_domain``) and API path used by Zoho.  ``{host}`` is replaced
with the data-centre host for the token, for example ``zoho.com``, ``zoho.eu``
or ``zohocloud.ca``.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
import os

try:  # Support both ``import src.app_registry`` and ``python src/server.py``.
    from .scopes import expand_scopes, is_all_scopes
    from .zoho_apps import APP_CONFIGS
except ImportError:  # pragma: no cover - script mode
    from scopes import expand_scopes, is_all_scopes
    from zoho_apps import APP_CONFIGS

logger = logging.getLogger(__name__)


@dataclass
class ZohoAppConfig:
    """Configuration for a Zoho application."""

    name: str
    api_path: str
    required_scopes: List[str]
    enabled: bool
    api_version: str
    category: str
    custom_domain: Optional[str] = None
    scopes_verified: bool = True

    def to_dict(self) -> Dict:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "api_path": self.api_path,
            "enabled": self.enabled,
            "api_version": self.api_version,
            "category": self.category,
            "custom_domain": self.custom_domain,
            "domain_template": self.custom_domain,
            "scopes_verified": self.scopes_verified,
        }


# The catalog itself lives in ``zoho_apps.py`` so that the registry and the
# ``all`` scope preset are generated from the same data.
# APP_CONFIGS is re-exported here for backwards compatibility.


def _scope_matches(required_scope: str, granted_scope: str) -> bool:
    """
    Return True when *granted_scope* satisfies *required_scope*.

    Handles the common Zoho patterns:
      * exact matches (case-insensitive);
      * app-level shorthands such as ``ZohoCreator`` being satisfied by
        ``ZohoCreator.data.ALL``;
      * ``.ALL`` wildcards satisfying the more specific operations in the same
        namespace.
    """
    required = (required_scope or "").strip().lower()
    granted = (granted_scope or "").strip().lower()
    if not required or not granted:
        return False
    if required == granted:
        return True

    # A more specific granted scope satisfies an app-level required scope
    # (e.g. ZohoCreator.data.ALL satisfies ZohoCreator) and vice versa for
    # hierarchical namespaces.
    if granted.startswith(required + ".") or required.startswith(granted + "."):
        return True

    # Zoho uses both ".ALL" and ".all" depending on the product.
    if granted.endswith(".all"):
        prefix = granted[:-4]
        if required == prefix or required.startswith(prefix + "."):
            return True

    return False


class AppRegistry:
    """Registry of available Zoho applications."""

    def __init__(self, scope_string: str):
        """
        Initialize registry based on OAuth scopes.

        Args:
            scope_string: Comma-separated OAuth scope string, or ``all``.
        """
        self.scope_string = scope_string
        self.scopes: List[str] = []
        self.apps: Dict[str, ZohoAppConfig] = {}
        self.allow_all = False
        self.reload(scope_string)

    def reload(self, scope_string: str) -> None:
        """Rebuild the registry from a scope string (used after auth loads)."""
        self.scope_string = scope_string or ""
        self.allow_all = is_all_scopes(self.scope_string) or os.getenv(
            "ZOHO_ALLOW_ALL_APPS", ""
        ).strip().lower() in {"1", "true", "yes", "on"}
        self.scopes = self._parse_scopes(expand_scopes(self.scope_string))
        self.apps = {}
        self._initialize_apps()

        logger.info("App Registry initialized with %d total apps", len(self.apps))
        enabled_count = len([app for app in self.apps.values() if app.enabled])
        logger.info("Enabled apps: %d/%d", enabled_count, len(self.apps))

    def _parse_scopes(self, scope_string: str) -> List[str]:
        """Parse a scope string separated by commas and/or whitespace.

        Zoho returns token scopes as a space-separated string, while
        ``ZOHO_SCOPE`` is usually comma-separated.  Accept both.
        """
        if not scope_string:
            return []
        normalized = scope_string.replace(",", " ")
        return [scope.strip() for scope in normalized.split() if scope.strip()]

    def _check_scopes_present(self, required_scopes: List[str]) -> bool:
        """Check if all required scopes are present in the OAuth scopes."""
        if self.allow_all:
            return True
        for required_scope in required_scopes:
            if not any(_scope_matches(required_scope, granted) for granted in self.scopes):
                return False
        return True

    def _initialize_apps(self) -> None:
        """Initialize all app configurations and determine enabled status."""
        for app_name, config in APP_CONFIGS.items():
            enabled = self._check_scopes_present(config["required_scopes"])
            self.apps[app_name] = ZohoAppConfig(
                name=app_name,
                api_path=config["api_path"],
                required_scopes=config["required_scopes"],
                enabled=enabled,
                api_version=config["api_version"],
                category=config["category"],
                custom_domain=config.get("custom_domain"),
                scopes_verified=bool(config.get("scopes_verified", True)),
            )
            if enabled:
                logger.debug("App '%s' enabled", app_name)

    def get_app_config(self, app_name: str) -> Optional[ZohoAppConfig]:
        """Get configuration for a specific app."""
        # Accept case-insensitive app names for friendliness.
        if app_name in self.apps:
            return self.apps[app_name]
        for name, config in self.apps.items():
            if name.lower() == (app_name or "").lower():
                return config
        return None

    def list_enabled_apps(self) -> List[ZohoAppConfig]:
        """List all enabled applications."""
        return [app for app in self.apps.values() if app.enabled]

    def list_all_apps(self) -> List[ZohoAppConfig]:
        """List all applications (enabled and disabled)."""
        return list(self.apps.values())

    def is_app_enabled(self, app_name: str) -> bool:
        """Check if an app is enabled."""
        app = self.get_app_config(app_name)
        return app.enabled if app else False

    def missing_scopes(self, app_name: str) -> List[str]:
        """Return required scopes that the current grant does not cover."""
        config = self.get_app_config(app_name)
        if config is None or self.allow_all:
            return []
        missing: List[str] = []
        for required in config.required_scopes:
            if not any(_scope_matches(required, granted) for granted in self.scopes):
                missing.append(required)
        return missing

    def scope_report(self) -> Dict:
        """Summarise the grant and per-app scope coverage."""
        return {
            "requested": self.scope_string,
            "allow_all": self.allow_all,
            "granted_scopes": list(self.scopes),
            "apps": {
                app.name: {
                    "enabled": app.enabled,
                    "scopes_verified": app.scopes_verified,
                    "required_scopes": list(app.required_scopes),
                    "missing_scopes": self.missing_scopes(app.name),
                }
                for app in self.apps.values()
            },
        }

    def get_apps_by_category(self, category: str) -> List[ZohoAppConfig]:
        """Get all apps in a specific category."""
        return [app for app in self.apps.values() if app.category == category]

    def get_enabled_categories(self) -> List[str]:
        """Get list of categories that have at least one enabled app."""
        categories = {app.category for app in self.apps.values() if app.enabled}
        return sorted(categories)
