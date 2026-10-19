# Security Policy

## Supported versions

Security fixes are applied to the latest release on `main`.

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Report privately
using GitHub's [Report a vulnerability](https://github.com/aceAaronCharles/Zoho-MCP/security/advisories/new)
form, or email the maintainers. Include:

* a description of the issue and its impact,
* reproduction steps or a proof of concept,
* the affected version or commit,
* any suggested remediation.

We aim to acknowledge reports within 72 hours and to publish a fix or
mitigation within 30 days, coordinating disclosure with you.

## Scope and threat model

This project brokers access to Zoho data, so the following are treated as
high-severity by default:

* **Credential exposure** — leaking `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`,
  `MCP_SECRET_KEY`, `MCP_HTTP_TOKEN`, or a per-user MCP API key.
* **Authentication bypass** — reaching `/mcp` or `/portal` without a valid
  bearer credential.
* **Cross-tenant access** — one user's API key resolving to another user's Zoho
  connection, or reusing another user's MCP session.
* **Secret decryption** — recovering stored Zoho tokens without
  `MCP_SECRET_KEY`.
* **Injection** — SSRF or request smuggling through `zoho_api_request`, or
  template/XSS issues in the portal UI.

Out of scope: vulnerabilities in Zoho's own services, in the identity provider,
or issues that require an already-compromised host.

## Handling secrets

* Never commit `.env`, `.zoho_tokens.json`, or `portal.db`; they are
  git-ignored and excluded from the image build context.
* If a credential was committed, rotate it in the Zoho API console **first**,
  then purge history. Rotation invalidates the old value everywhere; history
  rewriting alone does not.
* Per-user Zoho credentials are encrypted at rest with Fernet using
  `MCP_SECRET_KEY`. Back that key up separately: without it the database is
  undecryptable, and its loss is unrecoverable by design.
* The `detect-private-key` pre-commit hook and Dependabot are enabled to catch
  accidental key material and vulnerable dependencies.

## Hardening checklist for operators

See [DEPLOY.md](DEPLOY.md) for the full runbook. In short: terminate TLS,
require authentication (portal or `MCP_HTTP_TOKEN`), set `MCP_ALLOWED_HOSTS`,
use a strong random `MCP_SECRET_KEY`, rate-limit at the proxy, run one writer,
and back up the data volume.
