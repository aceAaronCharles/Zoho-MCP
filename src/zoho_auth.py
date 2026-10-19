"""
Zoho OAuth Authentication Handler
Handles OAuth flow, token storage, and refresh for Zoho API access.
"""

import json
import logging
import os
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests

logger = logging.getLogger(__name__)

# Data-centre hosts used by the Zoho product domains.
DC_HOSTS = {
    "com": "zoho.com",
    "in": "zoho.in",
    "eu": "zoho.eu",
    "com.au": "zoho.com.au",
    "com.cn": "zoho.com.cn",
    "jp": "zoho.jp",
    "ca": "zohocloud.ca",
    "sa": "zoho.sa",
    "ae": "zoho.ae",
    "sg": "zoho.sg",
}


def accounts_domain_for(dc: str) -> str:
    """Return the accounts host for a data-centre suffix (e.g. ``com``)."""
    normalized = (dc or "com").strip().lower()
    return f"https://accounts.{DC_HOSTS.get(normalized, f'zoho.{normalized}')}"


def build_authorization_url(
    accounts_domain: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    prompt: str = "consent",
) -> str:
    """Build a Zoho OAuth consent URL."""
    params = {
        "scope": scope,
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "access_type": "offline",
        "prompt": prompt,
    }
    return f"{accounts_domain.rstrip('/')}/oauth/v2/auth?{urlencode(params)}"


