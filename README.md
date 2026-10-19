# Zoho Ecosystem MCP Server

<div align="center">

**🚀 Built by [JunnAI](https://junnaisystem.com) - Empowering AI-driven business automation**

[![Website](https://img.shields.io/badge/Website-junnaisystem.com-blue?style=flat-square)](https://junnaisystem.com)
[![GitHub](https://img.shields.io/badge/GitHub-junnaisystems-black?style=flat-square&logo=github)](https://github.com/junnaisystems)
[![Support](https://img.shields.io/badge/Support-contact%20us-green?style=flat-square)](https://junnaisystem.com/contact)

</div>

---

A comprehensive **Model Context Protocol (MCP) server** for seamless integration with **46 Zoho applications**. This server enables AI assistants like Claude to interact with your entire Zoho ecosystem through a secure, OAuth-based authentication system.

**Free & Open Source** - Built with ❤️ by the team at [JunnAI](https://junnaisystem.com)

## 🎯 Supported Zoho Apps

This MCP server supports **46 Zoho applications** across all major business categories:

### Dedicated tools (9 apps)
- ✅ **CRM** - Customer relationship management
- ✅ **Books** - Accounting and invoicing
- ✅ **Projects** - Project management
- ✅ **Desk** - Customer support ticketing
- ✅ **People** - HR management
- ✅ **Recruit** - Applicant tracking
- ✅ **Inventory** - Stock management
- ✅ **Analytics** - Business intelligence
- ✅ **Creator** - Custom applications

### Full catalog (46 apps)

Every app is reachable through the generic `zoho_api_request` tool; the nine
apps above also have convenience tools. The catalog is defined in
[`src/zoho_apps.py`](src/zoho_apps.py):

**Sales & Marketing**: SalesIQ, Bookings, Campaigns, Social, Forms, Survey,
MarketingHub, PageSense  
**Finance & Commerce**: Books, Invoice, Expense, Inventory, Subscriptions,
Commerce  
**Customer Service**: Desk, Assist  
**HR & Recruitment**: People, Recruit, Payroll  
**Project Management**: Projects, Sprints, BugTracker, Practice  
**Collaboration**: Connect, Cliq, Meeting, Calendar  
**Email, Storage & Productivity**: Mail, TeamInbox, WorkDrive, Writer, Sheet,
Show, Learn  
**Analytics & Developer**: Analytics, Creator, Flow, Catalyst  
**Operations**: Fleet, FSM  
**Legal, Security & Admin**: Sign, Contracts, Vault, Directory  
**IoT**: IoT

`list_zoho_apps()` returns the live catalog with each app's base URL, API path,
required scopes, a `scopes_verified` flag, and any `missing_scopes` for the
current grant. Apps whose scope names could not be confirmed against Zoho's
published API docs are marked `scopes_verified: false` and are left out of the
default consent set (see [Enabling every app](#enabling-every-app)).

## ✨ Features

- **🔐 Secure OAuth Authentication** - Full OAuth 2.0 flow with automatic token refresh
- **🌐 Multi-App Support** - Access 46 Zoho applications through a single MCP server
- **📊 Complete Operations** - Create, read, update, delete records across all apps
- **🔍 Advanced Search** - Powerful search and filtering capabilities across apps
- **📈 Business Intelligence** - Access Analytics, reports, and dashboards
- **🔄 Bulk Operations** - Efficiently handle multiple records at once
- **🎯 Smart Routing** - Automatic API routing based on enabled apps
- **📱 Cross-App Integration** - Seamlessly work across multiple Zoho services
- **⚡ Real-time Token Management** - Automatic token refresh and error handling
- **📝 Comprehensive Logging** - Detailed logging for debugging and monitoring
- **🧩 Complete Tool Surface** - Every tool is always registered; calls the token is not authorised for return a clear Zoho error
- **🛰️ Hosting Ready** - Run locally over stdio, or host the streamable HTTP transport behind bearer auth

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Zoho CRM account with API access
- Claude Pro subscription (for AI integration)

### 1. Installation

#### Option A: Using pip (Recommended)
```bash
pip install -r requirements.txt
```

#### Option B: Using uv (Alternative)
```bash
# Install uv (if not already installed)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt
```

### 2. Zoho CRM Setup

#### Create a Zoho CRM Application

1. Go to [Zoho Developer Console](https://api-console.zoho.com/)
2. Click "Add Client"
3. Choose "Server-based Applications"
4. Fill in the details:
   - **Client Name**: Your application name
   - **Homepage URL**: Your website URL
   - **Authorized Redirect URIs**: `http://localhost:8080/callback`
5. Click "Create"
6. Note down your **Client ID** and **Client Secret**

#### Configure API Scopes

Make sure your application has the following scopes:
- `ZohoCRM.modules.ALL`
- `ZohoCRM.settings.ALL`
- `ZohoCRM.users.ALL`

### 3. Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your Zoho credentials:
```bash
# Zoho OAuth Configuration
ZOHO_CLIENT_ID=your_client_id_here
ZOHO_CLIENT_SECRET=your_client_secret_here
ZOHO_REDIRECT_URI=http://localhost:8080/callback
ZOHO_SCOPE=ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL

# Optional: Customize other settings
# ZOHO_API_DOMAIN=https://www.zohoapis.com
# ZOHO_ACCOUNTS_DOMAIN=https://accounts.zoho.com
# LOG_LEVEL=INFO
```

### 4. Using with AI Assistants

This MCP server is designed to work with AI assistants that support the Model Context Protocol (MCP).

#### For Warp Terminal Users:

Tell your AI assistant:

```
I have a Zoho Ecosystem MCP server ready to use. Here are the details:

Path to MCP Server: /path/to/your/zoho-mcp/src/server.py

Please use this MCP server to help me work with my Zoho data across multiple apps. 
Start by running get_configuration_status() to confirm credentials are loaded,
then list_zoho_apps() to see every supported Zoho app.
```

#### For Claude Desktop Users:

Add this to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "zoho-ecosystem": {
      "command": "python",
      "args": ["/path/to/your/zoho-mcp/src/server.py"],
      "env": {
        "ZOHO_CLIENT_ID": "your_client_id_here",
        "ZOHO_CLIENT_SECRET": "your_client_secret_here",
        "ZOHO_REFRESH_TOKEN": "your_refresh_token_here",
        "ZOHO_SCOPE": "all"
      }
    }
  }
}
```

#### First-Time Setup:

With `ZOHO_REFRESH_TOKEN` set (the recommended headless setup), the server
loads credentials immediately and never opens a browser. If you only have a
client ID and secret, run the interactive flow once with
`ZOHO_INTERACTIVE_AUTH=true` to create the token file, then copy the
`ZOHO_REFRESH_TOKEN` from `.zoho_tokens.json` into your environment.

The server always registers every tool, even before credentials are
configured, so an MCP client can discover them and receive an actionable setup
error from `get_configuration_status()`.

## 🔑 Obtaining a refresh token (recommended)

1. In the [Zoho API console](https://api-console.zoho.com/) create a
   **Server-based Application** and add the scopes you need, or use
   `ZOHO_SCOPE=all` and grant full access during consent.
2. Build a consent URL (replace the placeholders):

   ```
   https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCRM.modules.ALL,ZohoBooks.fullaccess.all,Desk.tickets.ALL,ZohoProjects.projects.ALL&client_id=CLIENT_ID&response_type=code&access_type=offline&redirect_uri=http://localhost:8080/callback
   ```

   Add `&prompt=consent` to force Zoho to return a refresh token.
3. Approve access. Zoho redirects to your redirect URI with a `code`
   parameter.
4. Exchange the code once:

   ```bash
   ZOHO_AUTH_CODE=<code> python manual_exchange.py
   ```

   Or run the server with `ZOHO_INTERACTIVE_AUTH=true` and the built-in
   callback listener.
5. Copy the `refresh_token` from `.zoho_tokens.json` into `ZOHO_REFRESH_TOKEN`
   and keep it secret. It does not expire, but it can be revoked.

### Enabling every app

Scope presets:

| Preset | Contents |
| --- | --- |
| `all` (default) | Scope names verified against Zoho's published API docs. |
| `recommended` | The validated 23-scope core set (the reference token). |
| `everything` | `all` plus the best-effort *unverified* app scopes. |

Zoho rejects the whole consent request with `invalid_scope` if a single scope
is unknown, so `all` deliberately ships only verified scopes. The unverified
apps (for example Forms, Survey, Sprints, BugTracker, TeamInbox, Learn,
Practice, Payroll, Fleet, FSM, Flow, Writer, Show, Contracts, IoT, Connect and
Commerce) stay in the catalog and remain callable — they are simply excluded
from the default consent set until their scopes are confirmed.

A refresh token keeps the scopes it was granted with, so after changing the
preset you must re-consent:

- **Local / stdio**: set `ZOHO_SCOPE=all`, then call
  `authenticate_zoho(scopes="all", force=True)` from your MCP client. It opens
  the browser, runs the callback listener, and reloads the registry.
- **Hosted portal**: open `/portal`, use **Re-authorize**, and keep `Scopes` set
  to `all` (or `recommended`).
- **Manual**: call `get_zoho_authorization_url(scopes="all")` to get a consent
  URL, then exchange the code as above.

To also attempt the unverified apps, use the `everything` preset (or set
`ZOHO_SCOPE_INCLUDE_UNVERIFIED=true` to append them to `all`). If Zoho replies
with `invalid_scope`, fall back to `recommended` or drop the offending names
with `ZOHO_SCOPE_EXCLUDE=Scope.One,Scope.Two`. Apps always appear in the
catalog; scopes only control whether your token can call them.

## 🌐 Hosting over HTTP

Set `MCP_TRANSPORT=http` to serve the streamable HTTP transport (useful for
remote hosts and containers). When binding to anything other than loopback you
must either set `MCP_HTTP_TOKEN` **or** enable the connection portal; the server
refuses to start with neither.

```bash
MCP_TRANSPORT=http \
MCP_HOST=0.0.0.0 \
MCP_PORT=8000 \
MCP_HTTP_TOKEN=$(openssl rand -hex 32) \
python -m src.server
```

Clients must send `Authorization: Bearer <MCP_HTTP_TOKEN>` on every request.
`GET /health` is public and returns `{"status":"ok"}`. A `Dockerfile` and
`docker-compose.yml` are included for container hosting.

For a complete VPS runbook — Docker Compose, Caddy with automatic HTTPS, the
multi-tenant portal, backups, and connecting **Hermes Agent** (stdio and hosted
HTTP) — see **[DEPLOY.md](DEPLOY.md)**.

Set `MCP_READ_ONLY=true` to block every write operation (POST/PUT/PATCH/DELETE)
while still allowing reads.

## 🔐 Multi-tenant connection portal (hosted setup UI)

For a hosted deployment where **each user connects their own Zoho account**, the
server ships a setup portal on the same port as the MCP endpoint. Users sign in
with OIDC, bring their own Zoho client ID/secret, connect Zoho once, and receive
a personal MCP API key.

```
User ──OIDC──▶ /portal ──▶ Zoho OAuth ──▶ encrypted tokens in SQLite
                                            │
MCP client ──Bearer <personal API key>──▶ /mcp ──▶ that user's Zoho connection
```

Everything below is optional: without `PORTAL_ENABLED=true` the server behaves
exactly as before (stdio, or HTTP with a shared `MCP_HTTP_TOKEN`).

### 1. Configure the portal

```bash
PORTAL_ENABLED=true
PORTAL_BASE_URL=https://zoho.example.com
PORTAL_DB_PATH=/data/portal.db
MCP_SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(48))")

# OIDC identity provider (any issuer with /.well-known/openid-configuration)
PORTAL_OIDC_ISSUER=https://accounts.google.com
PORTAL_OIDC_CLIENT_ID=...
PORTAL_OIDC_CLIENT_SECRET=...
PORTAL_OIDC_NAME=Google
```

Register `https://zoho.example.com/portal/auth/callback` with the identity
provider. Google, Microsoft Entra, Okta, Auth0, and Keycloak all work; GitHub is
plain OAuth2, not OIDC, so it is not supported by the generic client.

`MCP_SECRET_KEY` encrypts every stored Zoho secret and token with Fernet. **Back
it up**: without it the database cannot be decrypted. The server refuses to
start with the portal enabled and no key.

### 2. Start the server and open the portal

```bash
MCP_TRANSPORT=http MCP_HOST=0.0.0.0 MCP_PORT=8000 python -m src.server
```

Open `https://zoho.example.com/portal`. Each user:

1. Signs in with the identity provider.
2. Creates a **Server-based Application** in the
   [Zoho API Console](https://api-console.zoho.com/) and sets the authorized
   redirect URI to `https://zoho.example.com/oauth/zoho/callback`.
3. Pastes their client ID/secret, chooses the data centre and scopes
   (`all` by default), and authorizes Zoho.
4. Creates an MCP API key (shown once) and uses it as
   `Authorization: Bearer zoho_...` in their MCP client.

Point the MCP client at `https://zoho.example.com/mcp` with that header. Each
key resolves to its owner's Zoho connection, and the tool list adapts to the
scopes that account actually granted.

### Running the portal locally

For local testing you can skip the identity provider:

```bash
PORTAL_ENABLED=true PORTAL_DEV_LOGIN=true \
MCP_SECRET_KEY=dev-only-secret \
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 PORTAL_BASE_URL=http://127.0.0.1:8000 \
python -m src.server
```

Then open <http://127.0.0.1:8000/portal>. Never enable `PORTAL_DEV_LOGIN` on a
public deployment.

### Security notes

* `MCP_SECRET_KEY` and the portal database are as sensitive as a password vault.
  Keep both on a private volume and out of version control.
* Portal sessions are HMAC-signed, `HttpOnly`, `SameSite=Lax` cookies. Mutating
  forms reject cross-origin submissions.
* MCP sessions are bound to the API key that created them; a different key
  cannot reuse an existing session.
* A shared `MCP_HTTP_TOKEN` (if set) still works and maps to the process-wide
  `ZOHO_*` connection. Use it only for single-tenant deployments.
* The portal supports one Zoho connection per user; reconnecting replaces it.

### Production deployment checklist

Before exposing the server publicly:

* **Terminate TLS in front of it** (nginx, Caddy, a load balancer, or the
  platform ingress). The server speaks plain HTTP; set `PORTAL_BASE_URL` to the
  public `https://` origin, which also makes the session cookie `Secure`.
* **Require authentication.** Either `PORTAL_ENABLED=true` (multi-tenant) or
  `MCP_HTTP_TOKEN=<random>` (single tenant). Binding to `0.0.0.0` without one of
  these is refused at startup.
* **Set `MCP_ALLOWED_HOSTS`** to your public host (and `MCP_ALLOWED_ORIGINS` if a
  browser calls `/mcp`) so DNS-rebinding protection is active.
* **Use a strong `MCP_SECRET_KEY`** from a secret manager
  (`python -c "import secrets;print(secrets.token_urlsafe(48))"`). The same key
  must be used to read an existing `portal.db`; rotating it invalidates every
  stored connection.
* **Never set `PORTAL_DEV_LOGIN=true`** in production. Register
  `https://<host>/portal/auth/callback` with the identity provider and
  `https://<host>/oauth/zoho/callback` as the Zoho redirect URI.
* **Rate-limit and size-limit at the proxy** for `/portal/login`, `/portal/keys`
  and `/mcp` (the app has no built-in rate limiter).
* **Back up the `portal.db` and token-file volume.** SQLite is a single file per
  instance, so run one writer and use volume snapshots or `sqlite3 .backup`.
  For high write concurrency, replace the storage layer with a networked DB.
* **Pin dependencies** (the image builds from `requirements.txt`) and let CI
  (`.github/workflows/tests.yml`) gate `mcp`/`starlette` upgrades.
* **Monitor `/health` and the logs.** A `CryptoError` means `MCP_SECRET_KEY`
  changed or the database was copied between environments.
* **Rotate the Zoho client secret and refresh token** in the API console if they
  were ever committed. The server only reads them from the environment.

## 🧰 Generic access to every Zoho app

Use `zoho_api_request` to call any Zoho REST endpoint, including apps that do
not have dedicated tools:

```python
zoho_api_request("Books", "invoices", "GET", {"organization_id": "123"})
zoho_api_request("Desk", "tickets", "GET", {"limit": 10})
zoho_api_request("CRM", "Leads", "POST", data={"data": [{"Last_Name": "Doe"}]})
```

`list_zoho_apps()` returns every configured app, its base URL, API path,
required scopes, and any `missing_scopes` for the current grant. The `enabled`
flag reflects the local scope heuristic only; Zoho performs the final
authorisation check. To grant more scopes, call
`get_zoho_authorization_url(scopes="all")` and approve the consent, or
re-authorize through the portal.


### 5. Quick Reference - Available Tools

Once connected, your AI assistant can use these tools:

**System Tools:**
```
• list_enabled_apps() - See which Zoho apps are enabled for the current grant
• list_zoho_apps() - Full catalog with base URLs and missing scopes
• get_zoho_authorization_url(scopes="all") - Consent URL for more scopes
• authenticate_zoho(scopes=None, force=False) - Authenticate / re-consent
• revoke_authentication() - Revoke stored tokens
```

**CRM Tools (20+ tools):**
```
• get_modules() - Get all CRM modules  
• get_records() - Get records from modules
• search_records() - Search for specific records
• create_record() - Create new records
• update_record() - Update existing records
• convert_lead() - Convert leads to accounts/contacts/deals
• get_organization_info() - Get organization details
• And more...
```

**Books Tools (9 tools):**
```
• books_get_invoices() - Get invoices
• books_create_invoice() - Create new invoice
• books_get_customers() - Get customers
• books_get_vendors() - Get vendors
• books_get_bills() - Get bills
• books_get_expenses() - Get expenses
• And more...
```

**Projects Tools (9 tools):**
```
• projects_get_portals() - Get all portals
• projects_get_projects() - Get projects
• projects_get_tasks() - Get tasks
• projects_create_task() - Create new task
• projects_get_milestones() - Get milestones
• projects_get_timesheets() - Get timesheets
• And more...
```

**Desk Tools (8 tools):**
```
• desk_get_tickets() - Get support tickets
• desk_create_ticket() - Create new ticket
• desk_update_ticket() - Update ticket
• desk_add_comment() - Add comment to ticket
• desk_get_contacts() - Get support contacts
• And more...
```

**People, Recruit, Inventory, Analytics, Creator Tools:**
- 30+ additional tools for HR, recruitment, inventory, analytics, and custom apps
- See tool documentation for complete list

**Everything else:**
- Use `zoho_api_request(app_name, endpoint, method, params, data)` for the
  remaining catalog apps (Mail, Calendar, WorkDrive, Sign, Bookings, ...)

## 📚 Available Tools

### Authentication Tools

- **`authenticate_zoho(scopes=None, force=False)`** - Authenticate with Zoho (handles OAuth flow); pass `scopes="all", force=True` to re-consent for the full catalog
- **`get_zoho_authorization_url(scopes="all")`** - Return a consent URL for granting more scopes
- **`revoke_authentication()`** - Revoke stored authentication tokens

### Module & Metadata Tools

- **`get_modules()`** - Get all available CRM modules
- **`get_module_fields(module_name)`** - Get field information for a specific module

### Record Management Tools

- **`get_records(module_name, page, per_page, sort_order, sort_by)`** - Get records from a module
- **`get_record_by_id(module_name, record_id)`** - Get a specific record by ID
- **`search_records(module_name, criteria, page, per_page)`** - Search records using criteria
- **`create_record(module_name, record_data, trigger_workflow)`** - Create a new record
- **`update_record(module_name, record_id, record_data, trigger_workflow)`** - Update an existing record
- **`delete_record(module_name, record_id)`** - Delete a record
- **`bulk_create_records(module_name, records_data, trigger_workflow)`** - Create multiple records

### Relationship Tools

- **`get_related_records(module_name, record_id, related_module, page, per_page)`** - Get related records

### Analytics & Info Tools

- **`get_organization_info()`** - Get organization information
- **`get_users(type_filter)`** - Get CRM users information
- **`get_record_count(module_name, criteria)`** - Get record count with optional filtering

### Utility Tools

- **`convert_lead(lead_id, convert_data)`** - Convert leads to accounts, contacts, and deals

## 💡 Usage Examples

### Example 1: Get All Leads
```python
# This will be called by the AI assistant
result = get_records("Leads", page=1, per_page=50)
print(f"Found {result['count']} leads")
```

### Example 2: Search for Contacts
```python
# Search for contacts with specific email
result = search_records("Contacts", "(Email:equals:john@example.com)")
```

### Example 3: Create a New Lead
```python
lead_data = {
    "First_Name": "John",
    "Last_Name": "Doe", 
    "Email": "john.doe@example.com",
    "Company": "Example Corp",
    "Phone": "+1234567890"
}
result = create_record("Leads", lead_data)
```

### Example 4: Convert a Lead
```python
convert_data = {
    "overwrite": False,
    "notify_lead_owner": True,
    "notify_new_entity_owner": True,
    "Accounts": {
        "Account_Name": "Example Corp"
    },
    "Deals": {
        "Deal_Name": "New Business Opportunity",
        "Amount": 50000
    }
}
result = convert_lead("lead_id_here", convert_data)
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ZOHO_CLIENT_ID` | - | **Required**: Your Zoho app client ID |
| `ZOHO_CLIENT_SECRET` | - | **Required**: Your Zoho app client secret |
| `ZOHO_REFRESH_TOKEN` | - | **Required for headless use**: long-lived refresh token |
| `ZOHO_REDIRECT_URI` | `http://localhost:8080/callback` | OAuth redirect URI (interactive flow only) |
| `ZOHO_SCOPE` | `all` | Scope preset (`all`, `recommended`, `everything`) or an explicit list |
| `ZOHO_SCOPE_EXCLUDE` | - | Comma/space-separated scopes to drop from a preset |
| `ZOHO_SCOPE_INCLUDE_UNVERIFIED` | `false` | Append best-effort unverified scopes to the `all` preset |
| `ZOHO_DC` | `com` | Data centre suffix: `com`, `eu`, `in`, `com.au`, `jp`, `ca`, ... |
| `ZOHO_API_DOMAIN` | derived from DC | Override the Zoho API base URL |
| `ZOHO_ACCOUNTS_DOMAIN` | derived from DC | Override the Zoho accounts URL |
| `ZOHO_DESK_ORG_ID` | auto-discovered | Zoho Desk organisation ID |
| `ZOHO_ANALYTICS_ORG_ID` | auto-discovered | Zoho Analytics org ID (`ZANALYTICS-ORGID`) |
| `TOKEN_FILE_PATH` | `.zoho_tokens.json` | Path to store OAuth tokens |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `http` |
| `MCP_HTTP_TOKEN` | - | Shared bearer token for single-tenant HTTP (or enable the portal) |
| `MCP_ALLOWED_HOSTS` | SDK default | Comma-separated Host allow-list for DNS-rebinding protection |
| `PORTAL_ENABLED` | `false` | Serve the multi-tenant connection portal on the same port |
| `PORTAL_BASE_URL` | `http://localhost:8000` | Public URL used in links and OAuth callbacks |
| `PORTAL_DB_PATH` | `portal.db` | SQLite database for users, connections and API keys |
| `MCP_SECRET_KEY` | - | **Required** when the portal is enabled; encrypts stored Zoho secrets |
| `PORTAL_SESSION_SECRET` | `MCP_SECRET_KEY` | Signs portal session cookies |
| `PORTAL_OIDC_ISSUER` | - | OIDC issuer (e.g. `https://accounts.google.com`) |
| `PORTAL_OIDC_CLIENT_ID` | - | OIDC client ID |
| `PORTAL_OIDC_CLIENT_SECRET` | - | OIDC client secret |
| `PORTAL_OIDC_NAME` | `SSO` | Provider name shown on the sign-in page |
| `PORTAL_COOKIE_SECURE` | auto | Force `Secure` cookies (defaults to on for HTTPS) |
| `PORTAL_DEV_LOGIN` | `false` | Local-only email sign-in; never enable publicly |
| `ZOHO_OAUTH_REDIRECT_URI` | `${PORTAL_BASE_URL}/oauth/zoho/callback` | Per-user Zoho callback registered in their API client |
| `MCP_READ_ONLY` | `false` | Block all write operations when `true` |
| `LOG_LEVEL` | `INFO` | Logging level |
| `REQUEST_TIMEOUT` | `30` | API request timeout in seconds |
| `RATE_LIMIT` | `100` | Requests per minute limit |

## 🔒 Security Features

- **OAuth 2.0 Flow**: Secure authentication without exposing passwords
- **Refresh Tokens**: Headless authentication that never stores a password
- **Token Auto-Refresh**: Automatically refreshes expired access tokens
- **Owner-Only Token Storage**: Token files are written atomically with `0600` permissions
- **Read-Only Mode**: `MCP_READ_ONLY=true` blocks every write operation
- **Bearer-Authenticated HTTP**: Non-loopback HTTP requires `MCP_HTTP_TOKEN` or the portal
- **Encrypted at rest**: The portal encrypts every stored Zoho client secret and token (Fernet)
- **Per-user isolation**: Each MCP API key maps to one user's Zoho connection; sessions are bound to their key
- **No Secret Logging**: Credentials and tokens are never written to logs
- **Rate Limiting**: Built-in protection against API abuse
- **Request Timeout**: Prevents hanging requests

## 🐛 Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Check your `ZOHO_CLIENT_ID` and `ZOHO_CLIENT_SECRET`
   - Ensure redirect URI matches exactly: `http://localhost:8080/callback`
   - Verify your Zoho app has the required scopes

2. **"Token refresh failed"**
   - Delete `.zoho_tokens.json` and re-authenticate
   - Check if your Zoho app is still active

3. **"Module not found"**
   - Use `get_modules()` to see available modules
   - Check module name spelling (case-sensitive)

4. **"Permission denied"**
   - Verify your user has access to the requested module
   - Check if the module is enabled in your CRM

5. **`INVALID_OAUTH_SCOPE` / `SCOPE_MISMATCH` for an app**
   - The refresh token was created without that app's scope. Re-run the consent
     flow with the extra scope (or `ZOHO_SCOPE=all`) and replace
     `ZOHO_REFRESH_TOKEN`. Some apps also require the app to be provisioned on
     the account (for example Zoho Desk returns `SCOPE_MISMATCH` until
     `Desk.tickets.ALL` is granted *and* the Desk org exists).
   - `list_zoho_apps()` shows the local scope heuristic, but Zoho is the final
     authority; `zoho_api_request` still attempts apps marked disabled.

6. **Desk returns "requires an organisation ID"**
   - Set `ZOHO_DESK_ORG_ID` (Desk → Setup → Developer Space), or grant
     `Desk.organizations.READ` so the server can discover it automatically.

7. **Books/Inventory ask for an organisation ID**
   - Leave `organization_id` empty and the server discovers the first
     organisation automatically; set it explicitly when the account has more
     than one.

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

This will show detailed API requests and responses.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🎆 About JunnAI

[**JunnAI**](https://junnaisystem.com) is a leading provider of AI-driven business automation solutions. We specialize in:

- 🤖 **AI Voice Agents** - Intelligent conversational AI for customer service
- 🔗 **CRM Integrations** - Seamless connections between AI and business systems  
- 📈 **Sales Automation** - AI-powered lead generation and conversion
- ⚙️ **Custom AI Solutions** - Tailored automation for your business needs

**Why choose JunnAI?**
- ✅ Proven expertise in AI and business automation
- ✅ Open-source contributions to the community
- ✅ Enterprise-grade solutions with dedicated support
- ✅ Cutting-edge technology stack

🚀 **Ready to transform your business with AI?** 
➡️ Visit [junnaisystem.com](https://junnaisystem.com) to learn more!

---

## 📞 Support

- **🌐 Website**: [junnaisystem.com](https://junnaisystem.com)
- **📧 Email**: [jennifer@junnaisystem.com](mailto:jennifer@junnaisystem.com)
- **🐛 Issues**: [Report bugs via GitHub Issues](https://github.com/junnaisystems/zoho-crm-mcp/issues)
- **📖 Documentation**: See this README and inline code documentation
- **💬 Contact**: [Get in touch](https://junnaisystem.com/contact)

## 🚦 Status

- ✅ OAuth Authentication
- ✅ Core CRUD Operations
- ✅ Advanced Search
- ✅ Bulk Operations
- ✅ Lead Conversion
- ✅ Relationship Management
- ✅ Error Handling
- ✅ Token Management
- 🔄 Enhanced Analytics (planned)
- 🔄 Webhook Support (planned)

---

**Made with ❤️ by [JunnAI](https://junnaisystem.com)** - [Empowering AI-driven business automation](https://junnaisystem.com)

🚀 **Explore more AI solutions at [junnaisystem.com](https://junnaisystem.com)**
