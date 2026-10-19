"""
Request-scoped runtime context.

The MCP tools are registered once against module-level ``api_router`` and
``app_registry`` objects.  In hosted, multi-tenant mode every request must be
served by the Zoho connection that belongs to the authenticated user.  Rather
than threading a request object through 73 tools, the HTTP middleware sets an
:class:`ActiveContext` in a :class:`contextvars.ContextVar` for the duration of
the request.  The proxies below transparently dispatch to that context, and
fall back to the process-wide defaults for single-user (stdio) mode.
"""

from contextvars import ContextVar
from typing import Any, Optional


class ActiveContext:
    """The Zoho connection serving the current request."""

    def __init__(
        self,
        router: Any,
        registry: Any,
        user: Optional[dict] = None,
        connection: Optional[dict] = None,
    ):
        self.router = router
        self.registry = registry
        self.user = user
        self.connection = connection


_active: ContextVar[Optional[ActiveContext]] = ContextVar(
    "zoho_active_context", default=None
)


def set_active_context(context: Optional[ActiveContext]):
    """Install *context* for the current task; returns a reset token."""
    return _active.set(context)


def reset_active_context(token) -> None:
    """Restore the previous context."""
    _active.reset(token)


def get_active_context() -> Optional[ActiveContext]:
    """Return the context for the current task, if any."""
    return _active.get()


class _Proxy:
    """Base class that forwards attribute access to the active object."""

    def __init__(self, default: Any):
        object.__setattr__(self, "_default", default)

    def _target(self) -> Any:
        ctx = _active.get()
        candidate = getattr(ctx, self._attr, None) if ctx else None
        return candidate if candidate is not None else self._default

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target(), name)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{type(self).__name__} -> {type(self._target()).__name__}>"


class RouterProxy(_Proxy):
    """Dispatches ``make_request``/``get_base_url`` to the active router."""

    _attr = "router"


class RegistryProxy(_Proxy):
    """Dispatches registry lookups to the active connection's registry."""

    _attr = "registry"
