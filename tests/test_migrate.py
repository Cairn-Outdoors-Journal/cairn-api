import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

from cairn_api.db import connect
from cairn_api.migrate import apply, discover

DATABASE_URL = os.environ.get("CAIRN_TEST_DATABASE_URL")
needs_database = pytest.mark.skipif(
    DATABASE_URL is None, reason="set CAIRN_TEST_DATABASE_URL to run database tests"
)


def test_repository_migrations_are_well_formed() -> None:
    versions = [m.version for m in discover()]

    assert versions, "expected at least one migration"
    assert versions == sorted(versions)


def test_rejects_badly_named_files(tmp_path: Path) -> None:
    (tmp_path / "add accounts.sql").write_text("SELECT 1;")

    with pytest.raises(ValueError, match=r"0001_name\.sql"):
        discover(tmp_path)


def test_rejects_duplicate_versions(tmp_path: Path) -> None:
    (tmp_path / "0001_a.sql").write_text("SELECT 1;")
    (tmp_path / "0001_b.sql").write_text("SELECT 1;")

    with pytest.raises(ValueError, match="share version 0001"):
        discover(tmp_path)


@pytest.fixture
def conn() -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    assert DATABASE_URL is not None
    with connect(DATABASE_URL) as conn:
        conn.autocommit = True
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")
        yield conn


@needs_database
def test_applies_all_migrations_once(conn: psycopg.Connection[tuple[object, ...]]) -> None:
    expected = [m.version for m in discover()]

    assert apply(conn) == expected
    assert apply(conn) == []
    recorded = [row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY 1")]
    assert recorded == expected


@needs_database
def test_failed_migration_is_not_recorded(
    conn: psycopg.Connection[tuple[object, ...]], tmp_path: Path
) -> None:
    (tmp_path / "0001_ok.sql").write_text("CREATE TABLE ok (id int);")
    (tmp_path / "0002_broken.sql").write_text("CREATE TABLE broken (id nonsense_type);")

    with pytest.raises(psycopg.errors.UndefinedObject):
        apply(conn, tmp_path)

    recorded = [row[0] for row in conn.execute("SELECT version FROM schema_migrations")]
    assert recorded == ["0001"]
    exists = conn.execute("SELECT to_regclass('broken') IS NOT NULL").fetchone()
    assert exists == (False,)
