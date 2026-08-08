import sqlite3
from pathlib import Path

# ======================================================
# DATABASE PATH
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = ROOT_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "inspection.db"


# ======================================================
# CREATE DATABASE
# ======================================================

def create_database():

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspections (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            inspection_id TEXT UNIQUE,

            timestamp TEXT,

            image_path TEXT,

            scratches INTEGER,

            dents INTEGER,

            rust INTEGER,

            other INTEGER,

            total_defects INTEGER,

            status TEXT,

            inspector TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("=" * 50)
    print("Quality Inspection Database Ready")
    print(DATABASE_PATH)
    print("=" * 50)


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    create_database()