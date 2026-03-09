from pathlib import Path
import sqlite3

from db import DB_PATH


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"


def column_exists(cursor, table_name, column_name):
    """Check whether a column already exists before attempting a migration."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(column[1] == column_name for column in columns)


def ensure_column(cursor, table_name, column_name, definition):
    """Add a missing column in older local databases without dropping data."""
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def setup_database():
    """Create the schema and apply lightweight additive migrations for local development."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    conn.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        cursor.executescript(file.read())

    # These additive migrations keep an older database usable after the schema grows.
    ensure_column(cursor, "members", "phone", "TEXT")
    ensure_column(cursor, "members", "class_year", "TEXT")
    ensure_column(cursor, "members", "joined_at", "DATE")
    ensure_column(cursor, "members", "notes", "TEXT")
    # SQLite cannot add a column with CURRENT_DATE as a default during ALTER TABLE,
    # so older rows are backfilled after the column exists.
    cursor.execute(
        "UPDATE members SET joined_at = COALESCE(joined_at, date(created_at), date('now'))"
    )

    ensure_column(cursor, "events", "description", "TEXT")
    ensure_column(cursor, "events", "start_time", "TEXT")
    ensure_column(cursor, "events", "end_time", "TEXT")
    ensure_column(cursor, "events", "location", "TEXT")
    ensure_column(cursor, "events", "category", "TEXT DEFAULT 'other'")
    ensure_column(cursor, "events", "is_required", "INTEGER NOT NULL DEFAULT 0")

    ensure_column(cursor, "attendance", "attendance_status", "TEXT NOT NULL DEFAULT 'present'")
    ensure_column(cursor, "attendance", "check_in_method", "TEXT NOT NULL DEFAULT 'self'")

    conn.commit()
    conn.close()

    print(f"Success: Database '{DB_PATH.name}' created and tables initialized!")

if __name__ == "__main__":
    setup_database()