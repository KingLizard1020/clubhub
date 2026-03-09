from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parent / "club_hub.db"


def get_connection():
    """Return a SQLite connection configured the same way everywhere in the app."""
    conn = sqlite3.connect(DB_PATH)
    # sqlite3.Row lets the rest of the code read columns by name
    conn.row_factory = sqlite3.Row
    # Foreign keys are disabled by default in SQLite, so enable them on every connection to keep relationships between tables honest.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_all(query, params=()):
    """Run a read query and return all rows as plain dictionaries."""
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def fetch_one(query, params=()):
    """Run a read query and return one row as a dictionary, if it exists."""
    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def execute(query, params=()):
    """Run a write query for simple cases that do not need custom transaction logic."""
    with get_connection() as conn:
        conn.execute(query, params)
        conn.commit()
