from fastapi import APIRouter, Depends
from backend.database import get_db
from backend.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

TIMESTAMP_FORMATS = ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S"]


def parse_date(ts: str):
    if not ts:
        return None
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts.strip(), fmt).date()
        except ValueError:
            continue
    return None


@router.get("/summary")
def get_summary(user=Depends(get_current_user)):
    conn = get_db()
    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status='PASS' THEN 1 ELSE 0 END) as pass_count,
            SUM(CASE WHEN status='REWORK' THEN 1 ELSE 0 END) as rework_count,
            SUM(CASE WHEN status='FAIL' THEN 1 ELSE 0 END) as fail_count,
            AVG(CAST(quality_score AS REAL)) as avg_quality_score,
            SUM(total_defects) as total_defects
        FROM inspections
    """).fetchone()
    conn.close()

    total = row["total"] or 0
    pass_count = row["pass_count"] or 0
    rework_count = row["rework_count"] or 0
    fail_count = row["fail_count"] or 0
    avg_score = round(row["avg_quality_score"] or 0, 1)
    total_defects = row["total_defects"] or 0

    return {
        "total_inspections": total,
        "pass_count": pass_count,
        "rework_count": rework_count,
        "fail_count": fail_count,
        "avg_quality_score": avg_score,
        "total_defects": total_defects,
        "quality_rate": round((pass_count / total * 100) if total > 0 else 0, 1),
        "failure_rate": round((fail_count / total * 100) if total > 0 else 0, 1),
        "rework_rate": round((rework_count / total * 100) if total > 0 else 0, 1),
        "avg_defects_per_inspection": round((total_defects / total) if total > 0 else 0, 2),
    }


@router.get("/status-distribution")
def status_distribution(user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT status, COUNT(*) as count FROM inspections GROUP BY status"
    ).fetchall()
    conn.close()
    return [{"status": r["status"], "count": r["count"]} for r in rows]


@router.get("/severity-distribution")
def severity_distribution(user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT severity, COUNT(*) as count FROM inspections GROUP BY severity"
    ).fetchall()
    conn.close()
    return [{"severity": r["severity"] or "NONE", "count": r["count"]} for r in rows]


@router.get("/defect-distribution")
def defect_distribution(user=Depends(get_current_user)):
    conn = get_db()
    row = conn.execute(
        "SELECT SUM(scratches) as s, SUM(dents) as d, SUM(rust) as r, SUM(other) as o FROM inspections"
    ).fetchone()
    conn.close()
    return [
        {"type": "Scratches", "count": row["s"] or 0},
        {"type": "Dents", "count": row["d"] or 0},
        {"type": "Rust", "count": row["r"] or 0},
        {"type": "Other", "count": row["o"] or 0},
    ]


@router.get("/quality-trend")
def quality_trend(user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT inspection_id, timestamp, quality_score FROM inspections ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return [
        {
            "inspection_id": r["inspection_id"],
            "timestamp": r["timestamp"],
            "quality_score": r["quality_score"] or 100
        }
        for r in rows
    ]


@router.get("/defect-trend")
def defect_trend(user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT timestamp, total_defects FROM inspections ORDER BY id ASC"
    ).fetchall()
    conn.close()

    daily = {}
    for r in rows:
        date = parse_date(r["timestamp"])
        if date:
            key = str(date)
            daily[key] = daily.get(key, 0) + (r["total_defects"] or 0)

    return [{"date": k, "total_defects": v} for k, v in sorted(daily.items())]


@router.get("/daily-volume")
def daily_volume(user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT timestamp FROM inspections ORDER BY id ASC"
    ).fetchall()
    conn.close()

    daily = {}
    for r in rows:
        date = parse_date(r["timestamp"])
        if date:
            key = str(date)
            daily[key] = daily.get(key, 0) + 1

    return [{"date": k, "count": v} for k, v in sorted(daily.items())]
