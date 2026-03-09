from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime


def main() -> None:
    db_path = Path("strikeedge.db")
    migrations_dir = Path("migrations")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        existing = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}

        for migration_file in sorted(migrations_dir.glob("*.sql")):
            version = migration_file.name
            if version in existing:
                continue
            sql = migration_file.read_text(encoding="utf-8")
            try:
                conn.executescript(sql)
            except sqlite3.OperationalError as exc:
                # Keep migrations idempotent when columns/tables were already created by metadata bootstrapping.
                if "duplicate column name" not in str(exc).lower():
                    raise
            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES(?, ?)",
                (version, datetime.utcnow().isoformat()),
            )
        conn.commit()
    finally:
        conn.close()
    print("Migrations applied successfully.")


if __name__ == "__main__":
    main()
