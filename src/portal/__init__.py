"""Multi-tenant Zoho connection portal.

This package adds an OIDC-protected setup interface where each user connects
their own Zoho account (bringing their own client ID/secret), stores the
resulting refresh token encrypted in SQLite, and receives a per-user API key
for MCP clients.
"""

from .config import PortalConfig

__all__ = ["PortalConfig"]
