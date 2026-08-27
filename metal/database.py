"""
Metal Inspection Database
=========================
Manages database/metal_inspections.db

Tables
------
inspections
    id, inspection_id, timestamp, material, image_path,
    defect_count, quality_score, severity, status, remarks, inspector

defects
    id, inspection_id (FK), defect_class, confidence, x1, y1, x2, y2
"""

import sqlite3
from pathlib import Path

ROOT_DIR     = Path(__file__).resolve().parent.parent
DATABASE_DIR = ROOT_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "metal_inspections.db"


# ──────────────────────────────────────────────────────────────────────
# Connection helper
# ──────────────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ──────────────────────────────────────────────────────────────────────
# Schema creation
# ──────────────────────────────────────────────────────────────────────

def create_database():
    """Create tables if they do not already exist."""
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspections (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id TEXT    UNIQUE NOT NULL,
            timestamp     TEXT    NOT NULL,
            material      TEXT    NOT NULL DEFAULT 'Metal',
            image_path    TEXT,
            defect_count  INTEGER NOT NULL DEFAULT 0,
            quality_score INTEGER NOT NULL DEFAULT 100,
            severity      TEXT    NOT NULL DEFAULT 'LOW',
            status        TEXT    NOT NULL DEFAULT 'PASS',
            remarks       TEXT    DEFAULT '',
            inspector     TEXT    DEFAULT 'AI System'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defects (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id TEXT    NOT NULL,
            defect_class  TEXT    NOT NULL,
            confidence    REAL    NOT NULL,
            x1            INTEGER,
            y1            INTEGER,
            x2            INTEGER,
            y2            INTEGER,
            FOREIGN KEY (inspection_id)
                REFERENCES inspections (inspection_id)
                ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────
# Write
# ──────────────────────────────────────────────────────────────────────

def save_inspection(
    inspection_id: str,
    timestamp:     str,
    image_path:    str,
    defect_count:  int,
    quality_score: int,
    severity:      str,
    status:        str,
    remarks:       str,
    defects:       list,
    inspector:     str = "AI System",
    material:      str = "Metal",
):
    """
    Persist one inspection and its associated defect rows.

    Parameters
    ----------
    defects : list of dict
        Each dict must contain: defect_class, confidence, x1, y1, x2, y2
    """
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO inspections (
            inspection_id, timestamp, material, image_path,
            defect_count, quality_score, severity, status, remarks, inspector
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            inspection_id, timestamp, material, image_path,
            defect_count, quality_score, severity, status, remarks, inspector,
        ),
    )

    for d in defects:
        cursor.execute(
            """
            INSERT INTO defects (
                inspection_id, defect_class, confidence, x1, y1, x2, y2
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inspection_id,
                d.get("class_name", d.get("defect_class", "unknown")),
                d.get("confidence", 0.0),
                d.get("x1", 0),
                d.get("y1", 0),
                d.get("x2", 0),
                d.get("y2", 0),
            ),
        )

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────
# Read
# ──────────────────────────────────────────────────────────────────────

def get_inspections(limit: int = 100) -> list:
    """Return the latest *limit* inspection rows (newest first)."""
    conn = _connect()
    rows = conn.execute(
        """
        SELECT id, inspection_id, timestamp, material, image_path,
               defect_count, quality_score, severity, status, remarks, inspector
        FROM inspections
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_defects_for_inspection(inspection_id: str) -> list:
    """Return all defect rows for a given inspection_id."""
    conn = _connect()
    rows = conn.execute(
        """
        SELECT defect_class, confidence, x1, y1, x2, y2
        FROM defects
        WHERE inspection_id = ?
        ORDER BY id ASC
        """,
        (inspection_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_status() -> bool:
    """Return True if the database is reachable."""
    try:
        conn = _connect()
        conn.execute("SELECT 1 FROM inspections LIMIT 1")
        conn.close()
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    create_database()
    print("=" * 50)
    print("Metal Inspection Database Ready")
    print(f"Location : {DATABASE_PATH}")
    print("=" * 50)
