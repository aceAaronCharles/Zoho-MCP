# Deploying the Zoho MCP server

A production runbook for hosting the server on a VPS. It targets the
**multi-tenant** setup (each user connects their own Zoho account through the
connection portal); the single-tenant alternative is documented at the end.

## Choose a path

| Path | Best for | You get |
| --- | --- | --- |
| **A. Docker Compose** (recommended) | Most deployments | Caddy with automatic HTTPS, container isolation, one command to update |
| **B. systemd** | Hosts that don't run Docker | Hardened service unit, nightly backup timer, host reverse proxy |
| **C. Cloud bootstrap** | A brand-new VPS | Terraform + cloud-init that provisions and configures everything |

All three run the same server and use the same `.env` variables.

## What gets deployed

```
Internet ──443──▶ reverse proxy ──http──▶ zoho-mcp:8000
                  (Caddy/nginx,            /mcp      MCP streamable HTTP
                   TLS)                    /portal   setup UI + API keys
                                           /health   liveness probe
```

| File | Purpose |
| --- | --- |
| `DEPLOY.md` | This runbook. |
| `docker-compose.prod.yml` | App + Caddy stack (path A). The app is not published on the host. |
| `deploy/Caddyfile` | Reverse proxy with MCP-friendly streaming. |
| `deploy/env.prod.example` | Template for the root `.env`. |
| `deploy/systemd/` | Hardened unit, nightly backup timer, env template (path B). |
| `deploy/install-systemd.sh` | Idempotent installer for path B. |
| `deploy/backup.sh` | Consistent SQLite + token backup, run by the timer. |
| `deploy/cloud-init.yaml` | Provider-agnostic VPS bootstrap (path C). |
| `deploy/terraform/hetzner/` | Terraform example that drives the cloud-init. |
| `docker-compose.yml` | Single-host variant, loopback bind, no proxy. |
| `Makefile` | `make help` for common tasks. |

## Prerequisites

* A VPS with a public IP. **1 vCPU / 1 GB is plenty** — the workload is I/O
  bound.
* A (sub)domain, e.g. `mcp.example.com`, with an `A`/`AAAA` record pointing at
  the VPS.
* Ports **80 and 443** reachable (Caddy uses 80 for the ACME challenge).
* An OIDC identity provider where you can register a client (Google, Microsoft
  Entra, Okta, Auth0, Keycloak, Authentik). GitHub is plain OAuth2, not OIDC,
  so it does not work with the generic client.
* Docker Engine with Compose v2 (path A and C) **or** Python 3.11+ (path B).

---

## Path A — Docker Compose + Caddy

### 1. DNS

Create the record **before** starting Caddy so the certificate challenge can
succeed:

```
mcp.example.com.  300  IN  A  203.0.113.10
```

Verify with `dig +short mcp.example.com`.

### 2. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
newgrp docker          # or log out and back in
docker compose version
```

### 3. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 443/udp
sudo ufw enable
```

Do **not** open port 8000 — the application is only reachable through Caddy.

### 4. Fetch the code and configure

```bash
sudo mkdir -p /opt && sudo chown "$USER" /opt
cd /opt
git clone https://github.com/aceAaronCharles/Zoho-MCP.git zoho-mcp
cd zoho-mcp

cp deploy/env.prod.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # MCP_SECRET_KEY
chmod 600 .env
```

Edit `.env` and set:

* `SITE_ADDRESS`, `ACME_EMAIL`, `PORTAL_BASE_URL` — your public host.
* `MCP_SECRET_KEY` — the value printed above. **Store a copy somewhere safe**:
  losing it makes `portal.db` undecryptable.
