import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = ROOT_DIR / "database" / "inspection.db"


def show_history():

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            inspection_id,
            timestamp,
            total_defects,
            status
        FROM inspections
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    print("\n")
    print("=" * 75)
    print("STEEL QUALITY INSPECTION HISTORY")
    print("=" * 75)

    if len(rows) == 0:
        print("No inspection records found.")

    else:

        for row in rows:

            print(
                f"{row[0]} | {row[1]} | "
                f"Defects: {row[2]} | {row[3]}"
            )

    print("=" * 75)

    conn.close()


if __name__ == "__main__":
    show_history()