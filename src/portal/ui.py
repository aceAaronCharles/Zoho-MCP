"""
Self-contained HTML for the connection portal.

No template engine and no build step: the pages are plain strings with a
single inline stylesheet so the portal ships with the server and works behind
any reverse proxy.
"""

import html
import datetime
from typing import Any, Dict, List, Optional


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value))


STYLE = """
:root {
  --bg: #0f1220; --card: #171b2e; --card2: #1e2338; --line: #2a3050;
  --text: #e6e8f0; --muted: #9aa3c0; --accent: #4f7cff; --accent2: #6ee7b7;
  --danger: #ef4444; --warn: #f59e0b; --ok: #22c55e;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  background: radial-gradient(1200px 600px at 20% -10%, #1b2140, var(--bg));
  color: var(--text); min-height: 100vh; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar { display: flex; align-items: center; justify-content: space-between;
  padding: 14px 24px; border-bottom: 1px solid var(--line); background: rgba(15,18,32,.8);
  backdrop-filter: blur(8px); position: sticky; top: 0; z-index: 10; }
.brand { font-weight: 700; letter-spacing: .3px; }
.brand span { color: var(--accent2); }
.wrap { max-width: 980px; margin: 0 auto; padding: 28px 20px 80px; }
h1 { font-size: 26px; margin: 0 0 6px; }
h2 { font-size: 18px; margin: 0 0 14px; }
p.lead { color: var(--muted); margin-top: 0; }
.card { background: linear-gradient(180deg, var(--card), var(--card2));
  border: 1px solid var(--line); border-radius: 14px; padding: 20px; margin: 18px 0; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 760px) { .grid { grid-template-columns: 1fr; } }
label { display: block; font-size: 13px; color: var(--muted); margin: 12px 0 6px; }
input, select, textarea { width: 100%; padding: 10px 12px; border-radius: 9px;
  border: 1px solid var(--line); background: #0d1020; color: var(--text); font-size: 14px; }
textarea { min-height: 90px; font-family: ui-monospace, monospace; font-size: 12px; }
button, .btn { display: inline-block; padding: 10px 16px; border-radius: 9px; border: 0;
  background: var(--accent); color: white; font-size: 14px; font-weight: 600; cursor: pointer; }
button:hover, .btn:hover { filter: brightness(1.1); text-decoration: none; }
button.ghost { background: transparent; border: 1px solid var(--line); color: var(--text); }
button.danger { background: var(--danger); }
.badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px;
  font-weight: 600; }
.badge.ok { background: rgba(34,197,94,.15); color: #5ee89a; }
.badge.pending { background: rgba(245,158,11,.15); color: #f7c948; }
.badge.error { background: rgba(239,68,68,.15); color: #ff8b8b; }
.note { background: rgba(79,124,255,.08); border: 1px solid rgba(79,124,255,.35);
  border-radius: 10px; padding: 12px 14px; font-size: 13px; color: #c7d2fe; }
.err { background: rgba(239,68,68,.1); border: 1px solid rgba(239,68,68,.4);
  border-radius: 10px; padding: 12px 14px; font-size: 13px; color: #fecaca; }
.okmsg { background: rgba(34,197,94,.1); border: 1px solid rgba(34,197,94,.4);
  border-radius: 10px; padding: 12px 14px; font-size: 13px; color: #bbf7d0; }
code, .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12.5px; }
code { background: #0d1020; border: 1px solid var(--line); border-radius: 6px; padding: 2px 6px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--line); }
th { color: var(--muted); font-weight: 600; }
.muted { color: var(--muted); font-size: 13px; }
.kv { display: grid; grid-template-columns: 180px 1fr; gap: 8px 14px; font-size: 13.5px; }
.kv div:nth-child(odd) { color: var(--muted); }
.row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.spacer { flex: 1; }
.steps { counter-reset: step; padding-left: 0; list-style: none; }
.steps li { counter-increment: step; position: relative; padding: 8px 0 8px 40px; color: var(--muted); }
.steps li::before { content: counter(step); position: absolute; left: 0; top: 6px;
  width: 26px; height: 26px; border-radius: 999px; background: var(--card2);
  border: 1px solid var(--line); display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: var(--text); }
"""


def layout(title: str, body: str, user: Optional[Dict[str, Any]] = None) -> str:
    who = ""
    if user:
        who = (
            f'<span class="muted">{_e(user.get("email") or user.get("name") or "signed in")}</span>'
            f'<form method="post" action="/portal/logout" style="display:inline">'
            f'<button class="ghost" type="submit">Sign out</button></form>'
        )
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(title)} · Zoho MCP</title><style>{STYLE}</style>
</head><body>
<div class="topbar">
  <div class="brand">Zoho <span>MCP</span> · Connection Portal</div>
  <div class="row">{who}</div>
