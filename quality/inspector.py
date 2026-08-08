import sqlite3
from pathlib import Path

# ======================================================
# DATABASE PATH
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = ROOT_DIR / "database" / "inspection.db"


# ======================================================
# SAVE INSPECTION
# ======================================================

def save_inspection(
    inspection_id,
    timestamp,
    image_path,
    scratches,
    dents,
    rust,
    other,
    total_defects,
    status,
    inspector="AI System"
):

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inspections(
            inspection_id,
            timestamp,
            image_path,
            scratches,
            dents,
            rust,
            other,
            total_defects,
            status,
            inspector
        )
        VALUES(?,?,?,?,?,?,?,?,?,?)
    """, (
        inspection_id,
        timestamp,
        image_path,
        scratches,
        dents,
        rust,
        other,
        total_defects,
        status,
        inspector
    ))

    conn.commit()
    conn.close()

    print("======================================")
    print("Inspection Saved Successfully")
    print(f"Inspection ID : {inspection_id}")
    print(f"Status        : {status}")
    print("======================================")