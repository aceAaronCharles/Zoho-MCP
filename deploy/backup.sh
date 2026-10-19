#!/usr/bin/env bash
# Back up the Zoho MCP portal database (and token file) consistently.
#
# Uses SQLite's online backup API via the project virtualenv, so it is safe to
# run while the server is live (including in WAL mode). The database holds
# every user's *encrypted* Zoho credentials; MCP_SECRET_KEY must be backed up
# separately or these archives cannot be restored.
#
# Environment:
#   PORTAL_DB_PATH          default /var/lib/zoho-mcp/portal.db
#   TOKEN_FILE_PATH         default /var/lib/zoho-mcp/.zoho_tokens.json
#   BACKUP_DIR              default /var/backups/zoho-mcp
#   BACKUP_RETENTION_DAYS   default 14
set -euo pipefail

DB="${PORTAL_DB_PATH:-/var/lib/zoho-mcp/portal.db}"
TOKEN_FILE="${TOKEN_FILE_PATH:-/var/lib/zoho-mcp/.zoho_tokens.json}"
DEST_DIR="${BACKUP_DIR:-/var/backups/zoho-mcp}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

PYTHON="/opt/zoho-mcp/.venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="$(command -v python3)"

install -d -m 0750 "$DEST_DIR"

if [ ! -f "$DB" ]; then
    echo "backup: no database at $DB (nothing to do)"
    exit 0
fi

stamp="$(date +%Y%m%d-%H%M%S)"
target="$DEST_DIR/portal-$stamp.db"

echo "backup: copying $DB -> $target"
"$PYTHON" - "$DB" "$target" <<'PY'
import sqlite3
import sys

source, destination = sys.argv[1], sys.argv[2]
src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
try:
    with sqlite3.connect(destination) as dst:
        src.backup(dst)
finally:
    src.close()
PY

gzip -9 "$target"
echo "backup: wrote $target.gz"

if [ -f "$TOKEN_FILE" ]; then
    install -m 0600 "$TOKEN_FILE" "$DEST_DIR/token-$stamp.json"
    echo "backup: wrote $DEST_DIR/token-$stamp.json"
fi

if [ "$RETENTION_DAYS" -gt 0 ]; then
    find "$DEST_DIR" -maxdepth 1 -type f -name 'portal-*.db.gz' -mtime "+$RETENTION_DAYS" -delete
    find "$DEST_DIR" -maxdepth 1 -type f -name 'token-*.json' -mtime "+$RETENTION_DAYS" -delete
    echo "backup: pruned archives older than ${RETENTION_DAYS} days"
fi

echo "backup: done. Keep MCP_SECRET_KEY backed up separately."
