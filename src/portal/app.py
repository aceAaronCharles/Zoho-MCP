"""
HTTP routes for the multi-tenant Zoho connection portal.

The portal is mounted on the same Starlette application as the MCP transport.
Pages are protected by an OIDC-backed signed session cookie; the MCP endpoint
itself is protected by per-user API keys (see :meth:`Portal.resolve_bearer`).
"""

import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from starlette.concurrency import run_in_threadpool
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.routing import Route

from . import connections as conn_helpers
from . import security, ui
from .config import PortalConfig
from .crypto import CryptoError
from .db import Database
from .connections import ConnectionManager
from .oidc import OIDCClient, OIDCError

try:  # Support both ``src.portal`` and top-level ``portal`` imports.
    from ..runtime import ActiveContext
except ImportError:  # pragma: no cover - script mode
    from runtime import ActiveContext

logger = logging.getLogger(__name__)

SESSION_COOKIE = "zoho_portal_session"
OIDC_COOKIE = "zoho_portal_oidc"


class BearerError(Exception):
    """Raised when a bearer token cannot be mapped to a Zoho connection."""

    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class Portal:
    def __init__(
        self,
        config: PortalConfig,
        store: Database,
        manager: ConnectionManager,
        oidc: Optional[OIDCClient] = None,
    ):
        self.config = config
        self.store = store
        self.manager = manager
        self.oidc = oidc

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------
    def _set_session(self, response, user_id: int) -> None:
        value = security.sign_session(
            {"uid": user_id}, self.config.session_secret, self.config.session_ttl
        )
        response.set_cookie(
            SESSION_COOKIE,
            value,
            max_age=self.config.session_ttl,
            httponly=True,
            secure=self.config.cookie_secure,
            samesite="lax",
            path="/",
        )

    def _clear_session(self, response) -> None:
        response.delete_cookie(SESSION_COOKIE, path="/")

    def _current_user(self, request) -> Optional[Dict[str, Any]]:
        data = security.verify_session(
            request.cookies.get(SESSION_COOKIE), self.config.session_secret
        )
        if not data or "uid" not in data:
            return None
        return self.store.get_user(int(data["uid"]))

    def _origin_ok(self, request) -> bool:
        origin = request.headers.get("origin")
        if not origin:
            return True
        return origin.rstrip("/") == self.config.base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Bearer resolution (used by the MCP middleware)
    # ------------------------------------------------------------------
    def resolve_bearer(self, token: str) -> ActiveContext:
        """Map an MCP API key to the owner's Zoho connection context."""
        record = self.store.find_api_key(security.hash_api_key(token))
        if not record:
            raise BearerError("Invalid or revoked API key")
        user = self.store.get_user(record["user_id"])
        if not user:
            raise BearerError("API key owner no longer exists")
        try:
            context = self.manager.context_for_user(user)
        except CryptoError as exc:
            raise BearerError(str(exc), status_code=500) from exc
        if context is None:
            raise BearerError(
                "No Zoho connection is configured for this account. "
                f"Finish setup at {self.config.base_url}/portal",
                status_code=409,
            )
        return context

    # ------------------------------------------------------------------
    # Route table
    # ------------------------------------------------------------------
    def routes(self) -> List[Route]:
        return [
            Route("/", self._root, methods=["GET"]),
            Route("/portal", self.portal_home, methods=["GET"]),
            Route("/portal/login", self.login_page, methods=["GET"]),
            Route("/portal/login/start", self.login_start, methods=["GET"]),
            Route("/portal/auth/callback", self.auth_callback, methods=["GET"]),
            Route("/portal/logout", self.logout, methods=["GET", "POST"]),
            Route("/portal/dev-login", self.dev_login, methods=["POST"]),
            Route("/portal/connections/new", self.new_connection, methods=["GET", "POST"]),
            Route("/portal/connections", self.create_connection, methods=["POST"]),
            Route("/portal/connections/authorize", self.authorize, methods=["GET", "POST"]),
            Route("/portal/connections/test", self.test_connection, methods=["POST"]),
            Route("/portal/connections/delete", self.delete_connection, methods=["POST"]),
            Route("/portal/keys", self.create_key, methods=["POST"]),
            Route("/portal/keys/{key_id}/revoke", self.revoke_key, methods=["POST"]),
            Route("/oauth/zoho/callback", self.zoho_callback, methods=["GET"]),
        ]

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    async def _root(self, request):
        return RedirectResponse("/portal", status_code=303)

    async def portal_home(self, request):
        user = self._current_user(request)
        if not user:
            return RedirectResponse("/portal/login", status_code=303)
        error = request.query_params.get("err", "")
        try:
            connection = await run_in_threadpool(
                self.store.get_connection_for_user, user["id"]
            )
        except CryptoError as exc:
            connection = None
            error = str(exc)
        keys = await run_in_threadpool(self.store.list_api_keys, user["id"])
        return HTMLResponse(
            ui.dashboard(
                self.config,
                user,
                connection,
                keys,
                message=request.query_params.get("msg", ""),
                error=error,
            )
        )

    async def login_page(self, request):
        return HTMLResponse(ui.login(self.config, request.query_params.get("error", "")))

    async def login_start(self, request):
        if not self.oidc:
            return RedirectResponse(
                "/portal/login?" + urlencode({"error": "Identity provider is not configured"}),
                status_code=303,
            )
        state = security.random_token()
        nonce = security.random_token()
        verifier = OIDCClient.new_pkce_verifier()
        try:
            url = await run_in_threadpool(
                self.oidc.build_authorization_url, state, nonce, verifier
            )
        except OIDCError as exc:
            return RedirectResponse(
                "/portal/login?" + urlencode({"error": str(exc)}), status_code=303
            )
        response = RedirectResponse(url, status_code=303)
        response.set_cookie(
            OIDC_COOKIE,
            security.sign_session(
                {"state": state, "nonce": nonce, "verifier": verifier},
                self.config.session_secret,
                600,
            ),
            max_age=600,
            httponly=True,
            secure=self.config.cookie_secure,
            samesite="lax",
            path="/",
        )
        return response

    async def auth_callback(self, request):
        params = request.query_params
        if params.get("error"):
            return HTMLResponse(
                ui.message_page(
                    "Sign-in failed",
                    params.get("error_description") or params.get("error") or "Unknown error",
                ),
                status_code=400,
            )
        code = params.get("code")
        state = params.get("state")
        pending = security.verify_session(
            request.cookies.get(OIDC_COOKIE), self.config.session_secret
        )
        if not code or not pending or pending.get("state") != state:
            return HTMLResponse(
                ui.message_page("Sign-in failed", "The sign-in response was invalid or expired."),
                status_code=400,
            )
        try:
            tokens = await run_in_threadpool(
                self.oidc.exchange_code, code, pending.get("verifier", "")
            )
            profile = await run_in_threadpool(
                self.oidc.userinfo, tokens.get("access_token", "")
            )
        except OIDCError as exc:
            return HTMLResponse(
                ui.message_page("Sign-in failed", str(exc)), status_code=400
            )

        subject = profile.get("sub") or profile.get("email")
        if not subject:
            return HTMLResponse(
                ui.message_page("Sign-in failed", "The identity provider returned no subject."),
                status_code=400,
            )
        user = await run_in_threadpool(
            self.store.upsert_user,
            "oidc",
            subject,
            profile.get("email"),
            profile.get("name") or profile.get("preferred_username"),
            profile.get("picture"),
        )
        response = RedirectResponse("/portal", status_code=303)
        self._set_session(response, user["id"])
        response.delete_cookie(OIDC_COOKIE, path="/")
        return response

    async def dev_login(self, request):
        if not self.config.allow_dev_login:
            return JSONResponse({"error": "not_found"}, status_code=404)
        form = await request.form()
        email = (form.get("email") or "").strip()
        if not email:
            return RedirectResponse(
                "/portal/login?" + urlencode({"error": "Email is required"}), status_code=303
            )
        user = await run_in_threadpool(
            self.store.upsert_user, "dev", email.lower(), email, email.split("@")[0]
        )
        response = RedirectResponse("/portal", status_code=303)
        self._set_session(response, user["id"])
        return response

    async def logout(self, request):
        response = RedirectResponse("/portal/login", status_code=303)
        self._clear_session(response)
        return response

    async def new_connection(self, request):
        user = self._current_user(request)
        if not user:
            return RedirectResponse("/portal/login", status_code=303)
        existing = await run_in_threadpool(
            self.store.get_connection_for_user, user["id"]
        )
        error = request.query_params.get("err", "")
        return HTMLResponse(ui.new_connection(self.config, existing, error))

    async def create_connection(self, request):
        user = self._current_user(request)
        if not user:
            return RedirectResponse("/portal/login", status_code=303)
        if not self._origin_ok(request):
            return HTMLResponse(ui.message_page("Blocked", "Cross-origin request rejected."), status_code=403)

        form = await request.form()
        client_id = (form.get("client_id") or "").strip()
        client_secret = (form.get("client_secret") or "").strip()
        dc = conn_helpers.normalize_dc(form.get("dc"))
        scopes = (form.get("scopes") or "all").strip() or "all"

        existing = await run_in_threadpool(
            self.store.get_connection_for_user, user["id"]
        )
        if not client_secret and existing:
            client_secret = existing.get("client_secret") or ""
        if not client_id or not client_secret:
            return RedirectResponse(
                "/portal/connections/new?"
                + urlencode({"err": "Client ID and client secret are required"}),
                status_code=303,
            )

        await run_in_threadpool(
            self.store.create_connection,
            user["id"],
            client_id,
            client_secret,
            dc,
            scopes,
            self.config.zoho_redirect_uri,
        )
        return RedirectResponse("/portal/connections/authorize", status_code=303)

    async def authorize(self, request):
        user = self._current_user(request)
        if not user:
            return RedirectResponse("/portal/login", status_code=303)
        connection = await run_in_threadpool(
            self.store.get_connection_for_user, user["id"]
        )
        if not connection:
            return RedirectResponse("/portal/connections/new", status_code=303)

        state = security.random_token()
        await run_in_threadpool(
            self.store.create_state, state, user["id"], connection["id"]
        )
        url = conn_helpers.authorization_url(connection, self.config.zoho_redirect_uri)
        return RedirectResponse(url, status_code=303)

    async def zoho_callback(self, request):
        params = request.query_params
        state = params.get("state")
        record = (
            await run_in_threadpool(self.store.consume_state, state) if state else None
        )
        if not record:
            return HTMLResponse(
                ui.message_page(
                    "Connection failed",
                    "The authorization response was invalid or expired. Start again from the portal.",
                ),
                status_code=400,
            )
        connection = await run_in_threadpool(
            self.store.get_connection, record["connection_id"]
        )
        if not connection:
            return HTMLResponse(
                ui.message_page("Connection failed", "The connection no longer exists."),
                status_code=400,
            )

        if params.get("error"):
            message = params.get("error_description") or params.get("error")
            await run_in_threadpool(
                self.store.set_connection_status, connection["id"], "error", message
            )
            return RedirectResponse(
                "/portal?" + urlencode({"err": f"Zoho authorization failed: {message}"}),
                status_code=303,
            )

        code = params.get("code")
        if not code:
            return HTMLResponse(
                ui.message_page("Connection failed", "Zoho did not return an authorization code."),
                status_code=400,
            )

        try:
            tokens = await run_in_threadpool(
                conn_helpers.exchange_code,
                connection,
                code,
                self.config.zoho_redirect_uri,
            )
        except Exception as exc:
            await run_in_threadpool(
                self.store.set_connection_status, connection["id"], "error", str(exc)
            )
            return RedirectResponse(
                "/portal?" + urlencode({"err": f"Token exchange failed: {exc}"}),
                status_code=303,
            )

        expires_at = time.time() + int(tokens.get("expires_in", 3600) or 3600)
        api_domain = tokens.get("api_domain") or conn_helpers.api_domain_for(connection["dc"])
        accounts_domain = conn_helpers.accounts_domain_for(connection["dc"])
        await run_in_threadpool(
            self.store.store_tokens,
            connection["id"],
            tokens,
            expires_at,
            tokens.get("scope"),
            api_domain,
            accounts_domain,
        )
        self.manager.invalidate(connection["id"])
        return RedirectResponse(
            "/portal?" + urlencode({"msg": "Zoho account connected successfully."}),
            status_code=303,
        )

    async def test_connection(self, request):
        user = self._current_user(request)
        if not user:
            return RedirectResponse("/portal/login", status_code=303)
        if not self._origin_ok(request):
            return HTMLResponse(ui.message_page("Blocked", "Cross-origin request rejected."), status_code=403)
        connection = await run_in_threadpool(
            self.store.get_connection_for_user, user["id"]
        )
        if not connection:
            return RedirectResponse(
                "/portal?" + urlencode({"err": "No connection to test."}), status_code=303
            )

        def _run_test():
            context = self.manager.context_for_connection(connection, user)
            return context.router.make_request(
                app_name="CRM", endpoint="users", params={"type": "CurrentUser"}
            )

        result = await run_in_threadpool(_run_test)
        if result.get("status") == "success":
            users = (result.get("data") or {}).get("users") or [{}]
            name = users[0].get("full_name") or users[0].get("email") or "your Zoho account"
            return RedirectResponse(
                "/portal?" + urlencode({"msg": f"Connection works — signed in as {name}."}),
                status_code=303,
            )
        message = result.get("message") or "The test request failed."
        return RedirectResponse(
            "/portal?" + urlencode({"err": f"Connection test failed: {message}"}),
            status_code=303,
        )

    async def delete_connection(self, request):
        user = self._current_user(request)
        if not user:
            return RedirectResponse("/portal/login", status_code=303)
        if not self._origin_ok(request):
            return HTMLResponse(ui.message_page("Blocked", "Cross-origin request rejected."), status_code=403)
        connection = await run_in_threadpool(
            self.store.get_connection_for_user, user["id"]
        )
        if connection:
            def _revoke():
                try:
                    auth = conn_helpers.ConnectionAuth(connection, self.store)
                    auth.revoke_tokens()
                except Exception as exc:  # pragma: no cover - best effort
                    logger.warning("Token revocation failed: %s", exc)

            await run_in_threadpool(_revoke)
            await run_in_threadpool(
                self.store.delete_connection, connection["id"], user["id"]
            )
            self.manager.invalidate(connection["id"])
        return RedirectResponse(
            "/portal?" + urlencode({"msg": "Connection removed."}), status_code=303
        )

    async def create_key(self, request):
        user = self._current_user(request)
        if not user:
            return RedirectResponse("/portal/login", status_code=303)
        if not self._origin_ok(request):
            return HTMLResponse(ui.message_page("Blocked", "Cross-origin request rejected."), status_code=403)
        form = await request.form()
        label = (form.get("label") or "").strip() or None
        key = security.generate_api_key()
        await run_in_threadpool(
            self.store.create_api_key,
            user["id"],
            security.hash_api_key(key),
            security.api_key_prefix(key),
            label,
        )
        return HTMLResponse(ui.new_key_page(self.config, key, user))

    async def revoke_key(self, request):
        user = self._current_user(request)
        if not user:
            return RedirectResponse("/portal/login", status_code=303)
        if not self._origin_ok(request):
            return HTMLResponse(ui.message_page("Blocked", "Cross-origin request rejected."), status_code=403)
        try:
            key_id = int(request.path_params["key_id"])
        except (KeyError, ValueError):
            return RedirectResponse("/portal?err=Invalid+key", status_code=303)
        await run_in_threadpool(self.store.revoke_api_key, key_id, user["id"])
        return RedirectResponse(
            "/portal?" + urlencode({"msg": "API key revoked."}), status_code=303
        )