</div>
<div class="wrap">
{body}
</div>
</body></html>"""


def _status_badge(status: str) -> str:
    label = {"connected": "Connected", "pending": "Not connected", "error": "Error"}.get(
        status, status or "Unknown"
    )
    css = {"connected": "ok", "pending": "pending", "error": "error"}.get(status, "pending")
    return f'<span class="badge {css}">{_e(label)}</span>'


def login(config, error: str = "") -> str:
    error_block = f'<div class="err">{_e(error)}</div>' if error else ""

    oidc_card = ""
    if config.oidc_configured():
        oidc_card = f"""
<div class="card">
  <h2>Sign in with {_e(config.oidc_provider_name)}</h2>
  <p class="muted">Continue to your identity provider to authenticate.</p>
  <a class="btn" href="/portal/login/start">Continue with {_e(config.oidc_provider_name)}</a>
</div>"""

    dev = ""
    if config.allow_dev_login:
        dev = """
  <div class="card">
    <h2>Developer sign-in</h2>
    <p class="muted">Temporary sign-in for local testing. Disable by unsetting
    <code>PORTAL_DEV_LOGIN</code>.</p>
    <form method="post" action="/portal/dev-login">
      <label>Email</label>
      <input name="email" type="email" placeholder="you@example.com" required>
      <div style="margin-top:14px"><button type="submit">Continue</button></div>
    </form>
  </div>"""
    elif not config.oidc_configured():
        dev = (
            '<div class="err">No identity provider is configured. Set '
            "<code>PORTAL_OIDC_*</code> or, for local testing only, "
            "<code>PORTAL_DEV_LOGIN=true</code>.</div>"
        )

    body = f"""
<h1>Connect your Zoho account</h1>
<p class="lead">Sign in to manage the Zoho connection used by your MCP clients.</p>
{error_block}
{oidc_card}
{dev}"""
    return layout("Sign in", body)


def dashboard(
    config,
    user: Dict[str, Any],
    connection: Optional[Dict[str, Any]],
    keys: List[Dict[str, Any]],
    message: str = "",
    error: str = "",
) -> str:
    banners = ""
    if message:
        banners += f'<div class="okmsg">{_e(message)}</div>'
    if error:
        banners += f'<div class="err">{_e(error)}</div>'

    if not connection:
        conn_card = """
<div class="card">
  <h2>No Zoho connection yet</h2>
  <p class="muted">Connect your own Zoho account. You will need a Zoho API client
  (client ID and secret) for this. It takes about two minutes.</p>
  <a class="btn" href="/portal/connections/new">Connect Zoho</a>
</div>"""
    else:
        status = connection.get("status", "pending")
        details = f"""
<div class="kv">
  <div>Status</div><div>{_status_badge(status)}</div>
  <div>Client ID</div><div class="mono">{_e(connection.get('client_id'))}</div>
  <div>Data centre</div><div>{_e(connection.get('dc'))}</div>
  <div>Scopes</div><div class="mono" style="word-break:break-all">{_e(connection.get('scopes'))}</div>
  <div>Granted scopes</div><div class="mono" style="word-break:break-all">{_e(connection.get('granted_scopes') or '—')}</div>
  <div>Redirect URI</div><div class="mono" style="word-break:break-all">{_e(connection.get('redirect_uri'))}</div>
</div>"""
        err = ""
        if connection.get("error"):
            err = f'<div class="err" style="margin-top:12px">{_e(connection["error"])}</div>'

        if status == "connected":
            actions = """
  <form method="post" action="/portal/connections/test" style="display:inline">
    <button class="ghost" type="submit">Test connection</button>
  </form>
  <form method="post" action="/portal/connections/authorize" style="display:inline">
    <button class="ghost" type="submit">Re-authorize</button>
  </form>
  <form method="post" action="/portal/connections/delete" style="display:inline"
        onsubmit="return confirm('Remove this Zoho connection and revoke stored tokens?')">
    <button class="danger" type="submit">Disconnect</button>
  </form>"""
        else:
            actions = """
  <form method="post" action="/portal/connections/authorize" style="display:inline">
    <button type="submit">Authorize with Zoho</button>
  </form>
  <form method="post" action="/portal/connections/new" style="display:inline">
    <button class="ghost" type="submit">Edit credentials</button>
  </form>"""

        conn_card = f"""
<div class="card">
  <div class="row"><h2 style="margin:0">Zoho connection</h2><div class="spacer"></div>
  <a class="muted" href="/portal/connections/new">Edit</a></div>
  <div style="margin-top:14px">{details}</div>
  {err}
  <div class="row" style="margin-top:16px">{actions}</div>
</div>"""

    key_rows = ""
    for key in keys:
        if key.get("revoked"):
            continue
        last = key.get("last_used_at")
        if last:
            last = datetime.datetime.fromtimestamp(
                last, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%d %H:%M UTC")
        else:
            last = "never"
        last = _e(last)
        key_rows += f"""
