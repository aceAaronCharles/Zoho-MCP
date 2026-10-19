# Deploying the Zoho MCP server on a VPS

A production runbook for hosting the server on a single VPS with Docker Compose
and automatic HTTPS (Caddy). It targets the **multi-tenant** setup, where every
user connects their own Zoho account through the connection portal, and notes
the single-tenant alternative at the end.

## What gets deployed

```
Internet ──443──▶ caddy ──http──▶ zoho-mcp:8000
                  (TLS,           /mcp      MCP streamable HTTP
                   Let's Encrypt)  /portal   setup UI + API keys
                                   /health   liveness probe
```

* `zoho-mcp` — the Python server. **Not published on the host**; only Caddy
  reaches it, over the compose network.
* `caddy` — terminates TLS, obtains and renews certificates automatically.
* `zoho_data` volume — the token file and the encrypted `portal.db`.
* `caddy_data` volume — the issued certificates.

Artifacts in this repository:

| File | Purpose |
| --- | --- |
| `docker-compose.prod.yml` | App + Caddy stack (this is the file to use on a VPS). |
| `deploy/Caddyfile` | Reverse proxy with MCP-friendly streaming. |
| `deploy/env.prod.example` | Template for the root `.env`. |
| `docker-compose.yml` | Simpler single-host variant (loopback bind, no proxy). |

## Prerequisites

* A VPS with a public IP. **1 vCPU / 1 GB RAM is plenty** — the workload is
  I/O-bound. Use x86-64 or arm64 Linux (the image is `python:3.12-slim`).
* A (sub)domain, e.g. `mcp.example.com`, with an `A` (or `AAAA`) record pointing
  at the VPS.
* Ports **80 and 443** reachable from the internet (Caddy needs 80 for the
  ACME HTTP challenge).
* An OIDC identity provider where you can register a client (Google, Microsoft
  Entra, Okta, Auth0, Keycloak, Authentik). GitHub is plain OAuth2, not OIDC,
  so it does not work with the generic client.
* Docker Engine with Compose v2.

## 1. DNS

Create the record **before** starting Caddy so the certificate challenge can
succeed:

```
mcp.example.com.  300  IN  A  203.0.113.10
```

Verify it resolves to the VPS: `dig +short mcp.example.com`.

## 2. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
newgrp docker          # or log out and back in
docker compose version
```

## 3. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 443/udp
sudo ufw enable
```

Do **not** open port 8000 — the application is only reachable through Caddy.

## 4. Fetch the code and configure

```bash
sudo mkdir -p /opt && sudo chown "$USER" /opt
cd /opt
git clone https://github.com/aceAaronCharles/Zoho-MCP.git zoho-mcp
cd zoho-mcp

cp deploy/env.prod.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # MCP_SECRET_KEY
chmod 600 .env
```

Edit `.env` and set, at minimum:

* `SITE_ADDRESS`, `ACME_EMAIL`, `PORTAL_BASE_URL` — your public host.
* `MCP_SECRET_KEY` — the random value printed above. **Store a copy somewhere
  safe**: losing it makes `portal.db` undecryptable.
* `MCP_ALLOWED_HOSTS` / `MCP_ALLOWED_ORIGINS` — the same public host.
* The `PORTAL_OIDC_*` values for your identity provider.

## 5. Register the redirect URIs

You have **two** callbacks to register, on two different systems:

| Register with | URI |
| --- | --- |
| Your OIDC identity provider | `https://<host>/portal/auth/callback` |
| Each user's Zoho API console | `https://<host>/oauth/zoho/callback` |

Zoho only permits `http://localhost` redirects for local testing; a hosted
deployment must use `https://`, and the value in the Zoho console must match
exactly.

## 6. Start the stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f zoho-mcp
```

Caddy will request a certificate on first request. Confirm the deployment:

```bash
curl -fsS https://mcp.example.com/health          # {"status":"ok"}
curl -s -o /dev/null -w '%{http_code}\n' https://mcp.example.com/mcp   # 401
```

The `401` is expected: `/mcp` requires a bearer credential.

## 7. Use it

* **Portal** — open `https://mcp.example.com/portal`, sign in with OIDC, paste
  your Zoho client ID/secret, authorize Zoho, and copy the API key (shown once).
* **MCP endpoint** — `https://mcp.example.com/mcp` with
  `Authorization: Bearer <api key>`.

