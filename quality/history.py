import sqlite3
from pathlib import Path


# ======================================================
# DATABASE PATH
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = ROOT_DIR / "database" / "inspection.db"


# ======================================================
# SHOW INSPECTION HISTORY
# ======================================================

def show_history():

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            inspection_id,
            timestamp,
            total_defects,
            quality_score,
            severity,
            status
        FROM inspections
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    conn.close()


    # ==================================================
    # HEADER
    # ==================================================

    print()
    print("=" * 115)
    print("STEEL QUALITY INSPECTION HISTORY")
    print("=" * 115)

    if not records:

        print("No inspection records found.")

        print("=" * 115)

        return


    # ==================================================
    # TABLE HEADER
    # ==================================================

    print(
        f"{'INSPECTION ID':<25}"
        f"{'DATE & TIME':<20}"
        f"{'DEFECTS':<10}"
        f"{'SCORE':<10}"
        f"{'SEVERITY':<12}"
        f"{'STATUS':<10}"
    )

    print("-" * 115)


    # ==================================================
    # RECORDS
    # ==================================================

    for record in records:

        (
            inspection_id,
            timestamp,
            total_defects,
            quality_score,
            severity,
            status
        ) = record


        print(
            f"{inspection_id:<25}"
            f"{timestamp:<20}"
            f"{total_defects:<10}"
            f"{str(quality_score) + '%':<10}"
            f"{severity:<12}"
            f"{status:<10}"
        )


    # ==================================================
    # FOOTER
    # ==================================================

    print("=" * 115)


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":

    show_history()