<tr><td class="mono">{_e(key.get('prefix'))}…</td><td>{_e(key.get('label') or '—')}</td>
<td class="muted">{last}</td>
<td><form method="post" action="/portal/keys/{int(key['id'])}/revoke">
<button class="ghost" type="submit">Revoke</button></form></td></tr>"""
    if not key_rows:
        key_rows = '<tr><td colspan="4" class="muted">No API keys yet. Create one to use the MCP server.</td></tr>'

    mcp_url = f"{config.base_url}/mcp"
    keys_card = f"""
<div class="card">
  <h2>MCP API keys</h2>
  <p class="muted">Use one of these keys as the <code>Authorization: Bearer …</code>
  token when connecting an MCP client to <code>{_e(mcp_url)}</code>.</p>
  <table><thead><tr><th>Key</th><th>Label</th><th>Last used</th><th></th></tr></thead>
  <tbody>{key_rows}</tbody></table>
  <form method="post" action="/portal/keys" style="margin-top:16px">
    <div class="row">
      <input name="label" placeholder="Label (e.g. Claude Desktop)" style="max-width:320px">
      <button type="submit">Create API key</button>
    </div>
  </form>
</div>"""

    body = f"""
<h1>Your Zoho connection</h1>
<p class="lead">Each MCP user connects their own Zoho account. Tokens are encrypted at rest.</p>
{banners}
{conn_card}
{keys_card}"""
    return layout("Dashboard", body, user)


def new_connection(config, existing: Optional[Dict[str, Any]], error: str = "") -> str:
    err = f'<div class="err">{_e(error)}</div>' if error else ""
    dc_options = "".join(
        f'<option value="{dc}"{" selected" if (existing and existing.get("dc") == dc) or (not existing and dc == "com") else ""}>{dc}</option>'
        for dc in ["com", "eu", "in", "com.au", "com.cn", "jp", "ca", "sa", "ae", "sg"]
    )
    client_id = _e(existing.get("client_id")) if existing else ""
    scopes = _e(existing.get("scopes")) if existing else "all"
    body = f"""
<h1>Connect a Zoho account</h1>
<p class="lead">Enter the credentials from your own Zoho API client. They are
encrypted and only used to obtain tokens for this server.</p>
{err}
<div class="card">
  <h2>1. Register a Zoho API client</h2>
  <ol class="steps">
    <li>Open <a href="https://api-console.zoho.com/" target="_blank" rel="noopener">Zoho API Console</a>
        and create a <b>Server-based Application</b>.</li>
    <li>Set the <b>Authorized Redirect URI</b> to exactly:<br>
        <code>{_e(config.zoho_redirect_uri)}</code></li>
    <li>Copy the <b>Client ID</b> and <b>Client Secret</b> into the form below.</li>
  </ol>
</div>
<div class="card">
  <h2>2. Enter credentials</h2>
  <form method="post" action="/portal/connections">
    <label>Client ID</label>
    <input name="client_id" value="{client_id}" required autocomplete="off">
    <label>Client Secret</label>
    <input name="client_secret" type="password" required autocomplete="new-password"
           placeholder="{'leave blank to keep the current secret' if existing else ''}">
    <div class="grid">
      <div>
        <label>Data centre</label>
        <select name="dc">{dc_options}</select>
      </div>
      <div>
        <label>Scopes</label>
        <input name="scopes" value="{scopes}">
      </div>
    </div>
    <p class="muted">Use <code>all</code> for every app this server supports,
    <code>recommended</code> for the validated core set, or paste a
    comma/space-separated list of Zoho scopes. If Zoho rejects a scope, use
    <code>recommended</code> or remove the offending scope.</p>
    <div class="row" style="margin-top:16px">
      <button type="submit">Save and authorize</button>
      <a class="btn ghost" href="/portal">Cancel</a>
    </div>
  </form>
</div>"""
    return layout("Connect Zoho", body)


def message_page(title: str, message: str) -> str:
    body = f"""
<h1>{_e(title)}</h1>
<div class="card"><p>{_e(message)}</p>
<div style="margin-top:16px"><a class="btn" href="/portal">Back to portal</a></div></div>"""
    return layout(title, body)


def new_key_page(config, key: str, user: Dict[str, Any]) -> str:
    body = f"""
<h1>Your new API key</h1>
<div class="card">
  <div class="note">Copy this key now — it will not be shown again.</div>
  <p class="mono" style="word-break:break-all;font-size:15px;margin-top:16px">{_e(key)}</p>
  <p class="muted">Use it as the <code>Authorization: Bearer …</code> header when
  connecting to <code>{_e(config.base_url)}/mcp</code>.</p>
  <a class="btn" href="/portal">Done</a>
</div>"""
    return layout("API key", body, user)
