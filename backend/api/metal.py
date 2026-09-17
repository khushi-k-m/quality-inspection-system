"""
Metal API
=========
All endpoints under /api/metal/
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
from datetime import datetime
import numpy as np
import cv2

from backend.dependencies import get_current_user

ROOT_DIR    = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = ROOT_DIR / "output" / "reports"
IMAGE_DIR   = ROOT_DIR / "output" / "metal_capture"

TIMESTAMP_FORMATS = ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S"]
ALLOWED_TYPES     = {"image/jpeg", "image/jpg", "image/png"}
MAX_SIZE_BYTES    = 20 * 1024 * 1024

router = APIRouter(prefix="/api/metal", tags=["metal"])


def _parse_date(ts: str):
    if not ts:
        return None
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts.strip(), fmt).date()
        except ValueError:
            continue
    return None


# ──────────────────────────────────────────────────────────────────────
# INSPECTIONS
# ──────────────────────────────────────────────────────────────────────

@router.get("/inspections")
def list_metal_inspections(
    page:     int = Query(1, ge=1),
    limit:    int = Query(20, ge=1, le=100),
    status:   str = Query(""),
    severity: str = Query(""),
    search:   str = Query(""),
    user=Depends(get_current_user),
):
    from metal.database import _connect
    conn = _connect()

    conditions, params = [], []
    if status:
        conditions.append("status = ?"); params.append(status)
    if severity:
        conditions.append("severity = ?"); params.append(severity)
    if search:
        conditions.append("inspection_id LIKE ?"); params.append(f"%{search}%")

    where  = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    total  = conn.execute(f"SELECT COUNT(*) FROM inspections {where}", params).fetchone()[0]
    offset = (page - 1) * limit

    rows = conn.execute(
        f"""SELECT id, inspection_id, timestamp, material, image_path,
                   defect_count, quality_score, severity, status, remarks, inspector
            FROM inspections {where}
            ORDER BY id DESC LIMIT ? OFFSET ?""",
        params + [limit, offset],
    ).fetchall()
    conn.close()

    items = []
    for r in rows:
        d = dict(r)
        img = IMAGE_DIR / f"{d['inspection_id']}_{d['status']}.jpg"
        d["image_url"] = f"/api/images/metal/{d['inspection_id']}" if img.exists() else None
        items.append(d)

    return {
        "total": total, "page": page, "limit": limit,
        "pages": max(1, -(-total // limit)), "items": items,
    }


@router.get("/inspections/{inspection_id}")
def get_metal_inspection(inspection_id: str, user=Depends(get_current_user)):
    from metal.database import _connect, get_defects_for_inspection
    conn = _connect()
    row  = conn.execute(
        """SELECT id, inspection_id, timestamp, material, image_path,
                  defect_count, quality_score, severity, status, remarks, inspector
           FROM inspections WHERE inspection_id = ?""",
        (inspection_id,),
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Metal inspection not found")

    data = dict(row)
    img  = IMAGE_DIR / f"{inspection_id}_{data['status']}.jpg"
    data["image_url"] = f"/api/images/metal/{inspection_id}" if img.exists() else None
    data["defects"]   = get_defects_for_inspection(inspection_id)
    return data


# ──────────────────────────────────────────────────────────────────────
# UPLOAD
# ──────────────────────────────────────────────────────────────────────

@router.post("/inspect")
async def metal_upload_inspect(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=422,
            detail=f"Unsupported file type '{file.content_type}'. Use JPG or PNG.")

    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="File too large. Max 20 MB.")

    arr   = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=422, detail="Could not decode image.")

    try:
        from backend.services.material_validation_service import validate_and_run_inference
        result = validate_and_run_inference(frame, material="metal")
        if not result.get("inspection_valid", False):
            return result
        from backend.services.inference_service import save_inspection_record
        persisted = save_inspection_record(result, inspector="Upload", material="metal")
        return persisted
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inspection failed: {e}")


# ──────────────────────────────────────────────────────────────────────
# ANALYTICS
# ──────────────────────────────────────────────────────────────────────

@router.get("/analytics")
def metal_analytics(user=Depends(get_current_user)):
    from metal.database import _connect

    conn = _connect()

    # KPIs
    kpi = conn.execute("""
        SELECT
            COUNT(*)                                          AS total,
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

    # Distributions
    status_dist = [
        {"status": r["status"], "count": r["count"]}
        for r in conn.execute(
            "SELECT status, COUNT(*) as count FROM inspections GROUP BY status"
        ).fetchall()
    ]
    severity_dist = [
        {"severity": r["severity"] or "LOW", "count": r["count"]}
        for r in conn.execute(
            "SELECT severity, COUNT(*) as count FROM inspections GROUP BY severity"
        ).fetchall()
    ]

    # Defect distribution from defects table
    defect_rows = conn.execute(
        "SELECT defect_class, COUNT(*) as count FROM defects GROUP BY defect_class"
    ).fetchall()
    defect_dist = [{"type": r["defect_class"], "count": r["count"]} for r in defect_rows]

    # Quality trend
    trend_rows = conn.execute(
        "SELECT inspection_id, timestamp, quality_score FROM inspections ORDER BY id ASC"
    ).fetchall()
    quality_trend = [
        {"inspection_id": r["inspection_id"], "timestamp": r["timestamp"],
         "quality_score": r["quality_score"] or 100}
        for r in trend_rows
    ]

    # Defect trend (daily)
    all_rows = conn.execute(
        "SELECT timestamp, defect_count FROM inspections ORDER BY id ASC"
    ).fetchall()
    daily_defects: dict = {}
    for r in all_rows:
        d = _parse_date(r["timestamp"])
        if d:
            k = str(d)
            daily_defects[k] = daily_defects.get(k, 0) + (r["defect_count"] or 0)
    defect_trend = [{"date": k, "total_defects": v} for k, v in sorted(daily_defects.items())]

    # Daily volume
    daily_vol: dict = {}
    for r in all_rows:
        d = _parse_date(r["timestamp"])
        if d:
            k = str(d)
            daily_vol[k] = daily_vol.get(k, 0) + 1
    daily_volume = [{"date": k, "count": v} for k, v in sorted(daily_vol.items())]

    conn.close()

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
        "defect_trend":          defect_trend,
        "daily_volume":          daily_volume,
    }