class CallbackServer(BaseHTTPRequestHandler):
    """Simple HTTP server to handle the OAuth callback."""

    def do_GET(self):  # noqa: N802 - required by BaseHTTPRequestHandler
        """Handle GET request for OAuth callback."""
        if self.path.startswith("/callback"):
            query_params = parse_qs(urlparse(self.path).query)
            if "code" in query_params:
                self.server.auth_code = query_params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"""
                <html>
                <body>
                    <h2>Authorization Successful!</h2>
                    <p>You can now close this window and return to your application.</p>
                    <script>window.close();</script>
                </body>
                </html>
                """
                )
            elif "error" in query_params:
                self.server.auth_error = query_params["error"][0]
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                description = query_params.get("error_description", ["Unknown error"])[0]
                self.wfile.write(
                    (
                        "<html><body><h2>Authorization Failed!</h2>"
                        f"<p>Error: {description}</p></body></html>"
                    ).encode()
                )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP server logging (it writes to stderr)."""
        pass


class ZohoAuth:
    """Handles Zoho OAuth authentication and token management."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: str,
        token_file_path: str = ".zoho_tokens.json",
        api_domain: Optional[str] = None,
        accounts_domain: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        """Initialize Zoho authentication handler."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.token_file_path = token_file_path
        self.api_domain = (api_domain or os.getenv("ZOHO_API_DOMAIN") or "https://www.zohoapis.com").rstrip("/")
        self._accounts_domain_explicit = bool(accounts_domain or os.getenv("ZOHO_ACCOUNTS_DOMAIN"))
        self.accounts_domain = (accounts_domain or os.getenv("ZOHO_ACCOUNTS_DOMAIN") or "").rstrip("/")
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = refresh_token or os.getenv("ZOHO_REFRESH_TOKEN") or None
        self.token_expires_at: Optional[float] = None
        self.api_domain_for_tokens: Optional[str] = None
        self.granted_scope: str = ""

        # Load existing tokens (the file may contain a newer access token).
        self._load_tokens()

        # Derive the matching accounts host when the caller did not specify it.
        if not self._accounts_domain_explicit:
            self.accounts_domain = f"https://accounts.{self.get_data_center_host()}"

    # ------------------------------------------------------------------
    # Token storage
    # ------------------------------------------------------------------
    def _load_tokens(self) -> None:
        """Load tokens from file if they exist."""
        if not self.token_file_path or not os.path.exists(self.token_file_path):
            return
        try:
            with open(self.token_file_path, "r", encoding="utf-8") as handle:
                tokens = json.load(handle)
            self.access_token = tokens.get("access_token")
            # An explicit environment refresh token wins over the file so a
            # container can be rotated without editing the mounted file.
            self.refresh_token = self.refresh_token or tokens.get("refresh_token")
            self.token_expires_at = tokens.get("expires_at")
            self.api_domain_for_tokens = tokens.get("api_domain", self.api_domain)
            self.granted_scope = tokens.get("scope", "") or ""
            logger.info("Loaded existing tokens from %s", self.token_file_path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to load tokens: %s", exc)

    def _save_tokens(self, tokens: Dict[str, Any]) -> None:
        """Update in-memory tokens and persist to file when configured."""
        expires_in = tokens.get("expires_in", 3600)
        try:
            expires_at = time.time() + int(expires_in)
        except (TypeError, ValueError):
            expires_at = time.time() + 3600
        token_data = {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token") or self.refresh_token,
            "expires_at": expires_at,
            "api_domain": tokens.get("api_domain") or self.api_domain_for_tokens or self.api_domain,
            "token_type": tokens.get("token_type", "Bearer"),
            "scope": tokens.get("scope") or self.granted_scope or self.scope,
        }

        # Always update the in-memory state first.  This keeps callers working
        # even when there is no token file (in-memory/DB-backed auth) or the
        # filesystem is read-only, which is a valid deployment.
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.token_expires_at = token_data["expires_at"]
        self.api_domain_for_tokens = token_data["api_domain"]
        self.granted_scope = token_data["scope"] or self.granted_scope

        if not self.token_file_path:
            return

        try:
            directory = os.path.dirname(self.token_file_path) or "."
            os.makedirs(directory, exist_ok=True)

            # Write to a temporary file in the same directory, then replace it
            # so a crash cannot leave a partially written token file.
            fd, temp_path = tempfile.mkstemp(prefix=".zoho_tokens.", dir=directory, text=True)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(token_data, handle, indent=2)
                os.chmod(temp_path, 0o600)
                os.replace(temp_path, self.token_file_path)
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

            logger.info("Tokens saved successfully")
        except Exception as exc:  # pragma: no cover - depends on filesystem
            # A read-only container is a valid deployment: keep the token in
            # memory and continue rather than crashing the server.
            logger.warning("Could not persist tokens to %s: %s", self.token_file_path, exc)

    # ------------------------------------------------------------------
    # Data centre helpers
    # ------------------------------------------------------------------
    def get_data_center(self) -> str:
        """Return the Zoho data-centre suffix (com, eu, in, ca, ...)."""
        explicit = (os.getenv("ZOHO_DC") or "").strip().lower()
        if explicit:
            return explicit

        host = urlparse(self.api_domain_for_tokens or self.api_domain).hostname or ""
        if host.endswith("zohocloud.ca"):
            return "ca"
        marker = "zohoapis."
        if marker in host:
            return host.split(marker, 1)[1]
        if host.startswith("accounts."):
            suffix = host[len("accounts.") :]
            for dc, dc_host in DC_HOSTS.items():
                if suffix == dc_host:
                    return dc
        return "com"

    def get_data_center_host(self) -> str:
        """Return the product hostname suffix, e.g. ``zoho.com``."""
        dc = self.get_data_center()
        return DC_HOSTS.get(dc, f"zoho.{dc}")

    # ------------------------------------------------------------------
    # OAuth flows
    # ------------------------------------------------------------------
    def get_authorization_url(self) -> str:
        """Generate the authorization URL for OAuth flow."""
        return build_authorization_url(
            self.accounts_domain,
            self.client_id,
            self.redirect_uri,
            self.scope,
        )

    def authorize_interactive(self) -> bool:
        """Perform interactive OAuth authorization."""
        try:
            auth_url = self.get_authorization_url()
            print(f"\n{'=' * 60}", file=sys.stderr)
            print("ZOHO AUTHENTICATION REQUIRED", file=sys.stderr)
            print(f"{'=' * 60}", file=sys.stderr)
            print("Open the following URL in your browser:", file=sys.stderr)
            print(auth_url, file=sys.stderr)
            print(f"{'=' * 60}\n", file=sys.stderr)

            parsed = urlparse(self.redirect_uri)
            bind_host = parsed.hostname or "127.0.0.1"
            bind_port = parsed.port or 8080
            server = HTTPServer((bind_host, bind_port), CallbackServer)
            server.auth_code = None
            server.auth_error = None
            server.timeout = 5

            try:
                import webbrowser

                webbrowser.open(auth_url)
            except Exception:
                pass

            print("Waiting for authorization (timeout: 5 minutes)...", file=sys.stderr)
            deadline = time.time() + 300
            while time.time() < deadline:
                server.handle_request()
                if server.auth_code or server.auth_error:
                    break

            if server.auth_error:
                logger.error("Authorization failed: %s", server.auth_error)
                return False
            if not server.auth_code:
                logger.error("Authorization timed out")
                return False
            return self._exchange_code_for_tokens(server.auth_code)
        except Exception as exc:
            logger.error("Interactive authorization failed: %s", exc)
            return False

    def _exchange_code_for_tokens(self, auth_code: str) -> bool:
        """Exchange authorization code for access tokens."""
        try:
            token_url = f"{self.accounts_domain}/oauth/v2/token"
            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "code": auth_code,
            }
            response = requests.post(token_url, data=data, timeout=30)
            if response.status_code == 200:
                self._save_tokens(response.json())
                logger.info("Successfully obtained access tokens")
                return True
            logger.error("Token exchange failed: %s - %s", response.status_code, response.text[:500])
            return False
        except Exception as exc:
            logger.error("Failed to exchange code for tokens: %s", exc)
            return False

    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False

        try:
            token_url = f"{self.accounts_domain}/oauth/v2/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            response = requests.post(token_url, data=data, timeout=30)
            if response.status_code == 200:
                self._save_tokens(response.json())
                logger.info("Successfully refreshed access token")
                return True
            logger.error("Token refresh failed: %s - %s", response.status_code, response.text[:500])
            return False
        except Exception as exc:
            logger.error("Failed to refresh token: %s", exc)
            return False

    def force_refresh(self) -> bool:
        """Force a refresh even when the cached token looks valid."""
        self.token_expires_at = None
        return self.refresh_access_token()

    # ------------------------------------------------------------------
    # Token accessors
    # ------------------------------------------------------------------
    def is_token_valid(self) -> bool:
        """Check if the current access token is valid."""
        if not self.access_token or not self.token_expires_at:
            return False
        return time.time() < (self.token_expires_at - 300)

    def _interactive_allowed(self) -> bool:
        """Return True when it is safe to open an interactive browser flow."""
        setting = (os.getenv("ZOHO_INTERACTIVE_AUTH") or "auto").strip().lower()
        if setting in {"0", "false", "no", "off"}:
            return False
        if setting in {"1", "true", "yes", "on"}:
            return True
        # auto: only when a human is at a terminal (MCP stdio clients are not).
        try:
            return sys.stdin.isatty()
        except Exception:
            return False

    def get_valid_access_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary."""
        if self.is_token_valid():
            return self.access_token

        logger.info("Access token expired or invalid, attempting refresh...")
        if self.refresh_access_token():
            return self.access_token

        if self._interactive_allowed() and self.authorize_interactive():
            return self.access_token

        logger.error(
            "Failed to obtain a valid access token. Set ZOHO_REFRESH_TOKEN or "
            "run the authenticate_zoho tool interactively."
        )
        return None

    def get_api_domain(self) -> str:
        """Get the appropriate API domain for making requests."""
        return (self.api_domain_for_tokens or self.api_domain).rstrip("/")

    def get_granted_scopes(self) -> str:
        """Return the scopes granted to the current token, if known."""
        return self.granted_scope or ""

    def get_headers(self) -> Dict[str, str]:
        """Get the authorization headers for API requests."""
        token = self.get_valid_access_token()
        if not token:
            raise RuntimeError("No valid access token available")
        return {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def revoke_tokens(self) -> bool:
        """Revoke the current tokens."""
        try:
            if self.refresh_token:
                revoke_url = f"{self.accounts_domain}/oauth/v2/token/revoke"
                response = requests.post(revoke_url, data={"token": self.refresh_token}, timeout=30)
                if response.status_code != 200:
                    logger.warning("Token revocation warning: %s", response.status_code)

            self.access_token = None
            self.refresh_token = None
            self.token_expires_at = None
            self.api_domain_for_tokens = None
            self.granted_scope = ""

            if self.token_file_path and os.path.exists(self.token_file_path):
                os.remove(self.token_file_path)

            logger.info("Tokens revoked successfully")
            return True
        except Exception as exc:
            logger.error("Failed to revoke tokens: %s", exc)
            return False
