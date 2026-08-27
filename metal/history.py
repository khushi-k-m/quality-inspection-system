"""
MetalHistory
============
Retrieves and displays real inspection records from
database/metal_inspections.db.
"""

from metal.database import get_inspections, get_defects_for_inspection


class MetalHistory:
    """Retrieve and display Metal inspection history."""

    def get_inspections(self, limit: int = 100) -> list:
        """
        Return the latest *limit* inspection records (newest first).

        Returns
        -------
        list of dict — each dict contains all inspections table columns.
        """
        return get_inspections(limit=limit)

    def get_inspection_with_defects(self, inspection_id: str) -> dict:
        """
        Return a single inspection record together with its defect rows.

        Returns
        -------
        dict with keys: inspection (dict), defects (list of dict)
        Returns None if inspection_id is not found.
        """
        records = get_inspections(limit=10000)
        inspection = next(
            (r for r in records if r["inspection_id"] == inspection_id),
            None,
        )
        if inspection is None:
            return None

        return {
            "inspection": inspection,
            "defects":    get_defects_for_inspection(inspection_id),
        }

    def print_history(self, limit: int = 100):
        """Print a formatted history table to stdout."""
        records = self.get_inspections(limit=limit)

        print()
        print("=" * 110)
        print("METAL SURFACE INSPECTION HISTORY")
        print("=" * 110)

        if not records:
            print("No inspection records found.")
            print("=" * 110)
            return

        print(
            f"{'INSPECTION ID':<28}"
            f"{'DATE & TIME':<22}"
            f"{'DEFECTS':<10}"
            f"{'SCORE':<8}"
            f"{'SEVERITY':<10}"
            f"{'STATUS':<10}"
            f"{'INSPECTOR'}"
        )
        print("-" * 110)

        for r in records:
            print(
                f"{r['inspection_id']:<28}"
                f"{r['timestamp']:<22}"
                f"{r['defect_count']:<10}"
                f"{str(r['quality_score']) + '%':<8}"
                f"{r['severity']:<10}"
                f"{r['status']:<10}"
                f"{r['inspector']}"
            )

        print("=" * 110)


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    MetalHistory().print_history()
