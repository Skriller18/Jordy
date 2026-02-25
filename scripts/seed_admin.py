#!/usr/bin/env python3
"""
Bootstrap the first admin user for the Jordy dashboard.

Instead of creating a bare User row (which has no way to establish a session),
this script inserts InviteToken rows.  Visit the printed URL(s) in the dashboard
to claim your account and set up a session cookie.

Usage
-----
  python scripts/seed_admin.py                                  # auto-detect DB
  python scripts/seed_admin.py --admin-label "Subhash" --viewer-label "Alice"
  python scripts/seed_admin.py --db dashboard/dev.db
"""

from __future__ import annotations

import argparse
import hashlib
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _detect_db_path() -> Path:
    """Read DATABASE_URL from dashboard/.env and return the SQLite file path."""
    env_file = _repo_root() / "dashboard" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL"):
                _, _, value = line.partition("=")
                value = value.strip().strip('"').strip("'")
                # Prisma format: "file:./dev.db" or absolute path
                if value.startswith("file:"):
                    value = value[len("file:"):]
                path = Path(value)
                if not path.is_absolute():
                    # Prisma resolves relative paths from the prisma/ directory
                    # (where schema.prisma lives), not the project root.
                    prisma_dir = _repo_root() / "dashboard" / "prisma"
                    path = prisma_dir / path
                return path
    # Fallback
    return _repo_root() / "dashboard" / "dev.db"


def _detect_app_base_url() -> str:
    env_file = _repo_root() / "dashboard" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("APP_BASE_URL"):
                _, _, value = line.partition("=")
                return value.strip().strip('"').strip("'").rstrip("/")
    return "http://localhost:3000"


def _sha256(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _insert_invite(
    conn: sqlite3.Connection,
    *,
    role: str,
    label: str | None,
) -> str:
    """Insert an InviteToken row and return the raw (unhashed) token."""
    raw_token = secrets.token_hex(24)          # 48-char hex string
    token_hash = _sha256(raw_token)
    row_id = str(uuid.uuid4())
    created_at = _now_iso()

    conn.execute(
        """
        INSERT INTO InviteToken (id, createdAt, tokenHash, label, role)
        VALUES (?, ?, ?, ?, ?)
        """,
        (row_id, created_at, token_hash, label, role),
    )
    conn.commit()
    return raw_token


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the first Jordy dashboard admin.")
    parser.add_argument("--db", help="Path to the dashboard SQLite file (auto-detected if omitted)")
    parser.add_argument("--admin-label", default=None, help="Label for the ADMIN invite token")
    parser.add_argument("--viewer-label", default=None, help="Label for the VIEWER invite token")
    parser.add_argument("--no-viewer", action="store_true", help="Skip creating the VIEWER invite")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else _detect_db_path()
    base_url = _detect_app_base_url()

    if not db_path.exists():
        print(f"❌  Database not found at: {db_path}")
        print("    Run `npx prisma migrate dev` inside the dashboard/ folder first.")
        raise SystemExit(1)

    conn = sqlite3.connect(str(db_path))
    try:
        # Verify the InviteToken table exists
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "InviteToken" not in tables:
            print("❌  InviteToken table not found.  Run `npx prisma migrate dev` first.")
            raise SystemExit(1)

        admin_token = _insert_invite(conn, role="ADMIN", label=args.admin_label or "bootstrap-admin")
        print()
        print("✅  ADMIN invite (one-time use):")
        print(f"    {base_url}/invite/{admin_token}")
        print("    Visit this URL to claim your admin account and log in.")

        if not args.no_viewer:
            viewer_token = _insert_invite(conn, role="VIEWER", label=args.viewer_label or "bootstrap-viewer")
            print()
            print("✅  VIEWER invite (one-time use, share with a trusted user):")
            print(f"    {base_url}/invite/{viewer_token}")

        print()
        print("Once you've claimed the admin invite, you can create more invites at:")
        print(f"    {base_url}/admin/invites")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
