import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from app.models.errors import DataIntegrityError

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def parse_datetime(value):
    return datetime.fromisoformat(value) if value else None


class SqliteDatabase:
    """Opens one connection per unit of work: commit on success, rollback on error."""

    def __init__(self, path):
        self.path = str(path)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except sqlite3.IntegrityError as error:
            conn.rollback()
            raise DataIntegrityError(str(error)) from error
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self):
        """Drop and recreate all tables."""
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    def has_schema(self):
        if not Path(self.path).exists():
            return False
        with self.connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'orders'"
            ).fetchone()
        return row is not None
