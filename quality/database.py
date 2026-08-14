import sqlite3
from pathlib import Path


# ======================================================
# PATHS
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = ROOT_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "inspection.db"


# ======================================================
# CREATE / UPDATE DATABASE
# ======================================================

def create_database():

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # --------------------------------------------------
    # Create table if it doesn't exist
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Check existing columns
    # --------------------------------------------------

    cursor.execute("PRAGMA table_info(inspections)")

    existing_columns = {
        column[1]
        for column in cursor.fetchall()
    }

    # --------------------------------------------------
    # Add new quality columns if missing
    # --------------------------------------------------

    if "quality_score" not in existing_columns:

        cursor.execute("""
            ALTER TABLE inspections
            ADD COLUMN quality_score INTEGER DEFAULT 100
        """)

        print("✅ Added column: quality_score")


    if "severity" not in existing_columns:

        cursor.execute("""
            ALTER TABLE inspections
            ADD COLUMN severity TEXT DEFAULT 'NONE'
        """)

        print("✅ Added column: severity")


    if "remarks" not in existing_columns:

        cursor.execute("""
            ALTER TABLE inspections
            ADD COLUMN remarks TEXT DEFAULT ''
        """)

        print("✅ Added column: remarks")


    conn.commit()
    conn.close()


    # ==================================================
    # RESULT
    # ==================================================

    print("=" * 50)
    print("Quality Inspection Database Ready")
    print("=" * 50)

    print(f"Database : {DATABASE_PATH}")

    print()
    print("Current inspection columns:")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(inspections)")

    columns = cursor.fetchall()

    for column in columns:

        print(f"  - {column[1]}")

    conn.close()

    print("=" * 50)


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":

    create_database()