# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* Production deployment runbook (`DEPLOY.md`): Docker Compose with Caddy and
  automatic HTTPS, a hardened systemd unit and nightly backup timer, a
  provider-agnostic cloud-init bootstrap, and a Hetzner Cloud Terraform example.
* Identity-provider registration steps for Google, Microsoft Entra, Okta,
  Auth0, Keycloak and Authentik.
* Verified Hermes Agent integration (local stdio and hosted streamable HTTP).
* Supply-chain tooling: `.dockerignore`, Dependabot, and an image workflow that
  builds, smoke-tests, scans (Trivy) and publishes to GHCR.
* Developer tooling: `Makefile`, `.editorconfig`, `.pre-commit-config.yaml`,
  `CONTRIBUTING.md`, and this changelog.

### Changed

* The single-host `docker-compose.yml` now binds port 8000 to loopback by
  default; use the production stack for public hosting.
* Container image moved to `python:3.14-slim`; the test matrix now covers
  3.11–3.14.
* GitHub Actions refreshed (checkout, setup-python, buildx, login, metadata)
  and Trivy bumped to `0.36.0`, whose older tag had been removed upstream and
  was failing every scan job. All third-party actions are now pinned to full
  commit SHAs to defend against mutable-tag supply-chain attacks.

### Removed

* Deprecated TypeScript prototype, ad-hoc root scripts, Zoho Creator/Deluge
  exports, generated report JSON, and stale setup guides that referenced them.
  The Python server, `README.md`, and `DEPLOY.md` are the single source of truth.

## [1.0.0] - 2026-10-19

### Added

* Multi-tenant connection portal: OIDC sign-in, per-user Zoho client
  credentials, encrypted credential store (SQLite + Fernet), and per-user MCP
  API keys.
* Full Zoho app catalog (46 apps) with a generic `zoho_api_request` tool and
  `list_zoho_apps` discovery.
* Scope presets (`recommended`, `all`, `everything`) with a verified/unverified
  split so unverified scopes never break consent.
* stdio and streamable-HTTP transports with bearer authentication; binding to a
  non-loopback address without a credential is refused.

[Unreleased]: https://github.com/aceAaronCharles/Zoho-MCP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/aceAaronCharles/Zoho-MCP/releases/tag/v1.0.0
