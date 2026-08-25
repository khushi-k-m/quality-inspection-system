from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/images", tags=["images"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = ROOT_DIR / "output" / "camera_capture"


@router.get("/{inspection_id}")
def get_image(inspection_id: str, user=Depends(get_current_user)):
    # Try all possible status suffixes
    for suffix in ["PASS", "FAIL", "REWORK"]:
        path = IMAGE_DIR / f"{inspection_id}_{suffix}.jpg"
        if path.exists():
            return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Image not found")
