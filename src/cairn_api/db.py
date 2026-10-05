"""Database access."""

import psycopg


def connect(database_url: str) -> psycopg.Connection[tuple[object, ...]]:
    """Open a connection. Callers own it and should use it as a context manager."""
    return psycopg.connect(database_url, connect_timeout=5)


def ping(database_url: str) -> bool:
    """Return True if the database answers a trivial query."""
    try:
        with connect(database_url) as conn:
            conn.execute("SELECT 1")
    except psycopg.Error:
        return False
    return True
