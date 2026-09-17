"""
Welding Inspection Database
===========================
Manages database/welding_inspections.db

Tables
------
inspections
    id, inspection_id, timestamp, material, image_path,
    defect_count, quality_score, severity, status, remarks, inspector

defects
    id, inspection_id (FK), defect_class, confidence, x1, y1, x2, y2

Note: Welding defect_class values are 'good_weld' and 'bad_weld'.
      'good_weld' detections are NOT defects (filtered by generic evaluator).
"""

import sqlite3
from pathlib import Path

ROOT_DIR     = Path(__file__).resolve().parent.parent
DATABASE_DIR = ROOT_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "welding_inspections.db"


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
            material      TEXT    NOT NULL DEFAULT 'Welding',
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
    material:      str = "Welding",
):
    """
    Persist one inspection and its associated defect rows.
    
    Args:
        inspection_id: Unique inspection identifier
        timestamp: ISO datetime string
        image_path: File path to the captured/annotated image
        defect_count: Total number of defects detected (excluding good_weld)
        quality_score: 0-100 quality score
        severity: 'LOW', 'MEDIUM', 'HIGH'
        status: 'PASS', 'REWORK', 'FAIL'
        remarks: Human-readable summary
        defects: List of detection dicts with class_name, confidence, x1/y1/x2/y2
        inspector: Username of human inspector (default 'AI System')
        material: Material type (default 'Welding')
    """
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO inspections
           (inspection_id, timestamp, material, image_path, defect_count,
            quality_score, severity, status, remarks, inspector)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (inspection_id, timestamp, material, image_path, defect_count,
         quality_score, severity, status, remarks, inspector),
    )

    for defect in defects:
        cursor.execute(
            """INSERT INTO defects (inspection_id, defect_class, confidence, x1, y1, x2, y2)
               VALUES (?,?,?,?,?,?,?)""",
            (inspection_id,
             defect.get("class_name", defect.get("class", "unknown")),
             defect.get("confidence", 0.0),
             defect.get("x1", 0),
             defect.get("y1", 0),
             defect.get("x2", 0),
             defect.get("y2", 0)),
        )

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────
# Read (inspections)
# ──────────────────────────────────────────────────────────────────────

def get_inspections(limit=100, offset=0, status="", severity="", search=""):
    """
    Retrieve a paginated list of inspections with optional filtering.
    
    Args:
        limit: Number of records to return
        offset: Number of records to skip
        status: Filter by status ('PASS', 'REWORK', 'FAIL', or empty for all)
        severity: Filter by severity ('LOW', 'MEDIUM', 'HIGH', or empty for all)
        search: Search inspection_id substring (case-insensitive)
    
    Returns:
        (total_count, [inspection_dicts])
    """
    conn = _connect()
    cursor = conn.cursor()

    conditions = []
    params = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if severity:
        conditions.append("severity = ?")
        params.append(severity)
    if search:
        conditions.append("inspection_id LIKE ?")
        params.append(f"%{search}%")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # Get total
    total = cursor.execute(
        f"SELECT COUNT(*) FROM inspections {where}",
        params
    ).fetchone()[0]

    # Get paginated results
    rows = cursor.execute(
        f"""SELECT id, inspection_id, timestamp, material, image_path,
                   defect_count, quality_score, severity, status, remarks, inspector
            FROM inspections {where}
            ORDER BY id DESC
            LIMIT ? OFFSET ?""",
        params + [limit, offset]
    ).fetchall()

    conn.close()
    return total, [dict(r) for r in rows]


def get_inspection(inspection_id: str):
    """
    Retrieve a single inspection with all its defects.
    
    Args:
        inspection_id: Unique inspection identifier
    
    Returns:
        Inspection dict with 'defects' list, or None if not found
    """
    conn = _connect()
    cursor = conn.cursor()

    row = cursor.execute(
        """SELECT id, inspection_id, timestamp, material, image_path,
                  defect_count, quality_score, severity, status, remarks, inspector
           FROM inspections WHERE inspection_id = ?""",
        (inspection_id,)
    ).fetchone()

    if row is None:
        conn.close()
        return None

    defects = cursor.execute(
        """SELECT defect_class, confidence, x1, y1, x2, y2
           FROM defects WHERE inspection_id = ?
           ORDER BY id""",
        (inspection_id,)
    ).fetchall()

    conn.close()

    data = dict(row)
    data["defects"] = [dict(d) for d in defects]
    return data


