"""
SQLite persistence for the multi-tenant portal.

Every Zoho client secret and OAuth token is encrypted with the master key
(see :mod:`src.portal.crypto`) before it is written.  The database only ever
holds ciphertext for those columns.  Connections are opened per operation so
the module is safe to use from Starlette's thread pool.
"""

import logging
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

from . import crypto

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    subject TEXT NOT NULL,
    email TEXT,
    name TEXT,
    picture TEXT,
    created_at REAL NOT NULL,
    last_login_at REAL,
    UNIQUE(provider, subject)
);

CREATE TABLE IF NOT EXISTS connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    client_id TEXT NOT NULL,
    client_secret_enc TEXT NOT NULL,
    dc TEXT NOT NULL DEFAULT 'com',
    scopes TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    refresh_token_enc TEXT,
    access_token_enc TEXT,
    access_expires_at REAL,
    api_domain TEXT,
    accounts_domain TEXT,
    granted_scopes TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL UNIQUE,
    prefix TEXT NOT NULL,
    label TEXT,
    created_at REAL NOT NULL,
    last_used_at REAL,
    revoked INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    connection_id INTEGER NOT NULL,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_users_subject ON users(provider, subject);
"""


class Database:
    """Thin data-access layer over SQLite."""

    def __init__(self, path: str, state_ttl: int = 600):
        self.path = path
        self.state_ttl = state_ttl

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def upsert_user(
        self,
        provider: str,
        subject: str,
        email: Optional[str],
        name: Optional[str],
        picture: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (provider, subject, email, name, picture, created_at, last_login_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, subject) DO UPDATE SET
                    email=excluded.email,
                    name=excluded.name,
                    picture=excluded.picture,
                    last_login_at=excluded.last_login_at
                """,
                (provider, subject, email, name, picture, now, now),
            )
            row = conn.execute(
                "SELECT * FROM users WHERE provider=? AND subject=?",
                (provider, subject),
            ).fetchone()
        return dict(row)

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def count_users(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------
    def create_connection(
        self,
        user_id: int,
        client_id: str,
        client_secret: str,
        dc: str,
        scopes: str,
        redirect_uri: str,
    ) -> Dict[str, Any]:
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO connections (
                    user_id, client_id, client_secret_enc, dc, scopes, redirect_uri,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    client_id=excluded.client_id,
                    client_secret_enc=excluded.client_secret_enc,
                    dc=excluded.dc,
                    scopes=excluded.scopes,
                    redirect_uri=excluded.redirect_uri,
                    refresh_token_enc=NULL,
                    access_token_enc=NULL,
                    access_expires_at=NULL,
                    granted_scopes=NULL,
                    status='pending',
                    error=NULL,
                    updated_at=excluded.updated_at
                """,
                (
                    user_id,
                    client_id,
                    crypto.encrypt(client_secret),
                    dc,
                    scopes,
                    redirect_uri,
                    now,
                    now,
                ),
            )
            row = conn.execute(
                "SELECT * FROM connections WHERE user_id=?", (user_id,)
            ).fetchone()
        return self._decode_connection(row)

    def get_connection(self, connection_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM connections WHERE id=?", (connection_id,)
            ).fetchone()
        return self._decode_connection(row) if row else None

    def get_connection_for_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM connections WHERE user_id=?", (user_id,)
            ).fetchone()
        return self._decode_connection(row) if row else None

    def store_tokens(
        self,
        connection_id: int,
        tokens: Dict[str, Any],
        access_expires_at: Optional[float] = None,
        granted_scopes: Optional[str] = None,
        api_domain: Optional[str] = None,
        accounts_domain: Optional[str] = None,
    ) -> None:
        """Persist tokens returned by Zoho, leaving known values in place."""
        sets = ["updated_at=?"]
        values: List[Any] = [time.time()]
        if tokens.get("refresh_token"):
            sets.append("refresh_token_enc=?")
            values.append(crypto.encrypt(tokens["refresh_token"]))
        if tokens.get("access_token"):
            sets.append("access_token_enc=?")
            values.append(crypto.encrypt(tokens["access_token"]))
        if access_expires_at is not None:
            sets.append("access_expires_at=?")
            values.append(access_expires_at)
        if granted_scopes:
            sets.append("granted_scopes=?")
            values.append(granted_scopes)
        if api_domain:
            sets.append("api_domain=?")
            values.append(api_domain)
        if accounts_domain:
            sets.append("accounts_domain=?")
            values.append(accounts_domain)
        if tokens.get("access_token") or tokens.get("refresh_token"):
            sets.append("status=?")
            values.append("connected")
            sets.append("error=?")
            values.append(None)
        values.append(connection_id)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE connections SET {', '.join(sets)} WHERE id=?", values
            )

    def set_connection_status(
        self, connection_id: int, status: str, error: Optional[str] = None
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE connections SET status=?, error=?, updated_at=? WHERE id=?",
                (status, error, time.time(), connection_id),
            )

    def delete_connection(self, connection_id: int, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM connections WHERE id=? AND user_id=?",
                (connection_id, user_id),
            )

    @staticmethod
    def _decode_connection(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        data["client_secret"] = crypto.decrypt(data.pop("client_secret_enc", None))
        data["refresh_token"] = crypto.decrypt(data.pop("refresh_token_enc", None))
        data["access_token"] = crypto.decrypt(data.pop("access_token_enc", None))
        return data

    # ------------------------------------------------------------------
    # API keys
    # ------------------------------------------------------------------
    def create_api_key(
        self, user_id: int, key_hash: str, prefix: str, label: Optional[str]
    ) -> Dict[str, Any]:
        now = time.time()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO api_keys (user_id, key_hash, prefix, label, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, key_hash, prefix, label, now),
            )
            key_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM api_keys WHERE id=?", (key_id,)).fetchone()
        return dict(row)

    def list_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM api_keys WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def find_api_key(self, key_hash: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE key_hash=? AND revoked=0",
                (key_hash,),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE api_keys SET last_used_at=? WHERE id=?",
                    (time.time(), row["id"]),
                )
        return dict(row) if row else None

    def revoke_api_key(self, key_id: int, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE api_keys SET revoked=1 WHERE id=? AND user_id=?",
                (key_id, user_id),
            )

    def count_api_keys(self) -> int:
        with self._connect() as conn:
            return int(
                conn.execute("SELECT COUNT(*) FROM api_keys WHERE revoked=0").fetchone()[0]
            )

    # ------------------------------------------------------------------
    # OAuth state (CSRF protection for the Zoho redirect)
    # ------------------------------------------------------------------
    def create_state(self, state: str, user_id: int, connection_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO oauth_states (state, user_id, connection_id, created_at) VALUES (?, ?, ?, ?)",
                (state, user_id, connection_id, time.time()),
            )

    def consume_state(self, state: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM oauth_states WHERE state=?", (state,)
            ).fetchone()
            conn.execute("DELETE FROM oauth_states WHERE state=?", (state,))
            conn.execute(
                "DELETE FROM oauth_states WHERE created_at < ?",
                (now - self.state_ttl,),
            )
        if not row:
            return None
        if now - row["created_at"] > self.state_ttl:
            return None
        return dict(row)
