"""
Generic inspection database helper
===================================
Used by fabric, pcb, and welding materials.
Schema mirrors metal_inspections.db exactly.
"""
import sqlite3
from pathlib import Path


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_database(db_path: Path):
    conn = _connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS inspections (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id TEXT    UNIQUE NOT NULL,
            timestamp     TEXT    NOT NULL,
            material      TEXT    NOT NULL,
            image_path    TEXT,
            defect_count  INTEGER NOT NULL DEFAULT 0,
            quality_score INTEGER NOT NULL DEFAULT 100,
            severity      TEXT    NOT NULL DEFAULT 'LOW',
            status        TEXT    NOT NULL DEFAULT 'PASS',
            remarks       TEXT    DEFAULT '',
            inspector     TEXT    DEFAULT 'AI System'
        );
        CREATE TABLE IF NOT EXISTS defects (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id TEXT    NOT NULL,
            defect_class  TEXT    NOT NULL,
            confidence    REAL    NOT NULL,
            x1            INTEGER,
            y1            INTEGER,
            x2            INTEGER,
            y2            INTEGER,
            FOREIGN KEY (inspection_id) REFERENCES inspections (inspection_id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def save_inspection(db_path: Path, inspection_id, timestamp, material, image_path,
                    defect_count, quality_score, severity, status, remarks, defects, inspector="AI System"):
    conn = _connect(db_path)
    conn.execute(
        """INSERT INTO inspections
           (inspection_id, timestamp, material, image_path, defect_count,
            quality_score, severity, status, remarks, inspector)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (inspection_id, timestamp, material, image_path, defect_count,
         quality_score, severity, status, remarks, inspector),
    )
    for d in defects:
        conn.execute(
            """INSERT INTO defects (inspection_id, defect_class, confidence, x1, y1, x2, y2)
               VALUES (?,?,?,?,?,?,?)""",
            (inspection_id,
             d.get("class_name", d.get("defect_class", "unknown")),
             d.get("confidence", 0.0),
             d.get("x1", 0), d.get("y1", 0), d.get("x2", 0), d.get("y2", 0)),
        )
    conn.commit()
    conn.close()


def get_inspections(db_path: Path, limit=100, offset=0, status="", severity="", search=""):
    conn = _connect(db_path)
    conditions, params = [], []
    if status:
        conditions.append("status = ?"); params.append(status)
    if severity:
        conditions.append("severity = ?"); params.append(severity)
    if search:
        conditions.append("inspection_id LIKE ?"); params.append(f"%{search}%")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    total = conn.execute(f"SELECT COUNT(*) FROM inspections {where}", params).fetchone()[0]
    rows  = conn.execute(
        f"""SELECT id, inspection_id, timestamp, material, image_path,
                   defect_count, quality_score, severity, status, remarks, inspector
            FROM inspections {where} ORDER BY id DESC LIMIT ? OFFSET ?""",
        params + [limit, offset],
    ).fetchall()
    conn.close()
    return total, [dict(r) for r in rows]


def get_inspection(db_path: Path, inspection_id: str):
    conn = _connect(db_path)
    row = conn.execute(
        """SELECT id, inspection_id, timestamp, material, image_path,
                  defect_count, quality_score, severity, status, remarks, inspector
           FROM inspections WHERE inspection_id = ?""",
        (inspection_id,),
    ).fetchone()
    defects = conn.execute(
        "SELECT defect_class, confidence, x1, y1, x2, y2 FROM defects WHERE inspection_id = ? ORDER BY id",
        (inspection_id,),
    ).fetchall() if row else []
    conn.close()
    if row is None:
        return None
    data = dict(row)
    data["defects"] = [dict(d) for d in defects]
    return data


def get_analytics(db_path: Path):
    conn = _connect(db_path)
    kpi = conn.execute("""
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
        for r in conn.execute("SELECT status, COUNT(*) as count FROM inspections GROUP BY status").fetchall()
    ]
    severity_dist = [
        {"severity": r["severity"] or "LOW", "count": r["count"]}
        for r in conn.execute("SELECT severity, COUNT(*) as count FROM inspections GROUP BY severity").fetchall()
    ]
    defect_dist = [
        {"type": r["defect_class"], "count": r["count"]}
        for r in conn.execute("SELECT defect_class, COUNT(*) as count FROM defects GROUP BY defect_class").fetchall()
    ]

    all_rows = conn.execute(
        "SELECT timestamp, defect_count, quality_score, inspection_id FROM inspections ORDER BY id ASC"
    ).fetchall()
    conn.close()

    daily_defects, daily_vol = {}, {}
    quality_trend = []
    for r in all_rows:
        quality_trend.append({"inspection_id": r["inspection_id"], "quality_score": r["quality_score"] or 100})
        ts = r["timestamp"] or ""
        d  = _parse_date(ts)
        if d:
            daily_defects[d] = daily_defects.get(d, 0) + (r["defect_count"] or 0)
            daily_vol[d]     = daily_vol.get(d, 0) + 1

    return {
        "total_inspections":   total,
        "pass_count":          pass_count,
        "rework_count":        rework_count,
        "fail_count":          fail_count,
        "avg_quality_score":   avg_score,
        "total_defects":       total_defs,
        "quality_rate":        round(pass_count   / total * 100 if total else 0, 1),
        "failure_rate":        round(fail_count   / total * 100 if total else 0, 1),
        "rework_rate":         round(rework_count / total * 100 if total else 0, 1),
        "avg_defects_per_inspection": round(total_defs / total if total else 0, 2),
        "status_distribution":   status_dist,
        "severity_distribution": severity_dist,
        "defect_distribution":   defect_dist,
        "quality_trend":         quality_trend,
        "defect_trend":          [{"date": k, "total_defects": v} for k, v in sorted(daily_defects.items())],
        "daily_volume":          [{"date": k, "count": v}         for k, v in sorted(daily_vol.items())],
    }


def db_status(db_path: Path) -> bool:
    try:
        conn = _connect(db_path)
        conn.execute("SELECT 1 FROM inspections LIMIT 1")
        conn.close()
        return True
    except Exception:
        return False


def _parse_date(ts: str):
    from datetime import datetime
    for fmt in ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S"]:
        try:
            return str(datetime.strptime(ts.strip(), fmt).date())
        except ValueError:
            continue
    return None
