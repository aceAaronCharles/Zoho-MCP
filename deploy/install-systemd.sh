#!/usr/bin/env bash
# Install the Zoho MCP server as a hardened systemd service (no Docker).
#
#   sudo ./deploy/install-systemd.sh
#   sudo ./deploy/install-systemd.sh --repo-dir /opt/zoho-mcp --user zoho-mcp
#   sudo ./deploy/install-systemd.sh --no-start
#
# Idempotent: safe to re-run after a `git pull` to refresh the venv and units.
set -euo pipefail

REPO_DIR="/opt/zoho-mcp"
RUN_USER="zoho-mcp"
START="yes"

while [ $# -gt 0 ]; do
    case "$1" in
        --repo-dir) REPO_DIR="$2"; shift 2 ;;
        --user)     RUN_USER="$2"; shift 2 ;;
        --no-start) START="no"; shift ;;
        -h|--help)  sed -n '2,7p' "$0"; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

if [ "$(id -u)" -ne 0 ]; then
    echo "error: run as root (sudo $0)" >&2
    exit 1
fi

case "$REPO_DIR" in
    /home/*)
        echo "error: the unit sets ProtectHome=true, so /home is hidden from the service." >&2
        echo "       Use a path outside /home, e.g. /opt/zoho-mcp." >&2
        exit 1
        ;;
esac

log() { printf '\033[36m==>\033[0m %s\n' "$*"; }

if [ ! -f "$REPO_DIR/src/server.py" ]; then
    echo "error: $REPO_DIR does not look like the Zoho-MCP repository." >&2
    echo "       Clone it first:  git clone <repo-url> $REPO_DIR" >&2
    exit 1
fi

log "Checking prerequisites"
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "error: Python 3.11 or newer is required" >&2
    exit 1
fi

log "Creating service account '$RUN_USER'"
if ! id -u "$RUN_USER" >/dev/null 2>&1; then
    useradd --system --create-home --home-dir "/var/lib/$RUN_USER" --shell /usr/sbin/nologin "$RUN_USER"
fi

log "Preparing $REPO_DIR"
chown -R "$RUN_USER:$RUN_USER" "$REPO_DIR"

if [ ! -x "$REPO_DIR/.venv/bin/python" ]; then
    log "Creating virtualenv"
    python3 -m venv "$REPO_DIR/.venv"
fi
log "Installing Python dependencies"
"$REPO_DIR/.venv/bin/python" -m pip install --upgrade pip >/dev/null
"$REPO_DIR/.venv/bin/python" -m pip install -r "$REPO_DIR/requirements.txt"

log "Creating state, log and backup directories"
install -d -o "$RUN_USER" -g "$RUN_USER" -m 0750 "/var/lib/$RUN_USER"
install -d -o "$RUN_USER" -g "$RUN_USER" -m 0750 "/var/log/$RUN_USER"
install -d -o "$RUN_USER" -g "$RUN_USER" -m 0750 "/var/backups/$RUN_USER"

log "Installing /etc/zoho-mcp/zoho-mcp.env"
install -d -m 0750 -o root -g "$RUN_USER" /etc/zoho-mcp
ENV_FILE=/etc/zoho-mcp/zoho-mcp.env
if [ ! -f "$ENV_FILE" ]; then
    install -m 0640 -o root -g "$RUN_USER" \
        "$REPO_DIR/deploy/systemd/zoho-mcp.env.example" "$ENV_FILE"
    echo "    created a template; edit it:  sudoedit $ENV_FILE"
else
    echo "    keeping the existing environment file"
fi

log "Installing systemd units"
install -m 0644 "$REPO_DIR/deploy/systemd/zoho-mcp.service" /etc/systemd/system/zoho-mcp.service
install -m 0644 "$REPO_DIR/deploy/systemd/zoho-mcp-backup.service" /etc/systemd/system/zoho-mcp-backup.service
install -m 0644 "$REPO_DIR/deploy/systemd/zoho-mcp-backup.timer" /etc/systemd/system/zoho-mcp-backup.timer
chmod 0755 "$REPO_DIR/deploy/backup.sh"
systemctl daemon-reload

log "Enabling the nightly backup timer"
systemctl enable --now zoho-mcp-backup.timer

has()     { grep -qE "^$1=.+" "$ENV_FILE"; }
is_true() { grep -qiE "^$1=(true|1|yes|on)" "$ENV_FILE"; }

configured="no"
if has MCP_HTTP_TOKEN; then
    configured="yes"
elif is_true PORTAL_ENABLED && has MCP_SECRET_KEY; then
    configured="yes"
fi

if [ "$START" = "yes" ] && [ "$configured" = "yes" ]; then
    log "Starting the service"
    systemctl enable --now zoho-mcp.service
    sleep 1
    systemctl --no-pager --full status zoho-mcp.service || true
else
    systemctl enable zoho-mcp.service >/dev/null
    cat <<EOF

==> Installed, but NOT started yet.

Edit $ENV_FILE and set MCP_SECRET_KEY / OIDC settings (or MCP_HTTP_TOKEN),
then:

    sudo systemctl restart zoho-mcp.service
    sudo systemctl status zoho-mcp.service
    journalctl -u zoho-mcp.service -f

Put a TLS-terminating reverse proxy in front (see DEPLOY.md) and point MCP
clients at https://<host>/mcp.
EOF
fi