* `MCP_ALLOWED_HOSTS` / `MCP_ALLOWED_ORIGINS` — the same public host.
* The `PORTAL_OIDC_*` values (see [Registering the redirect URIs](#registering-the-redirect-uris)).

### 5. Start the stack

```bash
docker compose -f docker-compose.prod.yml up -d --build   # or: make prod-up
docker compose -f docker-compose.prod.yml logs -f zoho-mcp
```

Confirm:

```bash
curl -fsS https://mcp.example.com/health                            # {"status":"ok"}
curl -s -o /dev/null -w '%{http_code}\n' https://mcp.example.com/mcp  # 401
```

The `401` is expected — `/mcp` requires a bearer credential.

### 6. Use it

Open `https://mcp.example.com/portal`, sign in with OIDC, paste your Zoho
client ID/secret, authorize Zoho, and copy the API key (shown once). Point MCP
clients at `https://mcp.example.com/mcp` with
`Authorization: Bearer <api key>`.

---

## Path B — systemd (no Docker)

Run the server directly, behind a host reverse proxy.

### 1. Get the code

```bash
sudo mkdir -p /opt && sudo chown "$USER" /opt
cd /opt
git clone https://github.com/aceAaronCharles/Zoho-MCP.git zoho-mcp
```

Keep it under `/opt` (or `/srv`). The unit sets `ProtectHome=true`, so `/home`
is hidden from the service.

### 2. Install the service

```bash
cd /opt/zoho-mcp
sudo ./deploy/install-systemd.sh
```

The installer:

* creates the `zoho-mcp` system account,
* builds the virtualenv and installs `requirements.txt`,
* creates `/var/lib/zoho-mcp`, `/var/log/zoho-mcp`, `/var/backups/zoho-mcp`,
* installs `/etc/zoho-mcp/zoho-mcp.env` from the template (mode `0640`),
* installs and enables the unit plus the **nightly backup timer**,
* starts the service only once a credential source is configured.

### 3. Configure and start

```bash
sudoedit /etc/zoho-mcp/zoho-mcp.env     # SITE_ADDRESS, MCP_SECRET_KEY, OIDC, ...
sudo systemctl restart zoho-mcp.service
sudo systemctl status zoho-mcp.service
journalctl -u zoho-mcp.service -f
```

The unit binds `MCP_HOST=127.0.0.1` and sets `MCP_REQUIRE_AUTH=true`, so the
service **refuses to start** until the portal or a shared token is configured.
That is deliberate: a loopback bind is not by itself authentication.

### 4. TLS with a host reverse proxy

```bash
sudo apt install -y caddy
```

```
# /etc/caddy/Caddyfile
zoho.example.com {
    reverse_proxy 127.0.0.1:8000 {
        flush_interval -1
    }
}
```

```bash
sudo systemctl reload caddy
curl -fsS https://zoho.example.com/health
```

### 5. Backups

`zoho-mcp-backup.timer` runs `deploy/backup.sh` nightly at 03:30 and prunes
archives older than `BACKUP_RETENTION_DAYS` (default 14). Check it with:

```bash
systemctl list-timers zoho-mcp-backup.timer
sudo systemctl start zoho-mcp-backup.service    # run one now
ls -l /var/backups/zoho-mcp
```

---

## Path C — automated cloud bootstrap

`deploy/cloud-init.yaml` installs Docker, configures the firewall, clones the
repository to `/opt/zoho-mcp`, generates `MCP_SECRET_KEY`, and writes
`/root/NEXT-STEPS.txt`. It deliberately places **no** Zoho or OIDC secret in
user-data (which is readable from the instance metadata service and the
provider console).

Use it by pasting into any provider's user-data field, or with the bundled
Terraform example:

```bash
export HCLOUD_TOKEN="..."
cd deploy/terraform/hetzner
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars        # ssh_key_name, site_address, acme_email
terraform init && terraform apply
```

Then create the DNS record it prints, wait for cloud-init, and follow
`/root/NEXT-STEPS.txt`. See
[`deploy/terraform/hetzner/README.md`](deploy/terraform/hetzner/README.md).
For other providers, replace the `@@PLACEHOLDERS@@` in the cloud-init file by
hand and open ports 22/80/443.

---

## Registering the redirect URIs

Two callbacks are involved.

| Register with | URI |
| --- | --- |
| Your OIDC identity provider | `https://<host>/portal/auth/callback` |
| Each user's Zoho API console | `https://<host>/oauth/zoho/callback` |

Zoho only permits `http://localhost` redirects for local testing; a hosted
deployment must use `https://`, and the value must match exactly.

### Identity provider (portal sign-in)

The portal discovers endpoints from
`<issuer>/.well-known/openid-configuration`. Create a **web** application and
set the redirect/callback URI to `https://<host>/portal/auth/callback`.

| Provider | Issuer (`PORTAL_OIDC_ISSUER`) | Where to create the client |
| --- | --- | --- |
| Google | `https://accounts.google.com` | Cloud Console → APIs & Services → Credentials → Create OAuth client ID → Web application |
| Microsoft Entra | `https://login.microsoftonline.com/<tenant-id>/v2.0` | Entra admin → App registrations → New registration → Redirect URI (Web) |
| Okta | `https://<org>.okta.com` or `https://<org>.okta.com/oauth2/default` | Applications → Create App Integration → OIDC → Web Application |
| Auth0 | `https://<tenant>.<region>.auth0.com/` | Applications → Create Application → Regular Web App → Allowed Callback URLs |
| Keycloak | `https://<keycloak>/realms/<realm>` | Clients → Create client → OpenID Connect → Valid redirect URIs |
| Authentik | `https://<authentik>/application/o/<slug>/` | Applications → Providers → OAuth2/OpenID Provider → Redirect URIs |

Copy the client ID and secret into `PORTAL_OIDC_CLIENT_ID` and
`PORTAL_OIDC_CLIENT_SECRET`. The default `PORTAL_OIDC_SCOPES` is
`openid email profile`.

### Zoho (per user)

Each user, in the Zoho [API console](https://api-console.zoho.com/):

1. Creates a **Server-based Application**.
2. Sets the authorized redirect URI to `https://<host>/oauth/zoho/callback`.
3. Copies the client ID and secret into the portal, chooses their data centre,
   and approves the scope set (`all` by default).

---

## Connecting MCP clients

### Hermes Agent

Hermes speaks standard MCP; both transports are verified against this server
(74 tools discovered).

**Hosted (HTTP).** Add to `~/.hermes/config.yaml`, or run
`hermes mcp add zoho --url https://mcp.example.com/mcp --auth header`:

```yaml
mcp_servers:
  zoho:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ${ZOHO_MCP_API_KEY}"
```

Put the key in `~/.hermes/.env`:

```
ZOHO_MCP_API_KEY=zoho_xxxxxxxxxxxxxxxx
```

**Local (stdio).** Hermes spawns the server as a subprocess; use absolute paths
so nothing depends on Hermes' working directory:

```yaml
mcp_servers:
  zoho:
    command: "/opt/zoho-mcp/.venv/bin/python"
    args: ["-m", "src.server"]
    env:
      PYTHONPATH: "/opt/zoho-mcp"
      TOKEN_FILE_PATH: "/opt/zoho-mcp/.zoho_tokens.json"
      LOG_FILE_PATH: "/opt/zoho-mcp/logs/zoho_crm_mcp.log"
```

Verify with `hermes mcp list` and `hermes mcp test zoho`.

### Other clients

Cursor, VS Code, Windsurf and Claude-compatible clients accept the same shape:

```json
{
  "mcpServers": {
    "zoho": {
      "url": "https://mcp.example.com/mcp",
      "headers": { "Authorization": "Bearer zoho_xxxxxxxxxxxxxxxx" }
    }
  }
}
```

---

## Single-tenant deployment

One shared Zoho account, no portal, no identity provider:

1. Set `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN` and
   `ZOHO_SCOPE` in `.env`; remove/disable the `PORTAL_*` block.
2. Generate a shared key and set `MCP_HTTP_TOKEN` (`openssl rand -hex 32`).
3. Clients send that key as the bearer token.

Keep `MCP_REQUIRE_AUTH=true` so the service still fails closed.

---

## Authentication model

Read this before exposing the server.

* `/mcp` requires `Authorization: Bearer <token>` whenever **either**
  `MCP_HTTP_TOKEN` **or** the portal is configured.
* Binding to a non-loopback address with neither is **refused at startup**.
* Binding to **loopback** with neither is allowed for local development — but
  that is also how people run the server behind a proxy, where `/mcp` would be
  open to everyone. The server now logs a warning, and
  **`MCP_REQUIRE_AUTH=true`** makes it refuse to start instead. Set it in any
  proxied deployment.
* MCP sessions are bound to the credential that created them; one user's key
  cannot reuse another's session.
* Each portal key resolves to its owner's Zoho connection; the tool list adapts
  to the scopes that account actually granted.

---

## Operations

### Back up the data

`portal.db` holds every user's **encrypted** Zoho credentials; the token file
holds the shared refresh token. Back both up **and `MCP_SECRET_KEY`** — without
the key the database is useless.

Docker (path A/C):

```bash
docker run --rm -v zoho-mcp_zoho_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/zoho-data-$(date +%F).tgz -C /data .
```

systemd (path B): `deploy/backup.sh` does a consistent SQLite online backup
into `/var/backups/zoho-mcp` and prunes old archives.

### Upgrade

```bash
# path A
cd /opt/zoho-mcp && git pull && docker compose -f docker-compose.prod.yml up -d --build
# path B
cd /opt/zoho-mcp && git pull && sudo ./deploy/install-systemd.sh && sudo systemctl restart zoho-mcp
```

### Use the published image

CI builds, smoke-tests and scans the image, then publishes it to GHCR on every
push to `main` and every `v*` tag:

```bash
docker run -d --name zoho-mcp -p 127.0.0.1:8000:8000 \
  --env-file .env ghcr.io/aceaaroncharles/zoho-mcp:latest
```

### Rotating `MCP_SECRET_KEY`

Don't, unless you intend to invalidate every stored connection — the key is the
only thing that can decrypt them. If it leaks, rotate it and tell every user to
reconnect their Zoho account.

---

## Hardening

* **Rate-limit** `/portal/login`, `/portal/keys` and `/mcp` at the proxy; the
  app has no built-in limiter. Caddy needs the `caddy-ratelimit` plugin; with
  nginx:

  ```nginx
  limit_req_zone $binary_remote_addr zone=zoho:10m rate=10r/s;
  location /mcp          { limit_req zone=zoho burst=20 nodelay; proxy_pass http://127.0.0.1:8000; proxy_buffering off; }
  location /portal/login { limit_req zone=zoho burst=5  nodelay; proxy_pass http://127.0.0.1:8000; }
  ```

* Set `MCP_READ_ONLY=true` if clients should never write to Zoho.
* Run **one replica**. SQLite is a single-writer store; scale with a bigger VPS,
  not with replicas.
* Keep `MCP_ALLOWED_HOSTS` set so DNS-rebinding protection is active.
* Install/verify unattended upgrades and keep the host patched.
* Rotate the Zoho client secret and refresh token in the API console if they
  were ever committed, and purge the Git history afterwards.

---

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Caddy: certificate errors | DNS not pointing at the VPS, or port 80 blocked. |
| `502 Bad Gateway` | The app container/process is down — check its logs. |
| Service exits with `MCP_REQUIRE_AUTH=true but ...` | No `MCP_HTTP_TOKEN` and no portal configured. |
| Service exits with `Refusing to bind ... non-loopback` | Set `MCP_HTTP_TOKEN`, enable the portal, or bind loopback. |
| Login loop / cookie not set | `PORTAL_BASE_URL` is not the public `https://` origin. |
| `invalid_scope` from Zoho | `ZOHO_SCOPE` includes a scope the client was not approved for; use `all`. |
| `invalid_client` / `invalid redirect uri` | The Zoho client's redirect URI does not exactly match `https://<host>/oauth/zoho/callback`. |
| `CryptoError` in logs | `MCP_SECRET_KEY` changed, or `portal.db` was copied between environments. |
| A Zoho app returns `403 SCOPE_MISMATCH` | The account/subscription lacks that app, not a code issue. |
| Hermes cannot connect | Run `hermes mcp test zoho`; check the bearer header/key. |