# ──────────────────────────────────────────────────────────────────────
# IMAGE
# ──────────────────────────────────────────────────────────────────────

@router.get("/images/{inspection_id}")
def get_metal_image(inspection_id: str, user=Depends(get_current_user)):
    for suffix in ["PASS", "FAIL", "REWORK"]:
        path = IMAGE_DIR / f"{inspection_id}_{suffix}.jpg"
        if path.exists():
            return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Metal inspection image not found")


# ──────────────────────────────────────────────────────────────────────
# REPORTS
# ──────────────────────────────────────────────────────────────────────

@router.get("/reports")
def list_metal_reports(user=Depends(get_current_user)):
    from metal.database import get_inspections
    records = get_inspections(limit=1000)
    result  = []
    for r in records:
        pdf = REPORTS_DIR / f"{r['inspection_id']}_inspection_report.pdf"
        result.append({
            "inspection_id":    r["inspection_id"],
            "timestamp":        r["timestamp"],
            "status":           r["status"],
            "quality_score":    r["quality_score"],
            "material":         r["material"],
            "report_available": pdf.exists(),
        })
    return result


@router.get("/reports/{inspection_id}/download")
def download_metal_report(inspection_id: str, user=Depends(get_current_user)):
    try:
        from reports.enhanced_report import generate_enhanced_report
        pdf_path = generate_enhanced_report(inspection_id, "metal")
        if pdf_path is None:
            raise HTTPException(status_code=404, detail="Report could not be generated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{inspection_id}_inspection_report.pdf",
    )
