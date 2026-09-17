from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import numpy as np
import cv2
from backend.database import get_db
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/inspections", tags=["inspections"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = ROOT_DIR / "output" / "camera_capture"

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png"}
MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


def row_to_dict(row):
    return dict(row)


@router.get("")
def list_inspections(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(""),
    severity: str = Query(""),
    search: str = Query(""),
    user=Depends(get_current_user)
):
    conn = get_db()
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

    total = conn.execute(
        f"SELECT COUNT(*) FROM inspections {where}", params
    ).fetchone()[0]

    offset = (page - 1) * limit
    rows = conn.execute(
        f"""SELECT id, inspection_id, timestamp, scratches, dents, rust, other,
               total_defects, status, inspector, quality_score, severity, remarks
            FROM inspections {where}
            ORDER BY id DESC LIMIT ? OFFSET ?""",
        params + [limit, offset]
    ).fetchall()
    conn.close()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, -(-total // limit)),
        "items": [row_to_dict(r) for r in rows]
    }


@router.post("/upload")
async def upload_inspection(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{file.content_type}'. Use JPG or PNG."
        )

    contents = await file.read()

    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="File too large. Maximum size is 20 MB.")

    # Decode image to numpy array
    arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=422, detail="Could not decode image. Ensure it is a valid JPG or PNG.")

    # Run the centralized validation gate before accepting a result.
    try:
        from backend.services.material_validation_service import validate_and_run_inference
        result = validate_and_run_inference(frame, material="steel")
        if not result.get("inspection_valid", False):
            return result
        from backend.services.inference_service import save_inspection_record
        saved = save_inspection_record(result, inspector="Upload", material="steel")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    return saved


@router.get("/{inspection_id}")
def get_inspection(inspection_id: str, user=Depends(get_current_user)):
    conn = get_db()
    row = conn.execute(
        """SELECT id, inspection_id, timestamp, image_path, scratches, dents, rust, other,
                  total_defects, status, inspector, quality_score, severity, remarks
           FROM inspections WHERE inspection_id = ?""",
        (inspection_id,)
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Inspection not found")

    data = row_to_dict(row)
    # Expose image URL instead of raw path
    img_file = IMAGE_DIR / f"{inspection_id}_{data['status']}.jpg"
    data["image_url"] = f"/api/images/{inspection_id}" if img_file.exists() else None
    return data