# ──────────────────────────────────────────────────────────────────────
# Analytics
# ──────────────────────────────────────────────────────────────────────

def _parse_date(ts: str):
    from datetime import datetime
    if not ts:
        return None
    for fmt in ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S"]:
        try:
            return datetime.strptime(ts.strip(), fmt).date()
        except ValueError:
            continue
    return None


def get_analytics():
    """Return analytics in the schema expected by Analytics.jsx."""
    conn = _connect()
    cursor = conn.cursor()

    kpi = cursor.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status='PASS'   THEN 1 ELSE 0 END) AS pass_count,
               SUM(CASE WHEN status='REWORK' THEN 1 ELSE 0 END) AS rework_count,
               SUM(CASE WHEN status='FAIL'   THEN 1 ELSE 0 END) AS fail_count,
               AVG(CAST(quality_score AS REAL))                  AS avg_score,
               SUM(defect_count)                                 AS total_defects
        FROM inspections
    """).fetchone()

    total        = kpi["total"]        or 0
    pass_count   = kpi["pass_count"]   or 0
    rework_count = kpi["rework_count"] or 0
    fail_count   = kpi["fail_count"]   or 0
    avg_score    = round(kpi["avg_score"] or 0, 1)
    total_defs   = kpi["total_defects"] or 0

    status_dist = [
        {"status": r["status"], "count": r["count"]}
        for r in cursor.execute(
            "SELECT status, COUNT(*) as count FROM inspections GROUP BY status"
        ).fetchall()
    ]
    severity_dist = [
        {"severity": r["severity"] or "NONE", "count": r["count"]}
        for r in cursor.execute(
            "SELECT severity, COUNT(*) as count FROM inspections GROUP BY severity"
        ).fetchall()
    ]
    defect_dist = [
        {"type": r["defect_class"], "count": r["count"]}
        for r in cursor.execute(
            "SELECT defect_class, COUNT(*) as count FROM defects GROUP BY defect_class"
        ).fetchall()
    ]

    trend_rows = cursor.execute(
        "SELECT inspection_id, timestamp, quality_score FROM inspections ORDER BY id ASC"
    ).fetchall()
    quality_trend = [
        {"inspection_id": r["inspection_id"], "timestamp": r["timestamp"],
         "quality_score": r["quality_score"] or 100}
        for r in trend_rows
    ]

    all_rows = cursor.execute(
        "SELECT timestamp, defect_count FROM inspections ORDER BY id ASC"
    ).fetchall()
    daily_defects: dict = {}
    daily_vol: dict = {}
    for r in all_rows:
        d = _parse_date(r["timestamp"])
        if d:
            k = str(d)
            daily_defects[k] = daily_defects.get(k, 0) + (r["defect_count"] or 0)
            daily_vol[k]     = daily_vol.get(k, 0) + 1

    conn.close()

    return {
        "total_inspections":          total,
        "pass_count":                 pass_count,
        "rework_count":               rework_count,
        "fail_count":                 fail_count,
        "avg_quality_score":          avg_score,
        "total_defects":              total_defs,
        "quality_rate":               round(pass_count   / total * 100 if total else 0, 1),
        "failure_rate":               round(fail_count   / total * 100 if total else 0, 1),
        "rework_rate":                round(rework_count / total * 100 if total else 0, 1),
        "avg_defects_per_inspection": round(total_defs   / total       if total else 0, 2),
        "status_distribution":        status_dist,
        "severity_distribution":      severity_dist,
        "defect_distribution":        defect_dist,
        "quality_trend":              quality_trend,
        "defect_trend":               [{"date": k, "total_defects": v}
                                       for k, v in sorted(daily_defects.items())],
        "daily_volume":               [{"date": k, "count": v}
                                       for k, v in sorted(daily_vol.items())],
    }
