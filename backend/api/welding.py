"""Welding API — /api/welding/*"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import numpy as np
import cv2

from backend.dependencies import get_current_user
from backend.services.material_registry import get_material_config

ROOT_DIR    = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = ROOT_DIR / "output" / "reports"
MATERIAL    = "welding"

router = APIRouter(prefix="/api/welding", tags=["welding"])

TIMESTAMP_FORMATS = ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S"]

def _parse_date(ts: str):
    if not ts:
        return None
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _cfg():
    return get_material_config(MATERIAL)


@router.get("/inspections")
def list_welding_inspections(
    page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
    status: str = Query(""), severity: str = Query(""), search: str = Query(""),
    user=Depends(get_current_user),
):
    from welding.database import get_inspections
    cfg = _cfg()
    total, rows = get_inspections(limit, (page-1)*limit, status, severity, search)
    for r in rows:
        img = cfg["output_dir"] / f"{r['inspection_id']}_{r['status']}.jpg"
        r["image_url"] = f"/api/images/welding/{r['inspection_id']}" if img.exists() else None
    return {"total": total, "page": page, "limit": limit,
            "pages": max(1, -(-total // limit)), "items": rows}


@router.get("/inspections/{inspection_id}")
def get_welding_inspection(inspection_id: str, user=Depends(get_current_user)):
    from welding.database import get_inspection
    cfg  = _cfg()
    data = get_inspection(inspection_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Welding inspection not found")
    img = cfg["output_dir"] / f"{inspection_id}_{data['status']}.jpg"
    data["image_url"] = f"/api/images/welding/{inspection_id}" if img.exists() else None
    return data


@router.post("/inspect")
async def welding_inspect(file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in {"image/jpeg", "image/jpg", "image/png"}:
        raise HTTPException(status_code=422, detail="Use JPG or PNG.")
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File too large. Max 20 MB.")
    arr   = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=422, detail="Could not decode image.")
    try:
        from backend.services.material_validation_service import validate_and_run_inference
        result = validate_and_run_inference(frame, material=MATERIAL)
        if not result.get("inspection_valid", False):
            return result
        from backend.services.inference_service import save_inspection_record
        persisted = save_inspection_record(result, inspector="Upload", material=MATERIAL)
        return persisted
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inspection failed: {e}")


@router.get("/analytics")
def welding_analytics(user=Depends(get_current_user)):
    from welding.database import _connect

    conn = _connect()

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
        for r in conn.execute(
            "SELECT status, COUNT(*) as count FROM inspections GROUP BY status"
        ).fetchall()
    ]
    severity_dist = [
        {"severity": r["severity"] or "NONE", "count": r["count"]}
        for r in conn.execute(
            "SELECT severity, COUNT(*) as count FROM inspections GROUP BY severity"
        ).fetchall()
    ]
    defect_dist = [
        {"type": r["defect_class"], "count": r["count"]}
        for r in conn.execute(
            "SELECT defect_class, COUNT(*) as count FROM defects GROUP BY defect_class"
        ).fetchall()
    ]

    trend_rows = conn.execute(
        "SELECT inspection_id, timestamp, quality_score FROM inspections ORDER BY id ASC"
    ).fetchall()
    quality_trend = [
        {"inspection_id": r["inspection_id"], "timestamp": r["timestamp"],
         "quality_score": r["quality_score"] or 100}
        for r in trend_rows
    ]

    all_rows = conn.execute(
        "SELECT timestamp, defect_count FROM inspections ORDER BY id ASC"
    ).fetchall()
    daily_defects: dict = {}
    daily_vol:     dict = {}
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


@router.get("/images/{inspection_id}")
def get_welding_image(inspection_id: str, user=Depends(get_current_user)):
    cfg = _cfg()
    for suffix in ["PASS", "FAIL", "REWORK"]:
        path = cfg["output_dir"] / f"{inspection_id}_{suffix}.jpg"
        if path.exists():
            return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Welding inspection image not found")


@router.get("/reports")
def list_welding_reports(user=Depends(get_current_user)):
    from welding.database import get_inspections
    _, rows = get_inspections(limit=1000)
    result = []
    for r in rows:
        pdf = REPORTS_DIR / f"{r['inspection_id']}_inspection_report.pdf"
        result.append({
            "inspection_id": r["inspection_id"], "timestamp": r["timestamp"],
            "status": r["status"], "quality_score": r["quality_score"],
            "material": r["material"], "report_available": pdf.exists(),
        })
    return result


@router.get("/reports/{inspection_id}/download")
def download_welding_report(inspection_id: str, user=Depends(get_current_user)):
    try:
        from reports.enhanced_report import generate_enhanced_report
        pdf_path = generate_enhanced_report(inspection_id, MATERIAL)
        if pdf_path is None:
            raise HTTPException(status_code=404, detail="Report could not be generated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")
    return FileResponse(str(pdf_path), media_type="application/pdf",
                        filename=f"{inspection_id}_inspection_report.pdf")
