"""Apply plain-SQL migrations from ``migrations/`` in filename order.

Each file is named ``NNNN_description.sql`` and runs once, inside its own transaction. Applied
versions are recorded in ``schema_migrations``. A Postgres advisory lock stops two deploys from
migrating at the same time. Migrations only move forward: to undo one, write a new one.

Run with ``cairn-migrate`` (or ``python -m cairn_api.migrate``); it reads ``CAIRN_DATABASE_URL``.
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg

from cairn_api.config import get_settings
from cairn_api.db import connect

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
FILENAME = re.compile(r"^(?P<version>\d{4})_[a-z0-9_]+\.sql$")
LOCK_KEY = 4_217_001  # Arbitrary, fixed advisory-lock id for migrations.


@dataclass(frozen=True)
class Migration:
    version: str
    path: Path


def discover(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Return migrations sorted by version, rejecting badly named or duplicate files."""
    migrations: dict[str, Migration] = {}
    for path in sorted(directory.glob("*.sql")):
        match = FILENAME.match(path.name)
        if match is None:
            raise ValueError(f"Migration file name must look like 0001_name.sql: {path.name}")
        version = match["version"]
        if version in migrations:
            raise ValueError(f"Two migrations share version {version}")
        migrations[version] = Migration(version=version, path=path)
    return [migrations[v] for v in sorted(migrations)]


def apply(
    conn: psycopg.Connection[tuple[object, ...]], directory: Path = MIGRATIONS_DIR
) -> list[str]:
    """Apply pending migrations and return the versions applied."""
    conn.autocommit = True
    conn.execute("SELECT pg_advisory_lock(%s)", (LOCK_KEY,))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    text PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
        newly_applied: list[str] = []
        for migration in discover(directory):
            if migration.version in applied:
                continue
            with conn.transaction():
                conn.execute(migration.path.read_text())
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)", (migration.version,)
                )
            newly_applied.append(migration.version)
        return newly_applied
    finally:
        conn.execute("SELECT pg_advisory_unlock(%s)", (LOCK_KEY,))


def main() -> int:
    database_url = get_settings().database_url
    if database_url is None:
        print("CAIRN_DATABASE_URL is not set.", file=sys.stderr)
        return 1
    with connect(database_url) as conn:
        versions = apply(conn)
    print(f"Applied {len(versions)} migration(s): {', '.join(versions) or 'none pending'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
