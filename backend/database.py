import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = ROOT_DIR / "database" / "inspection.db"


def get_db():
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def db_status():
    try:
        conn = get_db()
        conn.execute("SELECT 1 FROM inspections LIMIT 1")
        conn.close()
        return True
    except Exception:
        return False