Each key resolves to its owner's Zoho connection, and the tool list adapts to
the scopes that account actually granted.

## Connecting Hermes Agent

Hermes Agent speaks standard MCP, so it can use the server either locally over
stdio or remotely over HTTP. Both have been verified against this server
(74 tools discovered).

### Remote (the hosted deployment above)

Add to `~/.hermes/config.yaml`, or use
`hermes mcp add zoho --url https://mcp.example.com/mcp --auth header`:

```yaml
mcp_servers:
  zoho:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ${ZOHO_MCP_API_KEY}"
```

Put the key in `~/.hermes/.env` (Hermes resolves `${VAR}` from there):

```
ZOHO_MCP_API_KEY=zoho_xxxxxxxxxxxxxxxx
```

### Local (stdio, single machine, no VPS)

Hermes spawns the server as a subprocess. Use **absolute paths** so nothing
depends on Hermes' working directory:

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

The server reads its own `.env` and `.zoho_tokens.json`, so credentials do not
need to be duplicated into the Hermes config.

### Verify

```bash
hermes mcp list            # zoho  ...  ✓ enabled
hermes mcp test zoho       # ✓ Connected ... ✓ Tools discovered: 74
```

## Connecting any other MCP client

Cursor, VS Code, Windsurf, and Claude-compatible clients all accept the same
shape:

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

## Single-tenant deployment

One shared Zoho account, no portal, no identity provider:

1. Set `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`, and
   `ZOHO_SCOPE` in `.env` (drop the `PORTAL_*` block).
2. Generate a shared key and set `MCP_HTTP_TOKEN` (e.g.
   `openssl rand -hex 32`).
3. Clients send that key as the bearer token.

Binding to `0.0.0.0` with neither `PORTAL_ENABLED=true` nor `MCP_HTTP_TOKEN`
set is refused at startup, on purpose.

## Operations

### Back up the data volume

`portal.db` holds every user's **encrypted** Zoho credentials, and the token
file holds the shared refresh token. Back both up along with `MCP_SECRET_KEY`;
without the key the database is useless.

```bash
docker compose -f docker-compose.prod.yml exec zoho-mcp \
  sh -c 'cp /data/portal.db /data/portal.db.bak'
docker run --rm -v zoho-mcp_zoho_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/zoho-data-$(date +%F).tgz -C /data .
```

### Upgrade

```bash
cd /opt/zoho-mcp
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

### Logs and status

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --since 1h zoho-mcp
```

### Rotating `MCP_SECRET_KEY`

**Don't**, unless you intend to invalidate every stored connection — the key is
the only thing that can decrypt them. If it leaks, rotate it and tell every user
to reconnect their Zoho account.

## Hardening

* Caddy has no built-in rate limiter. For `/portal/login`, `/portal/keys`, and
  `/mcp`, either install the `caddy-ratelimit` plugin or put Cloudflare/nginx in
  front. With nginx:

  ```nginx
  limit_req_zone $binary_remote_addr zone=zoho:10m rate=10r/s;
  location /mcp        { limit_req zone=zoho burst=20 nodelay; proxy_pass http://127.0.0.1:8000; proxy_buffering off; }
  location /portal/login { limit_req zone=zoho burst=5  nodelay; proxy_pass http://127.0.0.1:8000; }
  ```

* Keep `MCP_READ_ONLY=true` if clients should never write to Zoho.
* Run one replica. SQLite is a single-writer store; scale with a bigger VPS, not
  with replicas.
* Keep the host patched and only expose 80/443/SSH.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Caddy: `no certificate` / TLS errors | DNS not pointing at the VPS, or port 80 blocked. |
| `502 Bad Gateway` | The `zoho-mcp` container is down — check its logs. |
| Session cookie not set / login loop | `PORTAL_BASE_URL` is not the public `https://` origin. |
| `invalid_scope` from Zoho | `ZOHO_SCOPE` includes a scope the Zoho client was not approved for; use `all`. |
| `invalid_client` / `invalid redirect uri` | The Zoho client's redirect URI does not exactly match `https://<host>/oauth/zoho/callback`. |
| `CryptoError` in logs | `MCP_SECRET_KEY` changed, or `portal.db` was copied between environments. |
| Hermes cannot connect | Run `hermes mcp test zoho` and check the bearer header/key. |
